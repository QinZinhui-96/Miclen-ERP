# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class QualityCheckWizard(models.TransientModel):
    _inherit = 'quality.check.wizard'

    demand_qty = fields.Float(
        string='Demand Quantity',
        related='current_check_id.demand_qty',
        readonly=True,
    )
    passed_qty = fields.Float(
        string='Passed Quantity',
        related='current_check_id.passed_qty',
        readonly=False,
    )
    failed_qty = fields.Float(
        string='Failed Quantity',
        related='current_check_id.failed_qty',
        readonly=False,
    )

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
        """通过质检前校验通过数量"""
        self._validate_passed_qty()
        return super().do_pass()

    def do_fail(self):
        """失败质检前校验失败数量"""
        self._validate_failed_qty()
        return super().do_fail()

    def confirm_fail(self):
        """确认失败前再次校验失败数量"""
        self._validate_failed_qty()
        return super().confirm_fail()

    def do_measure(self):
        """测量质检时自动填充对应数量再进入通过/失败流程"""
        if self.current_check_id._measure_passes():
            if self.demand_qty > 0 and self.passed_qty <= 0:
                self.passed_qty = self.demand_qty - self.failed_qty
            return self.do_pass()
        else:
            if self.demand_qty > 0 and self.failed_qty <= 0:
                self.failed_qty = self.demand_qty - self.passed_qty
            return self.do_fail()

    def confirm_measure(self):
        """确认测量前校验对应数量"""
        if self.current_check_id._measure_passes():
            self._validate_passed_qty()
        else:
            self._validate_failed_qty()
        return super().confirm_measure()
