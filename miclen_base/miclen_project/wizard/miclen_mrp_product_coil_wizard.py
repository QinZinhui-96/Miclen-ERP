# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class MiclenMrpProductCoilWizard(models.TransientModel):
    _name = 'miclen.mrp.product.coil.wizard'
    _description = '卷料选料预览向导'

    move_id = fields.Many2one('stock.move', string="组件")
    product_id = fields.Many2one('product.product', string='产品')
    miclen_coil_w = fields.Integer(string='规格W(mm)', related='move_id.miclen_coil_w')
    miclen_coil_l = fields.Integer(string='规格L(mm)', related='move_id.miclen_coil_l')
    miclen_gap = fields.Integer(string='切割间距(mm)', related='move_id.miclen_gap')
    miclen_condition = fields.Char(string='筛选条件', related='move_id.miclen_condition')
    product_uom_qty = fields.Float('需求(件)', digits='Product Unit')
    product_uom = fields.Many2one('uom.uom', "单位")
    line_ids = fields.One2many(
        'miclen.mrp.product.coil.wizard.line',
        'wizard_id',
        string='卷料消耗明细')

    # 汇总字段（只统计选中行）
    total_consume_qty = fields.Float(
        '总消耗量(米)', digits='Product Unit', compute='_compute_total')
    total_consume_units = fields.Integer(
        '总出件数', compute='_compute_total')
    total_shortage_units = fields.Integer(
        '缺口件数', compute='_compute_total')
    total_shortage_qty = fields.Float(
        '总缺口量(米)', digits='Product Unit', compute='_compute_total')
    # products_domain = fields.Char(string='可选产品', compute='_compute_products_domain', store=True)
    products_domain = fields.Char(string='可选产品')

    # @api.depends('miclen_condition')
    # def _compute_products_domain(self):
    #     template_object = self.env['product.template'].sudo()
    #     product_object = self.env['product.product'].sudo()
    #     for rec in self:
    #         rec.products_domain = "[('id', '=', -1)]"
    #         if rec.miclen_condition:
    #             templates = template_object.search([
    #                 ('default_code', 'ilike', rec.miclen_condition)], order='miclen_width_int')
    #             tem_date = []
    #             for tem in templates:
    #                 if tem.miclen_width_len:
    #                     pass
    #             if templates:
    #
    #
    #                 product_ids = product_object.search([
    #                     ('product_tmpl_id', 'in', templates)
    #                 ]).ids
    #                 rec.products_domain = "[('id', 'in', %s)]" % product_ids



    @api.depends('line_ids.consume_qty', 'line_ids.shortage_qty',
                 'line_ids.number_units', 'line_ids.shortage_units',
                 'line_ids.selected')
    def _compute_total(self):
        for wiz in self:
            selected = wiz.line_ids.filtered('selected')
            wiz.total_consume_qty = sum(selected.mapped('consume_qty'))
            wiz.total_consume_units = sum(selected.mapped('number_units'))
            wiz.total_shortage_units = sum(selected.mapped('shortage_units'))
            wiz.total_shortage_qty = sum(selected.mapped('shortage_qty'))

    # ------------------------------------------------------------------
    # onchange
    # ------------------------------------------------------------------

    @api.onchange('move_id')
    def _onchange_move_id(self):
        """向导打开时自动加载匹配的卷材产品"""
        if self.move_id:
            self.product_uom_qty = self.move_id.product_uom_qty
            self.product_uom = self.move_id.product_uom
            self.product_id = self.move_id.product_id
        self._load_matching_materials()

    @api.onchange('line_ids')
    def _onchange_line_selected(self):
        """用户勾选/取消勾选行、或切换消耗方向时，重新计算选中行的消耗量"""
        self._recalc_selected_lines()

    # ------------------------------------------------------------------
    # 核心方法
    # ------------------------------------------------------------------

    def _load_matching_materials(self):
        """搜索所有满足宽幅要求的卷材产品，加入子表。

        对每个卷材计算 W 方向和 L 方向两个消耗方式：
        - W方向: 单片用料 = coil_w + gap, 所需宽幅 = gap + coil_l
        - L方向: 单片用料 = coil_l + gap, 所需宽幅 = gap + coil_w

        默认选 max_units 更大的方向（消耗库存最少的方式）。
        用户可在子表中手动切换方向。
        """
        self.ensure_one()
        self.line_ids = [(5, 0, 0)]

        move = self.move_id
        if not move:
            return

        coil_w = move.miclen_coil_w
        coil_l = move.miclen_coil_l
        gap = move.miclen_gap or 10
        product_uom_qty = move.product_uom_qty

        if not coil_w or not coil_l or not product_uom_qty:
            return

        # 两个方向的需求
        # W方向: 单片用料(mm) = coil_w + gap, 所需宽幅 = gap + coil_l
        req_w = gap + coil_l
        unit_w = coil_w + gap
        # L方向: 单片用料(mm) = coil_l + gap, 所需宽幅 = gap + coil_w
        req_l = gap + coil_w
        unit_l = coil_l + gap

        if req_w <= 0 or unit_w <= 0:
            return

        # 搜索卷材产品（按宽幅升序，窄的优先用）
        templates = self.env['product.template'].sudo().search(
            [('default_code', 'ilike', move.miclen_condition)],
            order='miclen_width_int'
        )

        line_data_list = []
        seq = 10
        product_ids = []
        for tem in templates:
            if tem.miclen_width_int <= 0:
                continue

            width_int = tem.miclen_width_int
            stock_mm = tem.qty_available * 1000  # 库存转毫米

            # 计算 W 方向
            w_ok = width_int >= req_w
            w_max = int(stock_mm / unit_w) if w_ok and stock_mm > 0 else 0

            # 计算 L 方向
            l_ok = width_int >= req_l
            l_max = int(stock_mm / unit_l) if l_ok and stock_mm > 0 else 0

            # 两个方向都不满足则跳过
            if w_max < 1 and l_max < 1:
                continue

            # 默认选 max_units 更大的方向（消耗库存最少）
            if w_max >= l_max and w_max >= 1:
                best_way = 'w'
                best_max = w_max
                best_unit = unit_w
            else:
                best_way = 'l'
                best_max = l_max
                best_unit = unit_l

            product = self.env['product.product'].sudo().search(
                [('product_tmpl_id', '=', tem.id)], limit=1
            )
            product_ids.append(product.id)
            line_data_list.append({
                'sequence': seq,
                'product_id': product.id if product else False,
                'uom_id': tem.uom_id.id if tem.uom_id else False,
                'miclen_width_len': width_int,
                'available_qty': tem.qty_available,
                'max_units': best_max,
                'selected': False,
                'consume_way': best_way,
                'unit_mm': best_unit,
                'number_units': 0,
                'consume_qty': 0.0,
                'shortage_units': 0,
                'shortage_qty': 0.0,
            })
            seq += 10

        new_lines = [(0, 0, data) for data in line_data_list]
        self.line_ids = new_lines
        if product_ids:
            self.products_domain = "[('id', 'in', %s)]" % product_ids
        else:
            self.products_domain = "[('id', '=', -1)]"
        _logger.info(
            "卷料选料: 加载了 %d 条匹配卷材 (coil_w=%s, coil_l=%s, gap=%s, "
            "W方向: req=%s unit=%s, L方向: req=%s unit=%s)",
            len(line_data_list), coil_w, coil_l, gap,
            req_w, unit_w, req_l, unit_l
        )

    def _recalc_selected_lines(self):
        """对选中的行按优先级逐卷分配消耗量。

        每行的 consume_way 决定单片用料：
        - 'w': coil_num = coil_w + gap
        - 'l': coil_num = coil_l + gap

        算法：
        1. 按优先级（sequence 升序）遍历选中行
        2. 每行：max_units 已在加载时算好，但如果用户切换了方向需要重算
        3. 实际取件 = min(max_units, 剩余需求)
        4. 消耗量(米) = 取件数 × unit_mm ÷ 1000
        5. 剩余需求 -= 取件数，继续下一行
        6. 全部选完仍不满足 → 最后一行记录缺口
        """
        self.ensure_one()

        move = self.move_id
        if not move:
            return

        coil_w = move.miclen_coil_w
        coil_l = move.miclen_coil_l
        gap = move.miclen_gap or 10

        # 两个方向的单片用量
        unit_w = coil_w + gap  # W方向
        unit_l = coil_l + gap  # L方向

        remaining_demand = int(move.product_uom_qty)

        selected_lines = self.line_ids.filtered('selected').sorted('sequence')

        # 先清空所有行的计算值
        for line in self.line_ids:
            line.number_units = 0
            line.consume_qty = 0.0
            line.shortage_units = 0
            line.shortage_qty = 0.0

        # 如果用户切换了消耗方向，需要重算该行的 unit_mm 和 max_units
        for line in self.line_ids:
            if line.consume_way == 'w':
                line.unit_mm = unit_w
            else:
                line.unit_mm = unit_l
            # 重算 max_units = int(库存(米) × 1000 ÷ unit_mm)
            if line.unit_mm and line.unit_mm > 0:
                line.max_units = int(line.available_qty * 1000 / line.unit_mm)
            else:
                line.max_units = 0

        last_selected = None
        for line in selected_lines:
            if remaining_demand <= 0:
                break

            max_units = line.max_units
            if max_units < 1:
                continue

            # 实际取件数 = min(该卷材可出件数, 剩余需求)
            units_from_this = min(max_units, remaining_demand)

            # 消耗量(米) = 取件数 × 单片用量(mm) ÷ 1000
            coil_num = line.unit_mm or (unit_w if line.consume_way == 'w' else unit_l)
            consume_qty = units_from_this * coil_num / 1000.0

            remaining_demand -= units_from_this

            line.number_units = units_from_this
            line.consume_qty = consume_qty
            last_selected = line

        # 所有选中卷材用完仍不满足需求 → 最后一个选中行记录缺口
        if remaining_demand > 0 and last_selected:
            coil_num = last_selected.unit_mm or (unit_w if last_selected.consume_way == 'w' else unit_l)
            shortage_meters = remaining_demand * coil_num / 1000.0
            last_selected.shortage_units = remaining_demand
            last_selected.shortage_qty = shortage_meters

    # ------------------------------------------------------------------
    # 确认按钮
    # ------------------------------------------------------------------

    def action_confirm_consume(self):
        """确认消耗按钮 — 将选中行的数据写入制造单组件

        支持草稿、已确认、已分配状态的制造单。
        对于已确认/已分配的 move，先取消（自动解预留），再删除，然后创建新 move
        并根据制造单状态自动确认和分配库存。
        """
        self.ensure_one()

        selected_lines = self.line_ids.filtered('selected')
        if not selected_lines:
            raise UserError(_("请先勾选要消耗的卷材行！"))

        if not self.move_id:
            raise UserError(_("无法关联到制造单组件！"))

        origin_move = self.move_id
        production = origin_move.raw_material_production_id
        if not production:
            raise UserError(_("无法关联到制造单！请确保该组件行属于某个制造单。"))

        # 已完成的 move 不允许替换
        if origin_move.state == 'done':
            raise UserError(_(
                "原始组件行已完成（Done），无法替换！"
            ))

        # 如果已有消耗数量，先清零已消耗数量（删除明细行）再替换，
        # 避免因已消耗数量导致无法替换（原始 move 随后会被删除）
        if origin_move.quantity and origin_move.quantity > 0:
            _logger.info(
                "卷材展开: MO=%s 原始组件行(id=%s, product=%s)已有消耗数量 %s，先清零再替换",
                production.name, origin_move.id,
                origin_move.product_id.display_name, origin_move.quantity
            )
            if origin_move.move_line_ids:
                origin_move.move_line_ids.sudo().unlink()
            origin_move.quantity = 0

        if self.total_shortage_units > 0:
            raise UserError(_(
                "存在缺口（%s 件），无法确认消耗！\n"
                "请勾选更多卷材行或补充库存后重试。"
            ) % self.total_shortage_units)

        # ---- 仓库与位置：判断是否需要建立 WH/库存 -> 消耗位的 PC 拣货单 ----
        # 卷材在 origin_move.location_id 被消耗（多步制造时为 WH/生产前）。
        # 若该位置不是 WH/库存本身，则需要从 WH/库存 调拨过来，
        # 否则库存会从错误的位置扣减（这正是之前的业务缺陷）。
        wh = production.picking_type_id.warehouse_id
        stock_loc = wh.lot_stock_id if wh else False
        consume_loc = origin_move.location_id  # 卷材消耗位（多步时为 WH/生产前）
        need_pc = bool(stock_loc and stock_loc.id != consume_loc.id)

        # ---- 为每条选中行创建 stock.move ----
        Move = self.env['stock.move']
        new_moves = Move
        pc_moves = Move
        for line in selected_lines:
            if line.consume_qty <= 0 or not line.product_id:
                continue
            way_label = "W" if line.consume_way == 'w' else "L"

            # 卷料 move：从消耗位 -> 生产虚拟位置，作为制造单组件
            coil_move = Move.create({
                'product_id': line.product_id.id,
                'product_uom_qty': line.consume_qty,
                'product_uom': line.uom_id.id or origin_move.product_uom.id,
                'location_id': consume_loc.id,
                'location_dest_id': origin_move.location_dest_id.id,
                'raw_material_production_id': production.id,
                'picking_type_id': origin_move.picking_type_id.id if origin_move.picking_type_id else False,
                'production_group_id': origin_move.production_group_id.id if origin_move.production_group_id else False,
                'origin': production.name,
                'company_id': origin_move.company_id.id,
                'procure_method': 'make_to_stock',
                'state': 'draft',
            })
            new_moves += coil_move

            # PC 拣货单 move：从 WH/库存 -> 消耗位，给卷料 move 供货
            if need_pc:
                pc_move = Move.create({
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.consume_qty,
                    'product_uom': line.uom_id.id or origin_move.product_uom.id,
                    'location_id': stock_loc.id,
                    'location_dest_id': consume_loc.id,
                    'picking_type_id': wh.pbm_type_id.id if (wh and wh.pbm_type_id) else False,
                    'production_group_id': production.production_group_id.id,
                    'origin': production.name,
                    'company_id': origin_move.company_id.id,
                    'warehouse_id': wh.id if wh else False,
                    'procure_method': 'make_to_stock',
                    'state': 'draft',
                    # move_dest_ids 会自动反写 coil_move.move_orig_ids，
                    # 使 coil_move 处于 waiting，避免 _adjust_procure_method 重复拉出第二张 PC 单
                    'move_dest_ids': [(4, coil_move.id)],
                })
                pc_moves += pc_move

            _logger.info(
                "卷材展开: MO=%s 创建 move product=%s qty=%s米 方向=%s 单片=%smm 取件=%s%s",
                production.name, line.product_id.display_name,
                line.consume_qty, way_label, line.unit_mm, line.number_units,
                " (已建PC拣货单)" if need_pc else ""
            )

        if new_moves:
            origin_move_id = origin_move.id
            origin_move_display = origin_move.product_id.display_name

            # 先取消并清理原始组件行的上游拉动 move（原生 PC 单），避免重复占用库存
            for up in origin_move.move_orig_ids.filtered(lambda m: m.state not in ('done', 'cancel')):
                if not (up.move_dest_ids - origin_move):
                    up.sudo()._action_cancel()

            # 成品 move（生产链下游），删除原始组件行前先记录以便重新挂接
            dest_moves = origin_move.move_dest_ids

            # 如果原始 move 已确认/已分配，先取消（_action_cancel 内部会自动解预留）
            if origin_move.state not in ('draft', 'cancel'):
                origin_move._action_cancel()
            origin_move.sudo().unlink()

            # 新卷料 move 重新挂接到成品 move，保持生产链完整
            for mv in new_moves:
                mv.move_dest_ids = [(6, 0, dest_moves.ids)]

            _logger.info(
                "卷材展开: MO=%s 已删除原始组件行(id=%s, product=%s)，"
                "替换为 %d 条卷材 move",
                production.name, origin_move_id,
                origin_move_display, len(new_moves)
            )

            # 创建 PC 拣货单（WH/库存 -> 消耗位），并打上 production_group_id
            # 使其出现在制造单的 action_view_mo_delivery（关联拣货单）按钮中
            pc_picking = False
            if need_pc and pc_moves:
                pc_picking = self.env['stock.picking'].create({
                    'picking_type_id': wh.pbm_type_id.id if (wh and wh.pbm_type_id) else False,
                    'location_id': stock_loc.id,
                    'location_dest_id': consume_loc.id,
                    'origin': production.name,
                    'company_id': production.company_id.id,
                })
                pc_moves.write({'picking_id': pc_picking.id})
                _logger.info(
                    "卷材展开: MO=%s 已创建 PC 拣货单 %s (WH/库存 -> %s)",
                    production.name, pc_picking.name, consume_loc.display_name
                )

            # 已确认/进行中的制造单：立即确认 PC 拣货单与新 move
            # 草稿制造单则留作 draft，待用户确认制造单时由原生 action_confirm
            # 的 self.picking_ids.filtered(...).action_confirm() 自动确认 PC 拣货单
            if production.state in ('confirmed', 'progress'):
                if pc_picking:
                    pc_picking.action_confirm()
                    pc_picking.action_assign()
                    # 当 PC 作业的需求数量(product_uom_qty)与已处理数量(quantity)一致
                    # （即所有作业行均已完全预留 state=='assigned'）时，自动调用
                    # 验证按钮(button_validate)将该 PC 拣货单置为已完成(done)。
                    # 部分可用时不自动验证，避免强行过账产生欠单，留给人工处理。
                    if pc_picking.move_ids and all(
                        m.state == 'assigned' for m in pc_picking.move_ids
                    ):
                        for mv in pc_picking.move_ids:
                            if not mv.product_uom.is_zero(mv.product_uom_qty):
                                mv.quantity = mv.product_uom_qty
                        pc_picking.button_validate()
                        _logger.info(
                            "卷材展开: MO=%s 的 PC 拣货单 %s 已全部预留，已自动验证完成",
                            production.name, pc_picking.name
                        )
                # coil_move 带有 move_orig_ids(PC move)，会被置为 waiting，不重复拉动
                new_moves._action_confirm()
                _logger.info(
                    "卷材展开: MO=%s 已确认 PC 拣货单与 %d 条新 move",
                    production.name, len(new_moves)
                )

        # 原始 stock.move 已被删除，关闭向导后跳转回制造单表单，
        # 否则浏览器会尝试重载已删除的记录导致 "Record does not exist" 报错
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'res_id': production.id,
            'view_mode': 'form',
            'target': 'current',
        }


