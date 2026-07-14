# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class RollMaterialConfig(models.Model):
    _name = 'roll.material.config'
    _description = '卷料选料配置'
    _order = 'sequence, name'

    sequence = fields.Integer(
        string='排序',
        default=10,
    )
    name = fields.Char(
        string='配置名称',
        required=True,
        help='如：金属外壳-选料配置',
    )
    product_id = fields.Many2one(
        'product.product',
        string='关联产品',
        required=True,
        help='触发选料的成品产品（制造单的成品）',
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        related='product_id.product_tmpl_id',
        store=True,
        string='产品模板',
    )
    required_length = fields.Integer(
        string='需求长(mm)',
        required=True,
        help='所需材料片的长度，单位毫米',
    )
    required_width = fields.Integer(
        string='需求宽(mm)',
        required=True,
        help='所需材料片的宽度，单位毫米',
    )
    gap = fields.Integer(
        string='切割间距(mm)',
        default=10,
        required=True,
        help='切割时各方向预留的间距，单位毫米',
    )
    quantity = fields.Float(
        string='单片用量',
        default=1.0,
        digits='Product Unit',
        help='每个成品需要的材料片数量，默认1',
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='消耗单位',
        default=lambda self: self.env.ref('uom.product_uom_meter', raise_if_not_found=False),
        help='卷料消耗量的计量单位，默认为米',
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
    )
    line_ids = fields.One2many(
        'roll.material.config.line',
        'config_id',
        string='卷料优先级',
    )
    line_count = fields.Integer(
        compute='_compute_line_count',
        string='卷料数量',
    )

    _sql_constraints = [
        ('check_required_length', 'CHECK(required_length > 0)',
         '需求长必须大于0。'),
        ('check_required_width', 'CHECK(required_width > 0)',
         '需求宽必须大于0。'),
        ('check_gap', 'CHECK(gap >= 0)',
         '切割间距不能为负数。'),
    ]

    @api.depends('line_ids')
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)

    def action_test_selection(self):
        """测试选料：以数量1执行选料算法并弹出预览向导"""
        self.ensure_one()
        # 创建临时向导（不关联MO）
        wizard = self.env['roll.material.selection.wizard'].create({
            'production_id': False,
            'config_id': self.id,
        })
        wizard.action_preview_test()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'roll.material.selection.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_compute_selection(self, product_qty=1.0):
        """
        核心选料算法：根据需求尺寸和配置计算最优卷料选择

        算法逻辑：
        1. 对每个优先级的卷料，检查卷料宽幅是否满足切割条件
        2. 尝试沿长边方向放置（卷料宽幅 >= max(L,W) + gap）
           → 每排可切 floor((W_roll + gap) / (min(L,W) + gap)) 片
           → 每片消耗 (min(L,W) + gap) mm 卷料长度
        3. 若不行，尝试沿短边方向放置（卷料宽幅 >= min(L,W) + gap）
           → 每排可切 floor((W_roll + gap) / (max(L,W) + gap)) 片
           → 每片消耗 (max(L,W) + gap) mm 卷料长度
        4. 都不满足则跳过此卷料
        5. 按优先级分配库存，不足时继续下一个卷料

        :param product_qty: 成品生产数量
        :return: list of dict, 每项包含卷料产品、消耗量、可用库存等
        """
        self.ensure_one()
        results = []
        gap = self.gap
        req_l = self.required_length
        req_w = self.required_width
        max_dim = max(req_l, req_w)
        min_dim = min(req_l, req_w)

        total_pieces = product_qty * self.quantity
        remaining_pieces = total_pieces

        for line in self.line_ids:
            if remaining_pieces <= 0:
                break

            roll_width = line.roll_width
            if not roll_width or roll_width <= 0:
                continue

            # 尝试沿长边方向放置（长边横跨卷料宽幅）
            pieces_per_row = int((roll_width + gap) / (max_dim + gap))
            if pieces_per_row >= 1:
                consume_per_piece_mm = min_dim + gap
                cut_direction = 'long_side'
            else:
                # 尝试沿短边方向放置（短边横跨卷料宽幅）
                pieces_per_row = int((roll_width + gap) / (min_dim + gap))
                if pieces_per_row >= 1:
                    consume_per_piece_mm = max_dim + gap
                    cut_direction = 'short_side'
                else:
                    continue  # 此卷料宽幅不足，跳过

            # 每片实际消耗的卷料长度（考虑每排可切多片）
            consume_per_piece_mm_actual = consume_per_piece_mm / pieces_per_row

            # 转换为配置的消耗单位（mm → m）
            consume_per_piece_m = consume_per_piece_mm_actual / 1000.0

            # 该卷料可用库存（转为米）
            available_qty_m = line.available_qty

            # 该卷料能满足的片数
            if available_qty_m > 0:
                max_pieces_from_roll = int(available_qty_m / consume_per_piece_m) if consume_per_piece_m > 0 else 0
            else:
                max_pieces_from_roll = 0

            # 分配片数
            allocate_pieces = min(remaining_pieces, max_pieces_from_roll) if max_pieces_from_roll > 0 else 0

            # 即使库存不足也记录（用于提示采购）
            if allocate_pieces == 0 and remaining_pieces > 0:
                # 库存不足，记录需求但消耗量为0
                results.append({
                    'roll_product_id': line.roll_product_id.id,
                    'roll_product_name': line.roll_product_id.display_name,
                    'roll_width': roll_width,
                    'pieces_per_row': pieces_per_row,
                    'cut_direction': cut_direction,
                    'consume_per_piece_mm': consume_per_piece_mm_actual,
                    'allocate_pieces': 0,
                    'consume_qty': 0.0,
                    'available_qty': available_qty_m,
                    'shortage_pieces': remaining_pieces,
                    'shortage_qty': remaining_pieces * consume_per_piece_m,
                    'sequence': line.sequence,
                })
                continue

            consume_qty = allocate_pieces * consume_per_piece_m
            remaining_pieces -= allocate_pieces

            results.append({
                'roll_product_id': line.roll_product_id.id,
                'roll_product_name': line.roll_product_id.display_name,
                'roll_width': roll_width,
                'pieces_per_row': pieces_per_row,
                'cut_direction': cut_direction,
                'consume_per_piece_mm': consume_per_piece_mm_actual,
                'allocate_pieces': allocate_pieces,
                'consume_qty': consume_qty,
                'available_qty': available_qty_m,
                'shortage_pieces': 0,
                'shortage_qty': 0.0,
                'sequence': line.sequence,
            })

        # 如果所有卷料都无法满足，记录未满足的数量
        if remaining_pieces > 0:
            results.append({
                'roll_product_id': False,
                'roll_product_name': _('（无法匹配卷料）'),
                'roll_width': 0,
                'pieces_per_row': 0,
                'cut_direction': 'none',
                'consume_per_piece_mm': 0,
                'allocate_pieces': 0,
                'consume_qty': 0.0,
                'available_qty': 0.0,
                'shortage_pieces': remaining_pieces,
                'shortage_qty': 0.0,
                'sequence': 999,
            })

        return results


