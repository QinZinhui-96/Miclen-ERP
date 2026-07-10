# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class QualityAlert(models.Model):
    _inherit = "quality.alert"

    demand_qty = fields.Float(
        string='Demand Quantity',
        digits='Product Unit',
        related='check_id.demand_qty',
        readonly=True,
        help='质检的需求数量',
    )
    passed_qty = fields.Float(
        string='Passed Quantity',
        digits='Product Unit',
        related='check_id.passed_qty',
        readonly=True,
        help='质检的通过数量',
    )
    failed_qty = fields.Float(
        string='Failed Quantity',
        digits='Product Unit',
        related='check_id.failed_qty',
        readonly=True,
        help='质检的失败数量',
    )
    return_picking_id = fields.Many2one(
        'stock.picking',
        string='Return Picking',
        readonly=True,
        copy=False,
        help='退回供应商的调拨单',
    )

    def action_return_to_supplier(self):
        """创建退回供应商的调拨单，将失败数量的产品退回给供应商"""
        self.ensure_one()
        check = self.check_id
        if not check:
            raise UserError(_('此质量警报没有关联的质检记录，无法退回。'))
        if check.failed_qty <= 0:
            raise UserError(_('没有失败数量可退回。'))

        # 获取原始收货调拨单
        picking = self.picking_id or check.picking_id
        if not picking:
            raise UserError(_('没有关联的调拨单，无法创建退回。'))
        if picking.state != 'done':
            raise UserError(_('原始收货单尚未完成（状态: %s），无法创建退回。', picking.state))

        # 获取退货操作类型
        return_type = picking.picking_type_id.return_picking_type_id
        if not return_type:
            raise UserError(_('未配置退货操作类型，请在仓库设置中为「%s」配置退货操作类型。'
                              % picking.picking_type_id.name))

        # 找到原始调拨单中对应产品的库存移动
        product = check.product_id or self.product_id
        if not product:
            raise UserError(_('没有指定要退回的产品。'))
        moves = picking.move_ids.filtered(lambda m: m.product_id == product)
        if not moves:
            raise UserError(_('在调拨单 %s 中未找到产品 %s 的库存移动。'
                              % (picking.name, product.display_name)))

        # 准备退回调拨单的值
        location = picking.location_dest_id  # 来源：我们的库存
        if return_type.default_location_dest_id:
            location_dest = return_type.default_location_dest_id
        else:
            location_dest = picking.location_id  # 目标：供应商位置

        new_picking_vals = {
            'move_ids': [],
            'picking_type_id': return_type.id,
            'state': 'draft',
            'return_id': picking.id,
            'origin': _("Return of %(picking)s (Quality Alert: %(alert)s)",
                        picking=picking.name, alert=self.name),
            'location_id': location.id,
            'location_dest_id': location_dest.id,
            'partner_id': picking.partner_id.id if picking.partner_id else False,
        }
        new_picking = picking.copy(new_picking_vals)
        new_picking.user_id = False

        # 发布来源链接消息
        new_picking.message_post_with_source(
            'mail.message_origin_link',
            render_values={'self': new_picking, 'origin': picking},
            subtype_xmlid='mail.mt_note',
        )

        # 创建退货移动行（按失败数量）
        remaining = check.failed_qty
        for move in moves:
            if remaining <= 0:
                break
            move_done_qty = move.quantity or move.product_uom_qty
            if move_done_qty <= 0:
                continue
            qty = min(remaining, move_done_qty)

            move_vals = {
                'product_id': move.product_id.id,
                'product_uom_qty': qty,
                'product_uom': move.product_uom.id,
                'picking_id': new_picking.id,
                'state': 'draft',
                'date': fields.Datetime.now(),
                'location_id': location.id,
                'location_dest_id': location_dest.id,
                'picking_type_id': return_type.id,
                'warehouse_id': return_type.warehouse_id.id if return_type.warehouse_id else False,
                'origin_returned_move_id': move.id,
                'procure_method': 'make_to_stock',
            }
            # 关联采购订单行（如果安装了 purchase_stock）
            if hasattr(move, 'purchase_line_id') and move.purchase_line_id:
                move_vals['purchase_line_id'] = move.purchase_line_id.id

            move.copy(move_vals)
            remaining -= qty

        # 确认并分配
        new_picking.action_confirm()
        new_picking.action_assign()

        # 关联到质量警报
        self.return_picking_id = new_picking.id

        # 在质量警报中留言
        self.message_post(
            body=_('已创建退回供应商调拨单: <a href="#" data-oe-model="stock.picking" '
                   'data-oe-id="%s">%s</a>，退回数量: %s %s')
            % (new_picking.id, new_picking.name, check.failed_qty, product.uom_id.name),
        )

        return {
            'name': _('Return to Supplier'),
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'res_id': new_picking.id,
            'type': 'ir.actions.act_window',
            'context': self.env.context,
        }

    def action_open_return_picking(self):
        """打开已创建的退回调拨单"""
        self.ensure_one()
        if not self.return_picking_id:
            return False
        return {
            'name': _('Return to Supplier'),
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'res_id': self.return_picking_id.id,
            'type': 'ir.actions.act_window',
            'context': self.env.context,
        }
