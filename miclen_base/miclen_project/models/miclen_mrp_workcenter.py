# -*- coding: utf-8 -*-


from odoo import fields, models, api


class MiclenMrpWorkcenter(models.Model):
    _name = 'miclen.mrp.workcenter'
    _description = "工序配置表"

    sequence = fields.Integer('序号', default=10)
    description = fields.Char('工序', compute='_compute_name', store=True)
    name = fields.Char(string='作业')
    workcenter_id = fields.Many2one('mrp.workcenter', string='工作中心')
    equipment_ids = fields.Many2many('maintenance.equipment', string='设备和工具')
    equipment_domain = fields.Char('设备详情', compute='_compute_equipment_domain', store=True)
    printing_plate = fields.Char(string='网版')
    die_mold = fields.Char(string='刀模')

    @api.depends('name', 'workcenter_id', 'workcenter_id.name')
    def _compute_name(self):
        for record in self:
            # 获取作业名称和工作中心名称
            name = record.name or ''
            workcenter_name = record.workcenter_id.name or ''
            # 组合名称，如果两者都有则用空格连接，否则只显示有的那个
            if name and workcenter_name:
                record.description = f"{name} - {workcenter_name}"
            elif name:
                record.description = name
            elif workcenter_name:
                record.description = workcenter_name
            else:
                record.description = ''

    @api.depends('workcenter_id')
    def _compute_equipment_domain(self):
        for rec in self:
            if rec.workcenter_id:
                equipments = rec.workcenter_id.equipment_ids.ids
                rec.equipment_domain = "[('id', 'in', %s)]" % equipments
            else:
                rec.equipment_domain = "[('id', '=', -1)]"