# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class MiclenProductCoil(models.Model):
    _name = 'miclen.product.coil'
    _rec_name = 'product_id'
    _description = "卷料选料配置"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    sequence = fields.Integer('序号', default=10)
    product_id = fields.Many2one(
        'product.product',
        string='卷材',
        required=True,
        help='触发选料的成品产品（制造单的成品）',
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        related='product_id.product_tmpl_id',
        store=True,
        string='产品模板',
    )
    coil_x = fields.Integer(
        string='规格x(mm)',
        required=True,
        default=300,
        help='所需材料片的长度，单位毫米',
    )
    coil_y = fields.Integer(
        string='规格y(mm)',
        required=True,
        default=400,
        help='所需材料片的宽度，单位毫米',
    )
    gap = fields.Integer(
        string='切割间距(mm)',
        default=10,
        required=True,
        help='切割时各方向预留的间距，单位毫米',
    )
    consume_way = fields.Selection([
        ('coil_x', 'x'),
        ('coil_y', 'y')],
        string='按（x,y）消耗', default='coil_x')
    line_ids = fields.One2many(
        'miclen.product.coil.line',
        'coil_id',
        string='卷料优先级',
    )

    def action_consume_way(self):
        self.ensure_one()
        if self.coil_x <= 0 or self.coil_y <= 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'title': "规格参数错误",
                    'message': '卷料规格 X 和 Y 必须大于 0，请重新填写！',
                    'next': {
                        'type': 'ir.actions.act_window_close'
                    },
                }
            }

        # 先清空现有记录
        self.line_ids.unlink()

        product_template_object = self.env['product.template'].sudo()
        product_product_object = self.env['product.product'].sudo()

        coil_len = self.gap
        if self.consume_way == 'coil_x':
            coil_len += self.coil_x
        else:
            coil_len += self.coil_y

        templates = product_template_object.search([('categ_id.name', '=', '卷材')], order='miclen_width')

        # 批量创建数据
        line_data = []
        for tem in templates:
            if tem.miclen_width and tem.miclen_width.isdigit() and tem.qty_available > 0:
                width_int = int(tem.miclen_width)
                if width_int >= coil_len:
                    product_id = product_product_object.search([('product_tmpl_id', '=', tem.id)])
                    if product_id:
                        line_data.append({
                            'coil_id': self.id,
                            'product_id': product_id.id,
                            'miclen_width_len': int(tem.miclen_width),
                        })

        # 批量创建所有记录
        if line_data:
            self.env['miclen.product.coil.line'].create(line_data)

class MiclenProductCoilLine(models.Model):
    _name = 'miclen.product.coil.line'
    _rec_name = 'product_id'
    _description = "卷料选料配置行"

    coil_id = fields.Many2one(
        'miclen.product.coil',
        required=True,
    )
    sequence = fields.Integer(
        string='优先级',
        default=10,
        help='数字越小优先级越高',
    )
    product_id = fields.Many2one(
        'product.product',
        string='卷料产品',
        required=True,
    )
    uom_id = fields.Many2one(related='product_id.uom_id', string='单位')
    miclen_width_len = fields.Integer(string='卷料宽幅(mm)')

    available_qty = fields.Float(
        string='可用库存',
        digits='Product Unit',
        compute='_compute_available_qty',  # 指定计算方法
    )

    @api.depends('product_id')
    def _compute_available_qty(self):
        for record in self:
            if record.product_id:
                # 推荐使用 product_id.qty_available，它返回所有仓库的当前在手总数
                record.available_qty = record.product_id.qty_available
            else:
                record.available_qty = 0.0
