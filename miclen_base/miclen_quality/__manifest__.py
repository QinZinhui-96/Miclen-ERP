# -*- coding: utf-8 -*-
{
    'name': 'Miclen Quality',
    'version': '19.0.1.0',
    'category': 'Miclen',
    'website': 'https://erp.miclen.com',
    'summary': '质检数量管理：需求数量、通过数量、失败数量',
    'description': """
        为质检模块增加数量管理功能：
        1. 需求数量：自动从调拨单获取，可手动修改
        2. 通过数量：质检人员填写
        3. 失败数量：质检人员填写
        4. 质检向导中通过/失败时必填对应数量
        5. 失败数量必须大于0
    """,
    'depends': ['quality_control'],
    'data': [
        'views/quality_check_views.xml',
        'views/quality_check_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'author': 'Miclen.',
    'license': 'LGPL-3',
}
