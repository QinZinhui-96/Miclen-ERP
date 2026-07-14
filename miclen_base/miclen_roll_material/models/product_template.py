from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_roll_material = fields.Boolean(
        string='卷料',
        default=False,
        help='勾选表示此产品为卷料，后续可用于动态选料计算',
    )
    spec_length = fields.Integer(
        string='规格长(mm)',
        help='卷料的规格长度，单位毫米',
    )
    spec_width = fields.Integer(
        string='规格宽(mm)',
        help='卷料的规格宽度（即卷料宽幅），单位毫米',
    )
