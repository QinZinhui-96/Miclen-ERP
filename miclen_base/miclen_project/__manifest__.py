# -*- coding: utf-8 -*-
{
    'name': 'Miclen Project Manager',
    'version': '19.0.1.0',
    'category': 'Miclen',
    "website": "https://erp.miclen.com",
    'summary': '限制用户只能查看被分配的作业类型',
    'description': """
        1.为作业类型添加负责人字段
        系统管理员：可以看到所有作业类型
        普通用户：只能看到自己被分配的作业类型
        
        
        2.为质量团队添加负责人字段
        系统管理员：可以看到所有作业类型
        普通用户：只能看到自己被分配的作业类型
        
        
        3.生产制造-工作中心添加负责人字段
        系统管理员：可以看到所有作业类型
        普通用户：只能看到自己被分配的作业类型
        
        
        4.采购订单过滤供应商选择时过滤个人联系人类型
        5.销售订单过滤供应商选择时过滤个人联系人类型
        
    """,
    'depends': ['stock', 'purchase', 'sale', 'mrp', 'quality_control', 'maintenance'],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',

        'views/stock_picking_type_view.xml',
        'views/quality_alert_team_view.xml',
        'views/mrp_workcenter_view.xml',
        'views/purchase_order_view.xml',
        'views/sale_order_view.xml',
        'views/miclen_product_category.xml',
        'views/miclen_category_details.xml',
        'views/miclen_category_subcategory.xml',
        'views/product_template_views.xml',
        'views/miclen_mrp_workcenter.xml',
        # 'views/mrp_routing_views.xml',
        'views/mrp_bom_views.xml',
        'views/mrp_production.xml',
        'views/mrp_workorder.xml',

        'data/miclen_product_category_data.xml',
        # 'data/miclen_category_details_data.xml',
        # 'data/miclen_category_subcategory_data.xml',

        'views/actions.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'author': 'Miclen.',
    'license': 'LGPL-3',
}