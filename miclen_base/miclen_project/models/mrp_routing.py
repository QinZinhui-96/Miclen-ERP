# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'
    _description = "miclen增加字段"

    name = fields.Char(string='工序名称', compute='_compute_miclen_fields', store=True, readonly=False)
    workcenter_id = fields.Many2one('mrp.workcenter', string='工作中心',
                                    compute='_compute_miclen_fields', store=True, readonly=False)
    miclen_work_id = fields.Many2one('miclen.mrp.workcenter', string='工序')
    equipment_ids = fields.Many2many('maintenance.equipment', string='设备和工具',
                                     compute='_compute_miclen_fields', store=True, readonly=False)
    printing_plate = fields.Char(string='网版', compute='_compute_miclen_fields', store=True, readonly=False)
    die_mold = fields.Char(string='刀模', compute='_compute_miclen_fields', store=True, readonly=False)
    equipment_domain = fields.Char('设备domain', compute='_compute_equipment_domain', store=True)

    def create(self, vals_list):
        """
            导入数据的时候直接可以使用工序名称即可导入
        """
        for vals in vals_list:
            work_name = vals.get('miclen_work_id')
            if work_name and not vals.get('workcenter_id') and not vals.get('name'):
                work = self.env['miclen.mrp.workcenter'].browse(vals['miclen_work_id'])
                vals['name'] = work.name
                vals['workcenter_id'] = work.workcenter_id.id
                vals['equipment_ids'] = [(6, 0, work.equipment_ids.ids)]
                vals['printing_plate'] = work.printing_plate
                vals['die_mold'] = work.die_mold
        return super().create(vals_list)

    @api.depends('miclen_work_id')
    def _compute_miclen_fields(self):
        """
            页面中手动创建的时候可以直接选择一个工序名称 然后自动带出里面的数据出来
        """
        for record in self:
            if record.miclen_work_id:
                work = record.miclen_work_id
                record.name = work.name
                record.workcenter_id = work.workcenter_id
                record.equipment_ids = work.equipment_ids
                record.printing_plate = work.printing_plate or ''
                record.die_mold = work.die_mold or ''
            else:
                record.name = False
                record.workcenter_id = False
                record.equipment_ids = [(5, 0, 0)]  # 清空 many2many
                record.printing_plate = ''
                record.die_mold = ''


    @api.depends('miclen_work_id')
    def _compute_equipment_domain(self):
        """
            动态根据miclen_work_id来过滤
        """
        for rec in self:
            if rec.workcenter_id and rec.workcenter_id.equipment_ids:
                equipments = rec.workcenter_id.equipment_ids.ids
                rec.equipment_domain = "[('id', 'in', %s)]" % equipments
            else:
                rec.equipment_domain = "[('id', '=', -1)]"