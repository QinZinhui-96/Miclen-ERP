# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class MiclenProductCategoryDetails(models.Model):
    _name = 'miclen.category.details'
    _description = "miclen产品中类"

    sequence = fields.Integer('序号', default=10)
    name = fields.Char('编码', tracking=True)
    note = fields.Char('备注', tracking=True)