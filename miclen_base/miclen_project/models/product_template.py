# -*- coding: utf-8 -*-
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
        group_user = self.env.ref('base.group_user')            # 角色用户
        group_system = self.env.ref('base.group_system')        # 角色管理员

        group_sale_salesman = self.env.ref('sales_team.group_sale_salesman')                        # 用户：仅自己的单据
        group_sale_salesman_all_leads = self.env.ref('sales_team.group_sale_salesman_all_leads')    # 用户：所有单据
        group_sale_manager = self.env.ref('sales_team.group_sale_manager')                          # 销售 管理员

        group_purchase_user = self.env.ref('purchase.group_purchase_user')          # 采购 用户
        group_purchase_manager = self.env.ref('purchase.group_purchase_manager')    # 采购 管理员

        group_stock_user = self.env.ref('stock.group_stock_user')                   # 库存 用户
        group_stock_manager = self.env.ref('stock.group_stock_manager')             # 库存 管理员

        group_mrp_user = self.env.ref('mrp.group_mrp_user')                         # 制造 用户
        group_mrp_manager = self.env.ref('mrp.group_mrp_manager')                   # 制造 管理员

        group_quality_user = self.env.ref('quality.group_quality_user')             # 质量 用户
        group_quality_manager = self.env.ref('quality.group_quality_manager')       # 质量 管理员

        group_equipment_manager = self.env.ref('maintenance.group_equipment_manager')   # 维护管理 管理员

        group_account_manager = self.env.ref('account.group_account_manager')           # 会计 管理员

        # 定义用户权限映射
        user_permissions = {
            'cnc01@126.com': [group_user, group_mrp_user, group_equipment_manager],
            'smt01@126.com': [group_user, group_mrp_user, group_equipment_manager],
            'jh01@126.com': [group_user, group_stock_user, group_equipment_manager],
            'wh@126.com': [group_user, group_stock_manager, group_equipment_manager],
            'ck01@126.com': [group_user, group_mrp_user, group_equipment_manager],
            'ck02@126.com': [group_user, group_mrp_user, group_equipment_manager],
            'account@126.com': [group_user, group_account_manager, group_equipment_manager],
            'ys01@126.com': [group_user, group_stock_user, group_equipment_manager],
            'admin@126.com': [
                group_system, group_sale_manager, group_purchase_manager,
                group_stock_manager, group_mrp_manager, group_quality_manager,
                group_equipment_manager, group_account_manager
            ],
            'sh01@126.com': [group_user, group_stock_user, group_equipment_manager],
            'sh02@126.com': [group_user, group_stock_user, group_equipment_manager],
            'mq01@126.com': [group_user, group_mrp_user, group_equipment_manager],
            'worker@126.com': [group_user, group_mrp_user, group_equipment_manager],
            'pm@126.com': [group_user, group_mrp_manager, group_equipment_manager],
            'mj01@126.com': [group_user, group_mrp_user, group_equipment_manager],
            'zh01@126.com': [group_user, group_mrp_user, group_equipment_manager],
            'quality@126.com': [group_user, group_quality_manager, group_equipment_manager],
            'th01@126.com': [group_user, group_mrp_user, group_equipment_manager],
            'buyer@126.com': [group_user, group_purchase_manager, group_stock_manager, group_equipment_manager],
            'sale@126.com': [group_user, group_sale_manager, group_equipment_manager],
        }

        # 批量用户权限
        zz_users = ['zz01@126.com', 'zz02@126.com', 'zz03@126.com', 'zz04@126.com',
                    'zz05@126.com', 'zz06@126.com', 'zz07@126.com', 'zz08@126.com']
        for zz_user in zz_users:
            user_permissions[zz_user] = [group_user, group_mrp_user, group_equipment_manager]

        zj_users = ['zj01@126.com', 'zj02@126.com']
        for zj_user in zj_users:
            user_permissions[zj_user] = [group_user, group_quality_user, group_equipment_manager]

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
                _logger.info(f"⚠跳过未配置的用户: {user.login}")

    def set_user_access_rights(self):
        """一键赋值权限"""
        user_ids = self.env['res.users'].sudo().search([])
        for user in user_ids:
            if user.login == 'sale@126.com':
                self.set_access_rights('销售', user)
            elif user.login == 'buyer@126.com':
                self.set_access_rights('采购', user)
            elif user.login in ['th01@126.com', 'zh01@126.com', 'zz08@126.com', 'zz07@126.com', 'zz06@126.com',
                                'zz05@126.com', 'zz04@126.com', 'zz03@126.com', 'zz02@126.com', 'zz01@126.com',
                                'mj01@126.com', 'mq01@126.com', 'ym01@126.com', 'ys01@126.com', 'smt01@126.com',
                                'cnc01@126.com']:
                self.set_access_rights('工序', user)
            elif user.login in ['quality@126.com', 'zj01@126.com', 'zj02@126.com']:
                self.set_access_rights('质量', user)
            elif user.login in ['pm@126.com', 'worker@126.com']:
                self.set_access_rights('生产', user)
            elif user.login in ['sh02@126.com', 'sh01@126.com']:
                self.set_access_rights('收货', user)
            elif user.login in ['wh@126.com', 'ck01@126.com', 'ck02@126.com']:
                self.set_access_rights('仓库', user)
            elif user.login in ['jh01@126.com']:
                self.set_access_rights('交货', user)

    def clear_user_access_rights(self, role_name):
        """一键清空权限"""
        # access_role = self.env['access.role'].sudo()
        if role_name:
            user_ids = self.env['res.users'].sudo().search([
                ('access_role_id.name', '=', role_name)
            ])
        else:
            user_ids = self.env['res.users'].sudo().search([])
        if user_ids:
            user_ids.write({'access_role_id': None})
        # if access_role:
        #     access_roles = access_role.search([
        #         ('name', '=', access_role)
        #     ])
        #     if access_roles:
        #         access_roles.write({'user_ids': None})

    def set_access_rights(self, name, user):
        role_management = self.env['role.management'].sudo()
        access_role = self.env['access.role'].sudo()
        menu_ids = self.env['ir.ui.menu'].sudo()
        management_id = role_management.search([('name', '=', name)], limit=1)
        access_id = access_role.search([('name', '=', name)], limit=1)
        menus_to_add = self.env['ir.ui.menu']
        if management_id:
            hide_app = ['Discuss', 'Dashboards', 'Maintenance', 'Barcode', 'Apps']
            for hide in hide_app:
                is_menu = menu_ids.search([('name', '=', hide)])
                if is_menu:
                    menus_to_add |= is_menu
            # 使用 (6, 0, ids) 方式
            management_id.write({'menu_ids': [(4, menu.id, 0) for menu in menus_to_add]})
            user.write({'access_role_id': access_id.id})
