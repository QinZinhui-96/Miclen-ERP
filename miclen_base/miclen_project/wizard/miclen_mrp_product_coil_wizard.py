# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MiclenMrpProductCoilWizard(models.TransientModel):
    _name = 'miclen.mrp.product.coil.wizard'
    _description = '卷料选料预览向导'

    move_id = fields.Many2one('stock.move', string="组件")
    product_id = fields.Many2one('product.product', string='产品')
    coil_id = fields.Many2one('miclen.product.coil', string='卷料选料')
    coil_x = fields.Integer(string='规格x(mm)')
    coil_y = fields.Integer(string='规格y(mm)')
    gap = fields.Integer(string='切割间距(mm)')
    product_uom_qty = fields.Float('需求(件)', digits='Product Unit')
    consume_way = fields.Selection([
        ('coil_x', 'x'),
        ('coil_y', 'y')],
        string='按（x,y）消耗', default='coil_x')
    product_uom = fields.Many2one('uom.uom', "单位")
    line_ids = fields.One2many(
        'miclen.mrp.product.coil.wizard.line',
        'wizard_id',
        string='卷料消耗明细')

    # 汇总字段
    total_consume_qty = fields.Float(
        '总消耗量(米)', digits='Product Unit', compute='_compute_total')
    total_consume_units = fields.Integer(
        '总出件数', compute='_compute_total')
    total_shortage_units = fields.Integer(
        '缺口件数', compute='_compute_total')
    total_shortage_qty = fields.Float(
        '总缺口量(米)', digits='Product Unit', compute='_compute_total')

    @api.depends('line_ids.consume_qty', 'line_ids.shortage_qty',
                 'line_ids.number_units', 'line_ids.shortage_units')
    def _compute_total(self):
        for wiz in self:
            wiz.total_consume_qty = sum(wiz.line_ids.mapped('consume_qty'))
            wiz.total_consume_units = sum(wiz.line_ids.mapped('number_units'))
            wiz.total_shortage_units = sum(wiz.line_ids.mapped('shortage_units'))
            wiz.total_shortage_qty = sum(wiz.line_ids.mapped('shortage_qty'))

    # ------------------------------------------------------------------
    # onchange
    # ------------------------------------------------------------------

    @api.onchange('coil_id')
    def _onchange_coil_id(self):
        """coil_id 变化 → 同步规格参数，并触发重新计算"""
        if self.coil_id:
            self.coil_x = self.coil_id.coil_x
            self.coil_y = self.coil_id.coil_y
            self.gap = self.coil_id.gap
            self.consume_way = self.coil_id.consume_way
        self._recalc_lines()

    @api.onchange('consume_way', 'product_uom_qty', 'coil_x', 'coil_y', 'gap')
    def _onchange_recalc_lines(self):
        """消耗方向 / 需求量 / 规格 变化 → 重新计算子表"""
        self._recalc_lines()

    # ------------------------------------------------------------------
    # 核心算法
    # ------------------------------------------------------------------

    def _recalc_lines(self):
        """根据当前规格和需求量，搜索卷材产品并按优先级分配消耗"""
        self.ensure_one()
        # 先清空子表（onchange 中不能用 unlink，用 (5,0,0) 命令）
        self.line_ids = [(5, 0, 0)]

        if not self.coil_x or not self.coil_y or not self.product_uom_qty:
            return

        # 计算所需宽幅和单片用料
        coil_len = (self.gap or 0)   # 所需宽幅(mm)
        coil_num = 0                 # 单片用料长度(mm)
        if self.consume_way == 'coil_x':
            coil_len += self.coil_x
            coil_num = self.coil_y
        else:
            coil_len += self.coil_y
            coil_num = self.coil_x

        if coil_num <= 0 or coil_len <= 0:
            return

        # 搜索卷材产品（与 action_consume_way 保持一致）
        templates = self.env['product.template'].sudo().search(
            [('categ_id.name', '=', '卷材')],
            order='miclen_width'
        )

        remaining_demand = int(self.product_uom_qty)  # 剩余需求(件)
        line_data_list = []
        seq = 10

        for tem in templates:
            if remaining_demand <= 0:
                break

            if not tem.miclen_width or not tem.miclen_width.isdigit():
                continue

            width_int = int(tem.miclen_width)
            if width_int < coil_len:
                continue

            if tem.qty_available <= 0:
                continue

            # 该卷材可出件数：库存(米) × 1000 ÷ 单片用料(mm)，取整
            # 例：15米 × 1000 = 15000mm ÷ 400mm = 37.5 → 37件
            max_units = int(tem.qty_available * 1000 / coil_num)

            if max_units < 1:
                continue

            # 实际取件数 = min(该卷材可出件数, 剩余需求)
            units_from_this = min(max_units, remaining_demand)

            # 消耗量(米) = 取件数 × 单片用料(mm) ÷ 1000
            consume_qty = units_from_this * coil_num / 1000.0

            remaining_demand -= units_from_this

            product = self.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', tem.id)],
                limit=1
            )

            line_data_list.append({
                'sequence': seq,
                'product_id': product.id if product else False,
                'uom_id': tem.uom_id.id if tem.uom_id else False,
                'miclen_width_len': width_int,
                'available_qty': tem.qty_available,
                'max_units': max_units,
                'number_units': units_from_this,
                'consume_qty': consume_qty,
                'shortage_units': 0,
                'shortage_qty': 0.0,
            })
            seq += 10

        # 所有卷材用完仍不满足需求 → 最后一行记录缺口
        if remaining_demand > 0 and line_data_list:
            shortage_meters = remaining_demand * coil_num / 1000.0
            line_data_list[-1]['shortage_units'] = remaining_demand
            line_data_list[-1]['shortage_qty'] = shortage_meters

        # 写入子表
        new_lines = [(0, 0, data) for data in line_data_list]
        self.line_ids = new_lines

    # ------------------------------------------------------------------
    # 按钮动作
    # ------------------------------------------------------------------

    def action_confirm_consume(self):
        """确认消耗按钮 — 直接执行写入制造单组件"""
        self.ensure_one()

        if not self.line_ids:
            raise UserError(_("没有可确认的卷料消耗明细！"))

        if not self.move_id:
            raise UserError(_("无法关联到制造单组件！"))

        origin_move = self.move_id
        production = origin_move.raw_material_production_id
        if not production:
            raise UserError(_("无法关联到制造单！请确保该组件行属于某个制造单。"))

        # 校验原始组件行状态（必须在草稿状态才能替换）
        if origin_move.state not in ('draft', 'cancel'):
            raise UserError(_(
                "原始组件行状态为「%s」，无法替换！\n"
                "请在制造单草稿状态下操作。"
            ) % origin_move.state)

        # 有缺口时阻止
        if self.total_shortage_units > 0:
            raise UserError(_(
                "存在缺口（%s 件），无法确认消耗！\n"
                "请先补充卷材库存后重试。"
            ) % self.total_shortage_units)

        # ---- 为每条卷材行创建 stock.move ----
        Move = self.env['stock.move']
        new_moves = []
        for line in self.line_ids:
            if line.consume_qty <= 0 or not line.product_id:
                continue
            new_move = Move.create({
                'name': origin_move.name or production.name,
                'product_id': line.product_id.id,
                'product_uom_qty': line.consume_qty,
                'product_uom': line.uom_id.id or origin_move.product_uom.id,
                'location_id': origin_move.location_id.id,
                'location_dest_id': origin_move.location_dest_id.id,
                'raw_material_production_id': production.id,
                'picking_type_id': origin_move.picking_type_id.id if origin_move.picking_type_id else False,
                'group_id': origin_move.group_id.id if origin_move.group_id else False,
                'origin': production.name,
                'company_id': origin_move.company_id.id,
                'coil_id': self.coil_id.id if self.coil_id else False,
                'is_coil_expanded': True,
                'procure_method': 'make_to_stock',
            })
            new_moves.append(new_move)
            _logger.info(
                "卷材展开: MO=%s 创建 move product=%s qty=%s 米",
                production.name, line.product_id.display_name, line.consume_qty
            )

        # ---- 删除原始 BOM 组件行 ----
        if new_moves:
            origin_move.sudo().unlink()
            _logger.info(
                "卷材展开: MO=%s 已删除原始组件行(id=%s, product=%s)，"
                "替换为 %d 条卷材 move",
                production.name, origin_move.id,
                origin_move.product_id.display_name, len(new_moves)
            )

        return {'type': 'ir.actions.act_window_close'}


class MiclenMrpProductCoilWizardLine(models.TransientModel):
    _name = 'miclen.mrp.product.coil.wizard.line'
    _description = '卷料选料预览向导行'
    _order = 'sequence'

    wizard_id = fields.Many2one(
        'miclen.mrp.product.coil.wizard',
        required=True, ondelete='cascade')
    sequence = fields.Integer(string='优先级', default=10)
    product_id = fields.Many2one('product.product', string='卷料产品')
    uom_id = fields.Many2one(related='product_id.uom_id', string='单位')
    miclen_width_len = fields.Integer(string='卷料宽幅(mm)')
    available_qty = fields.Float(string='可用库存(米)', digits='Product Unit')
    max_units = fields.Integer(string='可出件数')
    number_units = fields.Integer(string='实际取件')
    consume_qty = fields.Float(string='消耗量(米)', digits='Product Unit')
    shortage_units = fields.Integer(string='缺口件数')
    shortage_qty = fields.Float(string='缺口量(米)', digits='Product Unit')
