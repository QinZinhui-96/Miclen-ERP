# -*- coding: utf-8 -*-
{
    'name': 'Miclen Roll Material',
    'version': '19.0.2.0',
    'category': 'Miclen',
    'website': 'https://erp.miclen.com',
    'summary': '卷料动态选料配置与管理',
    'description': """
        卷料产品管理模块

        1. 产品模板增加卷料标记（is_roll_material）和规格长宽
        2. 卷料选料配置表（roll.material.config）+ 优先级行
        3. 选料算法：根据需求尺寸自动计算最优卷料选择
           - 支持每排多片切割优化
           - 按优先级分配库存
           - 库存缺口提示
        4. 制造单集成：自动匹配配置 + 选料预览向导 + 一键应用
        5. 配置表测试功能：无需制造单即可验证选料结果
    """,
    'depends': ['product', 'stock', 'mrp'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/roll_material_config_views.xml',
        'views/roll_material_selection_wizard_views.xml',
        'views/mrp_production_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'author': 'Miclen.',
    'license': 'LGPL-3',
}