class RollMaterialConfigLine(models.Model):
    _name = 'roll.material.config.line'
    _description = '卷料选料配置行'
    _order = 'sequence, id'

    config_id = fields.Many2one(
        'roll.material.config',
        required=True,
        ondelete='cascade',
    )
    sequence = fields.Integer(
        string='优先级',
        default=10,
        help='数字越小优先级越高',
    )
    roll_product_id = fields.Many2one(
        'product.product',
        string='卷料产品',
        required=True,
        domain="[('is_roll_material', '=', True)]",
    )
    roll_width = fields.Integer(
        related='roll_product_id.spec_width',
        string='卷料宽幅(mm)',
    )
    roll_length = fields.Integer(
        related='roll_product_id.spec_length',
        string='卷料长度(mm)',
    )
    available_qty = fields.Float(
        string='可用库存(m)',
        compute='_compute_available_qty',
        digits='Product Unit',
        help='该卷料在源库位的可用库存（转换为米）',
    )
    min_stock = fields.Float(
        string='最低安全库存(m)',
        default=0.0,
        digits='Product Unit',
        help='低于此值时触发采购补货提示',
    )
    company_id = fields.Many2one(
        'res.company',
        related='config_id.company_id',
        store=True,
    )

    @api.depends('roll_product_id', 'config_id.company_id')
    def _compute_available_qty(self):
        """计算卷料产品在所有源库位的可用库存"""
        for line in self:
            if not line.roll_product_id:
                line.available_qty = 0.0
                continue
            # 获取产品的可用库存（free quantity）
            quants = self.env['stock.quant'].search([
                ('product_id', '=', line.roll_product_id.id),
                ('quantity', '>', 0),
                ('location_id.usage', '=', 'internal'),
            ])
            total_qty = sum(quants.mapped('available_quantity'))
            # 转换为米（假设卷料的基本单位是米或千克，这里用产品UoM转配置UoM）
            product_uom = line.roll_product_id.uom_id
            target_uom = line.config_id.uom_id or self.env.ref('uom.product_uom_meter', raise_if_not_found=False)
            if product_uom and target_uom and product_uom != target_uom:
                total_qty = product_uom._compute_quantity(total_qty, target_uom)
            line.available_qty = total_qty
