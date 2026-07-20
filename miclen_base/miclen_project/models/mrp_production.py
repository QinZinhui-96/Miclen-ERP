# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.fields import Command

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    _description = '制造单卷材动态展开'

    # def _get_moves_raw_values(self):
    #     """重写 BOM 展开：有卷材配置的产品按库存优先级拆分成多条卷料 move。"""
    #     moves = super()._get_moves_raw_values()
    #     result = []
    #     for move_vals in moves:
    #         product_id = move_vals.get('product_id')
    #         product = self.env['product.product'].browse(product_id)
    #         # 查找该产品的卷料配置
    #         coil_config = self.env['miclen.product.coil'].sudo().search([('product_id', '=', product_id)], limit=1)
    #         if coil_config:
    #             # 如果有配置，将 coil_id 添加到 move_vals 中
    #             move_vals['coil_id'] = coil_config.id
    #         result.append(move_vals)
    #     return result
