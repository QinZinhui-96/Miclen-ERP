# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.fields import Command

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    coil_id = fields.Many2one('miclen.product.coil', string='卷料选料', domain="[('product_id', '=', product_id)]",)
    coil_x = fields.Integer(
        string='规格x(mm)',
        related='coil_id.coil_x',
        store=True,  # 存储到数据库
        readonly=True
    )
    coil_y = fields.Integer(
        string='规格y(mm)',
        related='coil_id.coil_y',
        store=True,  # 存储到数据库
        readonly=True
    )
    is_coil_expanded = fields.Boolean(
        string='卷材展开',
        default=False,
        help="标记该组件行是由卷料消耗向导展开生成的",
    )

    def action_button_consume(self):
        """点击卷料消耗按钮，打开卷料选料向导"""
        self.ensure_one()
        ctx = {
            'default_move_id': self.id,
            'default_product_id': self.product_id.id,
            'default_coil_id': self.coil_id.id if self.coil_id else False,
            'default_coil_x': self.coil_x,
            'default_coil_y': self.coil_y,
            'default_product_uom_qty': self.product_uom_qty,
            'default_product_uom': self.product_uom.id,
        }
        if self.coil_id:
            ctx['default_gap'] = self.coil_id.gap
            ctx['default_consume_way'] = self.coil_id.consume_way
        return {
            'type': 'ir.actions.act_window',
            'name': '卷料选料预览',
            'res_model': 'miclen.mrp.product.coil.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': ctx,
        }
