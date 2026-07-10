# -*- coding: utf-8 -*-
{
    'name': 'Miclen Quality',
    'version': '19.0.3.0',
    'category': 'Miclen',
    'website': 'https://erp.miclen.com',
    'summary': '质检数量管理：需求数量、通过数量、失败数量、通过率、失败原因、自动警报',
    'description': """
        为质检模块增加数量管理及便捷功能：
        1. 需求数量：自动从调拨单获取，可手动修改
        2. 通过数量：质检人员填写
        3. 失败数量：质检人员填写
        4. 剩余数量：自动计算（需求 - 通过 - 失败）
        5. 通过率：自动计算并显示进度条
        6. 失败原因：可选择分类，便于统计追踪
        7. 质检备注：记录质检观察和备注
        8. 数量联动：填写通过数量自动计算失败数量，反之亦然
        9. 质检向导中通过/失败时必填对应数量
        10. 失败时自动创建质量警报（含数量摘要）
        11. 批量通过功能：列表页一键通过多条质检
        12. 搜索过滤：有失败数量、全部通过、有待检数量
        13. 质量警报显示需求数量/通过数量/失败数量
        14. 退回供应商：质量警报中一键创建退回调拨单，将失败数量退回给供应商
    """,
    'depends': ['quality_control'],
    'data': [
        'views/quality_check_views.xml',
        'views/quality_check_wizard_views.xml',
        'views/quality_alert_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'author': 'Miclen.',
    'license': 'LGPL-3',
}
