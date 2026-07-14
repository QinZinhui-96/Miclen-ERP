# -*- coding: utf-8 -*-
{
    'name': 'Miclen Mrp',
    'version': '19.0.2.0',
    'category': 'Miclen',
    'website': 'https://erp.miclen.com',
    'summary': '卷料动态选料配置与管理',
    'description': """
    """,
    'depends': ['product', 'stock', 'mrp'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/product_category_view.xml'
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'author': 'Miclen.',
    'license': 'LGPL-3',
}
