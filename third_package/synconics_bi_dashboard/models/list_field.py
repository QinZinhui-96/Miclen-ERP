from odoo import fields, models


class ListFields(models.Model):
    _name = "list.fields"
    _description = "列表字段"

    sequence = fields.Integer()
    list_field_id = fields.Many2one(
        "ir.model.fields",
        string="字段",
        help="add column fields for the standard list view",
    )
    list_measure_id = fields.Many2one(
        "ir.model.fields",
        string="Field ",
        help="为标准列表视图添加列字段",
    )
    model_id = fields.Many2one("ir.model", string='模型')
    field_id = fields.Many2one(
        "dashboard.chart", ondelete="cascade", index=True, copy=False, string="关联图表"
    )
    measure_id = fields.Many2one(
        "dashboard.chart", ondelete="cascade", index=True, copy=False, string="关联度量"
    )
    value_type = fields.Selection(
        [("sum", "求和"), ("avg", "平均值")],
        string="操作类型",
        default="sum",
        help="设置字段值类型",
    )
