# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from collections import defaultdict
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pytz import timezone
from ast import literal_eval
from markupsafe import escape, Markup
from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.fields import Command, Domain
from odoo.tools import format_amount, format_date, formatLang, groupby, OrderedSet, SQL
from odoo.tools.float_utils import float_is_zero, float_repr
from odoo.exceptions import AccessDenied, UserError, ValidationError

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    _description = "采购单增加过滤"

