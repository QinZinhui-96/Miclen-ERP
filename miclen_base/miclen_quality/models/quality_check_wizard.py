# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class QualityCheckWizard(models.TransientModel):
    _inherit = 'quality.check.wizard'

    demand_qty = fields.Float(
        string='需求数量',
        related='current_check_id.demand_qty',
        readonly=True,
    )
    passed_qty = fields.Float(
        string='合格数量',
        related='current_check_id.passed_qty',
        readonly=False,
    )
    failed_qty = fields.Float(
        string='不合格数量',
        related='current_check_id.failed_qty',
        readonly=False,
    )
    remaining_qty = fields.Float(
        string='剩余数量',
        related='current_check_id.remaining_qty',
        readonly=True,
    )
    pass_rate = fields.Float(
        string='通过率',
        compute='_compute_wizard_pass_rate',
        help='通过率(%) = 通过数量 / 需求数量 * 100',
    )

    @api.depends('demand_qty', 'passed_qty', 'failed_qty')
    def _compute_wizard_pass_rate(self):
        """向导中实时计算通过率，不依赖 quality.check 的 store=True 计算字段"""
        for wizard in self:
            if wizard.demand_qty > 0:
                wizard.pass_rate = (wizard.passed_qty / wizard.demand_qty) * 100
            else:
                wizard.pass_rate = 0.0
    failure_reason_id = fields.Many2one(
        'quality.reason',
        string='不通过原因',
        related='current_check_id.failure_reason_id',
        readonly=False,
    )
    quality_remark = fields.Text(
        string='质量备注',
        related='current_check_id.quality_remark',
        readonly=False,
    )

    @api.model
    def default_get(self, fields_list):
        """向导打开时，自动将通过数量设为需求数量（默认全部通过）"""
        res = super().default_get(fields_list)
        check_id = self.env.context.get('default_current_check_id')
        if check_id:
            check = self.env['quality.check'].browse(check_id)
            if check.exists() and check.quality_state == 'none' \
                    and check.demand_qty > 0 \
                    and not check.passed_qty and not check.failed_qty:
                check.passed_qty = check.demand_qty
        return res

    @api.onchange('passed_qty')
    def _onchange_wizard_passed_qty(self):
        """向导中通过数量变更时自动计算失败数量 = 需求数量 - 通过数量"""
        if self.demand_qty > 0:
            expected_failed = self.demand_qty - self.passed_qty
            if expected_failed >= 0:
                self.failed_qty = expected_failed

    @api.onchange('failed_qty')
    def _onchange_wizard_failed_qty(self):
        """向导中失败数量变更时自动计算通过数量 = 需求数量 - 失败数量"""
        if self.demand_qty > 0:
            expected_passed = self.demand_qty - self.failed_qty
            if expected_passed >= 0:
                self.passed_qty = expected_passed

    def _validate_passed_qty(self):
        """校验通过数量：有需求数量时必须大于0"""
        if self.demand_qty > 0 and self.passed_qty <= 0:
            raise UserError(_(
                '请填写通过数量，通过数量必须大于0。当前需求数量为 %(demand)s。',
                demand=self.demand_qty,
            ))
        if self.demand_qty > 0 and \
                (self.passed_qty + self.failed_qty) > self.demand_qty:
            raise UserError(_(
                '通过数量(%(passed)s)加失败数量(%(failed)s)不能超过需求数量(%(demand)s)。',
                passed=self.passed_qty,
                failed=self.failed_qty,
                demand=self.demand_qty,
            ))

    def _validate_failed_qty(self):
        """校验失败数量：有需求数量时必须大于0"""
        if self.demand_qty > 0 and self.failed_qty <= 0:
            raise UserError(_(
                '请填写失败数量，失败数量必须大于0。当前需求数量为 %(demand)s。',
                demand=self.demand_qty,
            ))
        if self.demand_qty > 0 and \
                (self.passed_qty + self.failed_qty) > self.demand_qty:
            raise UserError(_(
                '通过数量(%(passed)s)加失败数量(%(failed)s)不能超过需求数量(%(demand)s)。',
                passed=self.passed_qty,
                failed=self.failed_qty,
                demand=self.demand_qty,
            ))

    def do_pass(self):
        """通过质检前校验：有失败数量时禁止通过"""
        if self.demand_qty > 0 and self.failed_qty > 0:
            raise UserError(_(
                '当前质检有失败数量 %(failed)s，不能通过质检。请点击"失败"按钮完成质检，'
                '系统将自动创建质量警报。',
                failed=self.failed_qty,
            ))
        if self.demand_qty > 0 and self.passed_qty <= 0:
            self.passed_qty = self.demand_qty - self.failed_qty
        self._validate_passed_qty()
        return super().do_pass()

    def do_fail(self):
        """失败质检前自动填充失败数量并校验"""
        if self.demand_qty > 0 and self.failed_qty <= 0:
            self.failed_qty = self.demand_qty - self.passed_qty
        self._validate_failed_qty()
        return super().do_fail()

    def do_measure(self):
        """测量质检：有失败数量时直接走失败流程"""
        if self.demand_qty > 0 and self.failed_qty > 0:
            return self.do_fail()
        return super().do_measure()

    def confirm_fail(self):
        """确认失败前再次校验失败数量"""
        self._validate_failed_qty()
        return super().confirm_fail()

    def confirm_measure(self):
        """确认测量前校验对应数量：有失败数量时走失败校验"""
        if self.demand_qty > 0 and self.failed_qty > 0:
            self._validate_failed_qty()
        elif self.current_check_id._measure_passes():
            self._validate_passed_qty()
        else:
            self._validate_failed_qty()
        return super().confirm_measure()
