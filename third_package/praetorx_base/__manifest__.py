# Copyright 2025 Lars Weiler
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    "name": "Base",
    "version": "19.0.1.1.1",
    "category": "PraetorX/Core",
    "summary": "Queue Jobs, Batch Processing & Validation Framework for Odoo",
    "description": """
Praetorx Base - Foundation Module
==================================

This module provides reusable technical patterns extracted from production
codebases. It serves as a foundation for building robust Odoo applications.

Key Features
------------

* **Queue Job System**: Background job processing via cron with state management
* **Validation Mixin**: Structured validation with HTML-formatted summaries
* **Batch Processing Mixin**: State machine pattern for parent-child workflows
* **Split View Component**: OWL component for master-detail UI patterns

Use Cases
---------

* Background processing of large datasets
* Multi-step validation workflows with user feedback
* Document workflows (draft → validated → posted)
* Master-detail UI layouts

Technical Details
-----------------

All patterns are implemented as abstract models or mixins that can be
inherited by concrete models. This promotes code reuse and consistency
across modules.

Author & Maintainer
-------------------

* Author: Lars Weiler
* Maintainer: Syntax & Sabotage
* Website: https://praetorx.net
* Support: support@syntaxandsabotage.io
    """,
    "author": "Syntax & Sabotage, Lars Weiler",
    "maintainer": "Syntax & Sabotage",
    "website": "https://praetorx.net",
    "support": "support@syntaxandsabotage.io",
    "license": "LGPL-3",
    "price": 0,
    "currency": "EUR",
    "depends": [
        "base",
        "mail",
        "web",
    ],
    "data": [
        "data/module_category_data.xml",
        "security/praetorx_groups.xml",
        "security/ir.model.access.csv",
        "data/queue_job_cron.xml",
        "views/praetorx_menus.xml",
        "views/app_store_views.xml",
        "views/queue_job_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "images": [
        "static/description/banner.png",
        "static/description/icon.png",
    ],
    "assets": {
        "web.assets_backend": [
            "praetorx_base/static/src/scss/app_store.scss",
            "praetorx_base/static/src/js/split_view.js",
            "praetorx_base/static/src/xml/split_view.xml",
            "praetorx_base/static/src/js/app_store/app_store.js",
            "praetorx_base/static/src/xml/app_store.xml",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
