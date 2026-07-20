# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    miclen_is_coil = fields.Boolean('选材规格', related='product_tmpl_id.miclen_is_coil', store=True)
    miclen_coil_w = fields.Integer(string='规格w(mm)', related='product_tmpl_id.miclen_coil_w', store=True)
    miclen_coil_l = fields.Integer(string='规格l(mm)', related='product_tmpl_id.miclen_coil_l', store=True)
    miclen_gap = fields.Integer(string='切割间距(mm)', related='product_tmpl_id.miclen_gap', store=True)
    miclen_condition = fields.Char(string='筛选条件', related='product_tmpl_id.miclen_condition', store=True)

    def action_button_consume(self):
        """点击卷料消耗按钮，打开卷料选料向导

        显式创建 wizard 记录并加载匹配卷材，确保 line_ids 在数据库中存在，
        这样用户勾选 selected 时 onchange 才能正常触发。
        """
        self.ensure_one()
        wizard = self.env['miclen.mrp.product.coil.wizard'].create({
            'move_id': self.id,
            'product_id': self.product_id.id,
            'product_uom_qty': self.product_uom_qty,
            'product_uom': self.product_uom.id,
        })
        # 直接加载匹配卷材到子表（创建真实的 DB 记录）
        wizard._load_matching_materials()
        return {
            'type': 'ir.actions.act_window',
            'name': '卷料选料预览',
            'res_model': 'miclen.mrp.product.coil.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }
