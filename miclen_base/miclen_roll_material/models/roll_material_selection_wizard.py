# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class RollMaterialSelectionWizard(models.TransientModel):
    _name = 'roll.material.selection.wizard'
    _description = '卷料选料预览向导'

    production_id = fields.Many2one(
        'mrp.production',
        string='制造单',
        ondelete='cascade',
    )
    config_id = fields.Many2one(
        'roll.material.config',
        string='选料配置',
        required=True,
    )
    product_id = fields.Many2one(
        'product.product',
        related='production_id.product_id',
        string='成品',
    )
    product_qty = fields.Float(
        string='生产数量',
        default=1.0,
        digits='Product Unit',
    )
    required_length = fields.Integer(
        related='config_id.required_length',
        string='需求长(mm)',
    )
    required_width = fields.Integer(
        related='config_id.required_width',
        string='需求宽(mm)',
    )
    gap = fields.Integer(
        related='config_id.gap',
        string='切割间距(mm)',
    )
    line_ids = fields.One2many(
        'roll.material.selection.wizard.line',
        'wizard_id',
        string='选料结果',
    )
    has_shortage = fields.Boolean(
        string='存在缺口',
        compute='_compute_has_shortage',
    )

    @api.depends('line_ids.shortage_pieces')
    def _compute_has_shortage(self):
        for rec in self:
            rec.has_shortage = any(l.shortage_pieces > 0 for l in rec.line_ids)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        # 从上下文获取制造单
        production_id = self.env.context.get('default_production_id') or self.env.context.get('active_id')
        if production_id:
            production = self.env['mrp.production'].browse(production_id)
            if production.exists():
                res['production_id'] = production.id
                res['product_qty'] = production.product_qty
                # 查找该成品的选料配置
                config = self.env['roll.material.config'].search([
                    ('product_id', '=', production.product_id.id),
                    ('active', '=', True),
                ], limit=1)
                if config:
                    res['config_id'] = config.id
        return res

    def action_preview(self):
        """执行选料算法并填充结果行"""
        self.ensure_one()
        # 如果有制造单，同步生产数量
        if self.production_id:
            self.product_qty = self.production_id.product_qty
        self._run_selection()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'roll.material.selection.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_preview_test(self):
        """测试模式：以当前数量执行选料"""
        self.ensure_one()
        self._run_selection()

    def _run_selection(self):
        """执行选料算法并填充结果行"""
        self.ensure_one()
        # 清除旧行
        self.line_ids.unlink()
        # 执行选料
        results = self.config_id.action_compute_selection(self.product_qty)
        # 创建结果行
        for r in results:
            self.env['roll.material.selection.wizard.line'].create({
                'wizard_id': self.id,
                'roll_product_id': r.get('roll_product_id') or False,
                'roll_product_name': r.get('roll_product_name', ''),
                'roll_width': r.get('roll_width', 0),
                'pieces_per_row': r.get('pieces_per_row', 0),
                'cut_direction': r.get('cut_direction', 'none'),
                'consume_per_piece_mm': r.get('consume_per_piece_mm', 0),
                'allocate_pieces': r.get('allocate_pieces', 0),
                'consume_qty': r.get('consume_qty', 0),
                'available_qty': r.get('available_qty', 0),
                'shortage_pieces': r.get('shortage_pieces', 0),
                'shortage_qty': r.get('shortage_qty', 0),
                'sequence': r.get('sequence', 999),
            })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'roll.material.selection.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_apply(self):
        """将选料结果应用到制造单的原料行"""
        self.ensure_one()
        production = self.production_id
        if not production:
            return {'type': 'ir.actions.act_window_close'}

        # 删除已有的卷料原料行（来自同一配置的）
        existing_roll_moves = production.move_raw_ids.filtered(
            lambda m: m.product_id.is_roll_material
        )
        existing_roll_moves.unlink()

        # 创建新的原料行
        Move = self.env['stock.move']
        for line in self.line_ids:
            if not line.roll_product_id or line.consume_qty <= 0:
                continue
            uom = self.config_id.uom_id or self.env.ref('uom.product_uom_meter', raise_if_not_found=False)
            move_vals = production._get_move_raw_values(
                line.roll_product_id,
                line.consume_qty,
                uom,
            )
            move_vals.pop('bom_line_id', None)
            Move.create(move_vals)

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'res_id': production.id,
            'view_mode': 'form',
            'target': 'current',
        }


class RollMaterialSelectionWizardLine(models.TransientModel):
    _name = 'roll.material.selection.wizard.line'
    _description = '卷料选料预览行'
    _order = 'sequence, id'

    wizard_id = fields.Many2one(
        'roll.material.selection.wizard',
        required=True,
        ondelete='cascade',
    )
    roll_product_id = fields.Many2one(
        'product.product',
        string='卷料产品',
    )
    roll_product_name = fields.Char(
        string='卷料名称',
    )
    roll_width = fields.Integer(string='卷料宽幅(mm)')
    pieces_per_row = fields.Integer(
        string='每排可切片数',
        help='沿卷料宽幅方向可同时排列的片数',
    )
    cut_direction = fields.Selection(
        [
            ('long_side', '长边横放'),
            ('short_side', '短边横放'),
            ('none', '无法切割'),
        ],
        string='切割方向',
    )
    consume_per_piece_mm = fields.Float(
        string='单片消耗(mm)',
        digits='Product Unit',
    )
    allocate_pieces = fields.Integer(
        string='分配片数',
    )
    consume_qty = fields.Float(
        string='消耗量(m)',
        digits='Product Unit',
    )
    available_qty = fields.Float(
        string='可用库存(m)',
        digits='Product Unit',
    )
    shortage_pieces = fields.Integer(
        string='缺口片数',
        help='该卷料库存不足以满足的片数',
    )
    shortage_qty = fields.Float(
        string='缺口量(m)',
        digits='Product Unit',
    )
    sequence = fields.Integer(default=10)
