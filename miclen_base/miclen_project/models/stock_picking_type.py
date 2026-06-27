# -*- coding: utf-8 -*-


from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'
    _description = "作业类型中增加仓管"

    manager_users = fields.Many2many('res.users', string='管理用户', help='选择哪些用户可以查看此作业类型')
