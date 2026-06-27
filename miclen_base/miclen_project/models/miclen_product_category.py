# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class MiclenProductCategory(models.Model):
    _name = 'miclen.product.category'
    _description = "miclen产品类型"

    sequence = fields.Integer('序号', default=10)
    name = fields.Char('编码', tracking=True)
    note = fields.Char('备注', tracking=True)

