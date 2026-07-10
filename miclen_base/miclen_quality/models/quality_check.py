# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class QualityCheck(models.Model):
    _inherit = "quality.check"

    demand_qty = fields.Float(
        string='Demand Quantity',
        digits='Product Unit',
        compute='_compute_demand_qty',
        store=True,
        readonly=False,
        tracking=True,
        help='调拨单的需求数量，质检时自动从调拨单获取，可手动修改',
    )
    passed_qty = fields.Float(
        string='Passed Quantity',
        digits='Product Unit',
        tracking=True,
        help='质检通过的数量',
    )
    failed_qty = fields.Float(
        string='Failed Quantity',
        digits='Product Unit',
        tracking=True,
        help='质检失败的数量',
    )

    @api.depends('picking_id', 'move_line_id', 'product_id', 'measure_on')
    def _compute_demand_qty(self):
        """从调拨单的库存移动中自动计算需求数量"""
        for check in self:
            qty = 0.0
            if check.picking_id:
                if check.measure_on == 'move_line' and check.move_line_id:
                    # 按数量控制：取移动行的实际数量
                    qty = check.move_line_id.quantity
                elif check.product_id:
                    # 按产品控制：取该产品在调拨单中的需求数量
                    moves = check.picking_id.move_ids.filtered(
                        lambda m: m.product_id == check.product_id
                    )
                    qty = sum(moves.mapped('product_uom_qty'))
                else:
                    # 按操作控制：取调拨单所有移动的需求数量
                    qty = sum(check.picking_id.move_ids.mapped('product_uom_qty'))
            check.demand_qty = qty

    @api.constrains('demand_qty', 'passed_qty', 'failed_qty')
    def _check_qty_consistency(self):
        """校验数量一致性"""
        for check in self:
            if check.passed_qty < 0 or check.failed_qty < 0:
                raise ValidationError(_('通过数量和失败数量不能为负数。'))
            if check.demand_qty > 0 and \
                    (check.passed_qty + check.failed_qty) > check.demand_qty:
                raise ValidationError(_(
                    '通过数量(%(passed)s)加失败数量(%(failed)s)不能超过需求数量(%(demand)s)。',
                    passed=check.passed_qty,
                    failed=check.failed_qty,
                    demand=check.demand_qty,
                ))

    def do_pass(self):
        """通过质检时，若通过数量未填写则自动填充"""
        for check in self:
            if check.demand_qty > 0 and not check.passed_qty:
                check.passed_qty = check.demand_qty - check.failed_qty
        return super().do_pass()

    def do_fail(self):
        """失败质检时，若失败数量未填写则自动填充"""
        for check in self:
            if check.demand_qty > 0 and not check.failed_qty:
                check.failed_qty = check.demand_qty - check.passed_qty
        return super().do_fail()
