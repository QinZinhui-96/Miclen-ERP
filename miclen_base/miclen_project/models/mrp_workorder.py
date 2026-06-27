# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'
    _description = '制造工单增加字段'

    miclen_work_id = fields.Many2one(
        related='operation_id.miclen_work_id',
        store=True,
        readonly=False, string='工序'
    )
    equipment_ids = fields.Many2many(
        related='operation_id.equipment_ids', string='设备和工具'
    )
    printing_plate = fields.Char(
        string='网版',
        related='operation_id.printing_plate',
        store=True
    )
    die_mold = fields.Char(
        string='刀模',
        related='operation_id.die_mold',
        store=True
    )