# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class QualityCheck(models.Model):
    _inherit = "quality.check"

    demand_qty = fields.Float(
        string='需求数量',
        digits='Product Unit',
        compute='_compute_demand_qty',
        store=True,
        readonly=False,
        tracking=True,
        help='调拨单的需求数量，质检时自动从调拨单获取，可手动修改',
    )
    passed_qty = fields.Float(
        string='合格数量',
        digits='Product Unit',
        tracking=True,
        help='质检通过的数量',
    )
    failed_qty = fields.Float(
        string='不合格数量',
        digits='Product Unit',
        tracking=True,
        help='质检失败的数量',
    )
    remaining_qty = fields.Float(
        string='剩余数量',
        digits='Product Unit',
        compute='_compute_remaining_qty',
        store=True,
        help='剩余待检数量 = 需求数量 - 通过数量 - 失败数量',
    )
    pass_rate = fields.Float(
        string='通过率',
        compute='_compute_pass_rate',
        store=True,
        help='通过率(%) = 通过数量 / 需求数量 * 100',
    )
    failure_reason_id = fields.Many2one(
        'quality.reason',
        string='不合格原因',
        tracking=True,
        help='质检失败的原因分类',
    )
    quality_remark = fields.Text(
        string='质量备注',
        tracking=True,
        help='质检备注 / 观察记录',
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

    @api.depends('demand_qty', 'passed_qty', 'failed_qty')
    def _compute_remaining_qty(self):
        """计算剩余待检数量"""
        for check in self:
            check.remaining_qty = check.demand_qty - check.passed_qty - check.failed_qty

    @api.depends('demand_qty', 'passed_qty', 'failed_qty')
    def _compute_pass_rate(self):
        """计算通过率"""
        for check in self:
            if check.demand_qty > 0:
                check.pass_rate = (check.passed_qty / check.demand_qty) * 100
            else:
                check.pass_rate = 0.0

    @api.onchange('passed_qty')
    def _onchange_passed_qty(self):
        """通过数量变更时自动计算失败数量 = 需求数量 - 通过数量"""
        for check in self:
            if check.demand_qty > 0:
                expected_failed = check.demand_qty - check.passed_qty
                if expected_failed >= 0:
                    check.failed_qty = expected_failed

    @api.onchange('failed_qty')
    def _onchange_failed_qty(self):
        """失败数量变更时自动计算通过数量 = 需求数量 - 失败数量"""
        for check in self:
            if check.demand_qty > 0:
                expected_passed = check.demand_qty - check.failed_qty
                if expected_passed >= 0:
                    check.passed_qty = expected_passed

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
        """通过质检：有失败数量时禁止通过，自动填充通过数量"""
        for check in self:
            if check.demand_qty > 0 and check.failed_qty > 0:
                raise UserError(_(
                    '当前质检有失败数量 %(failed)s，不能通过质检。请点击"失败"按钮完成质检，'
                    '系统将自动创建质量警报。',
                    failed=check.failed_qty,
                ))
            if check.demand_qty > 0 and not check.passed_qty:
                check.passed_qty = check.demand_qty - check.failed_qty
        return super().do_pass()

    def do_fail(self):
        """失败质检时，若失败数量未填写则自动填充，并自动创建质量警报"""
        for check in self:
            if check.demand_qty > 0 and not check.failed_qty:
                check.failed_qty = check.demand_qty - check.passed_qty
        result = super().do_fail()
        for check in self:
            if check.failed_qty > 0 and not check.alert_ids:
                check._create_quality_alert()
        return result

    def do_measure(self):
        """测量质检：有失败数量时直接判定失败，不再判断测量值"""
        for check in self:
            if check.demand_qty > 0 and check.failed_qty > 0:
                return check.do_fail()
        return super().do_measure()

    def _create_quality_alert(self):
        """自动创建质量警报记录，状态设为'新建'"""
        self.ensure_one()
        desc = _(
            '质检失败：需求数量 %(demand)s，通过数量 %(passed)s，失败数量 %(failed)s',
            demand=self.demand_qty,
            passed=self.passed_qty,
            failed=self.failed_qty,
        )
        if self.quality_remark:
            desc = desc + '\n' + self.quality_remark
        # 获取"New"阶段，优先用 ref，找不到则走默认逻辑
        stage = self.env.ref('quality.quality_alert_stage_0', raise_if_not_found=False)
        if not stage:
            stage = self.env['quality.alert.stage'].search(
                [('team_ids', '=', False)], limit=1)
        vals = {
            'check_id': self.id,
            'product_id': self.product_id.id if self.product_id else False,
            'product_tmpl_id': self.product_id.product_tmpl_id.id if self.product_id else False,
            'picking_id': self.picking_id.id if self.picking_id else False,
            'partner_id': self.picking_id.partner_id.id if self.picking_id and self.picking_id.partner_id else False,
            'reason_id': self.failure_reason_id.id if self.failure_reason_id else False,
            'description': desc,
            'team_id': self.team_id.id if self.team_id else False,
            'company_id': self.company_id.id if self.company_id else False,
            'user_id': self.env.user.id,
            'stage_id': stage.id if stage else False,
        }
        return self.env['quality.alert'].create(vals)

    def action_batch_pass(self):
        """批量通过质检：自动填充通过数量并执行通过操作，跳过有失败数量的记录"""
        passed_count = 0
        skipped_count = 0
        for check in self:
            if check.quality_state != 'none':
                continue
            if check.demand_qty > 0 and check.failed_qty > 0:
                skipped_count += 1
                continue
            if check.demand_qty > 0 and not check.passed_qty:
                check.passed_qty = check.demand_qty - check.failed_qty
            check.do_pass()
            passed_count += 1
        msg_parts = [_('已成功通过 %(count)s 条质检记录。', count=passed_count)]
        msg_type = 'success'
        if skipped_count:
            msg_parts.append(_('跳过 %(count)s 条有失败数量的记录（请单独处理）。', count=skipped_count))
            msg_type = 'warning'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('批量通过'),
                'message': ' '.join(msg_parts),
                'type': msg_type,
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
