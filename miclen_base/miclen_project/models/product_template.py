# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging


from odoo import api, fields, models, _
from odoo.tools.sql import create_column, column_exists

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _description = "产品模版中增加字段"


    # default_code = fields.Char(string='内部编码',
    #                            compute='_compute_default_code', store=True, readonly=False, copy=False, tracking=True)
    miclen_category_id = fields.Many2one('miclen.product.category', string='大类', copy=False)
    miclen_details_id = fields.Many2one('miclen.category.details', string='中类', copy=False)
    miclen_subcategory_id = fields.Many2one('miclen.category.subcategory', string='小类', copy=False)
    miclen_width = fields.Char('宽幅')

    @api.depends('miclen_category_id', 'miclen_details_id',
                 'miclen_subcategory_id', 'miclen_width')
    def _compute_default_code(self):
        # 先调用父类方法（处理变体同步）
        super()._compute_default_code()
        # 然后添加自定义逻辑
        for record in self:
            # 如果有自定义分类，生成新的编码
            if record.miclen_category_id:
                parts = []
                if record.miclen_category_id:
                    parts.append(record.miclen_category_id.name)
                if record.miclen_details_id:
                    parts.append(record.miclen_details_id.name)
                if record.miclen_subcategory_id:
                    parts.append(record.miclen_subcategory_id.name)
                if record.miclen_width:
                    parts.append(record.miclen_width)
                record.default_code = '-'.join(parts) if parts else ''
