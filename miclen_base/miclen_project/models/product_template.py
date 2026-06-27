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

    def assign_users_to_work_type(self):
        picking_ids = self.env['stock.picking.type'].sudo().search([])

        for pick in picking_ids:
            if pick.sequence_code == 'IN':
                users = self.env['res.users'].sudo().search([
                    ('login', 'in', ['wh@126.com', 'buyer@126.com'])
                ])
                pick.write({
                    'manager_users': [(6, 0, users.ids)]
                })
                _logger.info(f"✅IN: {pick.name} 已分配用户: {[u.login for u in users]}")

            elif pick.sequence_code == 'STOR':
                users = self.env['res.users'].sudo().search([
                    ('login', 'in', ['wh@126.com', 'ck01@126.com', 'ck02@126.com'])
                ])
                pick.write({
                    'manager_users': [(6, 0, users.ids)]
                })
                _logger.info(f"✅STOR: {pick.name} 已分配用户: {[u.login for u in users]}")

            elif pick.sequence_code == 'INT':
                users = self.env['res.users'].sudo().search([])
                pick.write({
                    'manager_users': [(6, 0, users.ids)]
                })
                _logger.info(f"✅INT: {pick.name} 已分配用户: {[u.login for u in users]}")

            elif pick.sequence_code == 'OUT':
                users = self.env['res.users'].sudo().search([
                    ('login', 'in', ['wh@126.com'])
                ])
                pick.write({
                    'manager_users': [(6, 0, users.ids)]
                })
                _logger.info(f"✅OUT: {pick.name} 已分配用户: {[u.login for u in users]}")

            elif pick.sequence_code == 'PC':
                users = self.env['res.users'].sudo().search([
                    ('login', 'in', ['wh@126.com', 'worker@126.com', 'pm@126.com'])
                ])
                pick.write({
                    'manager_users': [(6, 0, users.ids)]
                })
                _logger.info(f"✅PC: {pick.name} 已分配用户: {[u.login for u in users]}")

            elif pick.sequence_code == 'MO':
                users = self.env['res.users'].sudo().search([
                    ('login', 'in', ['worker@126.com', 'pm@126.com'])
                ])
                pick.write({
                    'manager_users': [(6, 0, users.ids)]
                })
                _logger.info(f"✅MO: {pick.name} 已分配用户: {[u.login for u in users]}")

            elif pick.sequence_code == 'SFP':
                users = self.env['res.users'].sudo().search([
                    ('login', 'in', ['wh@126.com'])
                ])
                pick.write({
                    'manager_users': [(6, 0, users.ids)]
                })
                _logger.info(f"✅SFP: {pick.name} 已分配用户: {[u.login for u in users]}")


    def assign_user_permissions(self):
        user_ids = self.env['res.users'].sudo().search([])

        # 获取权限组
        group_user = self.env.ref('base.group_user')
        group_system = self.env.ref('base.group_system')

        group_sale_salesman = self.env.ref('sales_team.group_sale_salesman')
        group_sale_salesman_all_leads = self.env.ref('sales_team.group_sale_salesman_all_leads')
        group_sale_manager = self.env.ref('sales_team.group_sale_manager')

        group_purchase_user = self.env.ref('purchase.group_purchase_user')
        group_purchase_manager = self.env.ref('purchase.group_purchase_manager')

        group_stock_user = self.env.ref('stock.group_stock_user')
        group_stock_manager = self.env.ref('stock.group_stock_manager')

        group_mrp_user = self.env.ref('mrp.group_mrp_user')
        group_mrp_manager = self.env.ref('mrp.group_mrp_manager')

        group_quality_user = self.env.ref('quality.group_quality_user')
        group_quality_manager = self.env.ref('quality.group_quality_manager')

        group_equipment_manager = self.env.ref('maintenance.group_equipment_manager')

        group_account_manager = self.env.ref('account.group_account_manager')

        # 定义用户权限映射
        user_permissions = {
            'cnc01@126.com': [group_user, group_mrp_user],
            'smt01@126.com': [group_user, group_mrp_user],
            'jh01@126.com': [group_user, group_stock_user],
            'wh@126.com': [group_user, group_stock_manager],
            'ck01@126.com': [group_user, group_mrp_user],
            'ck02@126.com': [group_user, group_mrp_user],
            'account@126.com': [group_user, group_account_manager],
            'ys01@126.com': [group_user, group_stock_user],
            'admin@126.com': [
                group_system, group_sale_manager, group_purchase_manager,
                group_stock_manager, group_mrp_manager, group_quality_manager,
                group_equipment_manager, group_account_manager
            ],
            'sh01@126.com': [group_system, group_stock_user],
            'sh02@126.com': [group_system, group_stock_user],
            'mq01@126.com': [group_system, group_mrp_user],
            'worker@126.com': [group_system, group_mrp_user],
            'pm@126.com': [group_system, group_mrp_manager],
            'mj01@126.com': [group_system, group_mrp_user],
            'zh01@126.com': [group_system, group_mrp_user],
            'quality@126.com': [group_system, group_quality_manager],
            'th01@126.com': [group_system, group_mrp_user],
            'buyer@126.com': [group_system, group_purchase_manager, group_stock_manager],
            'sale@126.com': [group_system, group_sale_manager],
        }

        # 批量用户权限
        zz_users = ['zz01@126.com', 'zz02@126.com', 'zz03@126.com', 'zz04@126.com',
                    'zz05@126.com', 'zz06@126.com', 'zz07@126.com', 'zz08@126.com']
        for zz_user in zz_users:
            user_permissions[zz_user] = [group_system, group_mrp_user]

        zj_users = ['zj01@126.com', 'zj02@126.com']
        for zj_user in zj_users:
            user_permissions[zj_user] = [group_system, group_quality_user]

        # 执行赋值
        for user in user_ids:
            if user.login in user_permissions:
                groups = user_permissions[user.login]
                # 使用 group_ids 字段（可写）
                # (6, 0, ids) 会替换所有现有权限组
                user.write({
                    'group_ids': [(6, 0, [group.id for group in groups])]
                })
                _logger.info(f"✅ 已设置: {user.login} - {[group.name for group in groups]}")
            else:
                _logger.info(f"⚠️ 跳过未配置的用户: {user.login}")