class MiclenMrpProductCoilWizardLine(models.TransientModel):
    _name = 'miclen.mrp.product.coil.wizard.line'
    _description = '卷料选料预览向导行'
    _order = 'sequence'

    wizard_id = fields.Many2one(
        'miclen.mrp.product.coil.wizard',
        required=True, ondelete='cascade')
    sequence = fields.Integer(string='优先级', default=10)
    product_id = fields.Many2one('product.product', string='卷材产品')
    uom_id = fields.Many2one(related='product_id.uom_id', string='单位')
    miclen_width_len = fields.Integer(string='卷材宽幅(mm)')
    available_qty = fields.Float(string='可用库存(米)', digits='Product Unit')
    max_units = fields.Integer(string='可出件数')
    selected = fields.Boolean(string='选择', default=False)
    consume_way = fields.Selection([
        ('w', 'W方向'),
        ('l', 'L方向'),
    ], string='消耗方向', default='w')
    unit_mm = fields.Integer(string='单片用量(mm)')
    number_units = fields.Integer(string='实际取件')
    consume_qty = fields.Float(string='消耗量(米)', digits='Product Unit')
    shortage_units = fields.Integer(string='缺口件数')
    shortage_qty = fields.Float(string='缺口量(米)', digits='Product Unit')
    # 从主表获取可选产品 domain（related 字段，用于 product_id 的过滤）
    wizard_products_domain = fields.Char(
        related='wizard_id.products_domain', string='产品过滤域')

    @api.constrains('wizard_id', 'product_id')
    def _check_unique_product(self):
        for record in self:
            if not record.wizard_id or not record.product_id:
                continue
            # 检查同一个向导中是否存在相同产品
            duplicate = self.search([
                ('wizard_id', '=', record.wizard_id.id),
                ('product_id', '=', record.product_id.id),
                ('id', '!=', record.id),  # 排除自己
            ], limit=1)
            if duplicate:
                raise ValidationError(_(
                    "产品「%s」已存在于明细行中，不能重复添加！"
                ) % record.product_id.display_name)