# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    roll_material_config_id = fields.Many2one(
        'roll.material.config',
        string='卷料选料配置',
        compute='_compute_roll_material_config_id',
        store=True,
        compute_sudo=True,
        help='根据成品自动匹配的卷料选料配置',
    )
    has_roll_material_config = fields.Boolean(
        string='有选料配置',
        compute='_compute_roll_material_config_id',
        store=True,
        compute_sudo=True,
    )

    @api.depends('product_id')
    def _compute_roll_material_config_id(self):
        for production in self:
            config = self.env['roll.material.config'].search([
                ('product_id', '=', production.product_id.id),
                ('active', '=', True),
            ], limit=1)
            production.roll_material_config_id = config.id if config else False
            production.has_roll_material_config = bool(config)

    def action_open_roll_material_wizard(self):
        """打开卷料选料预览向导"""
        self.ensure_one()
        if not self.roll_material_config_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'roll.material.selection.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_production_id': self.id,
                },
            }
        # 预创建向导并执行选料
        wizard = self.env['roll.material.selection.wizard'].create({
            'production_id': self.id,
            'config_id': self.roll_material_config_id.id,
        })
        wizard.action_preview()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'roll.material.selection.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }
