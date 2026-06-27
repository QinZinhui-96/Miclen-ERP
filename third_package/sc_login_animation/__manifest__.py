# Copyright 2026 Shachain
# License OPL-1 (Odoo Proprietary License v1.0)
{
    "name": "SC Login Animation",
    "version": "19.0.1.0.0",
    "category": "Website",
    "summary": "Animated cartoon characters with eye-tracking on login page",
    "description": "Animated cartoon characters on the login page. Pure CSS/JS, no impact on form logic.",
    "author": "Shachain",
    "website": "https://shachain.dev",
    "support": "business@shachain.dev",
    "license": "OPL-1",
    "depends": ["web"],
    "images": [
        "static/description/banner.png",
        "static/description/icon.png",
    ],
    "live_test_url": "https://demo.shachain.dev",
    "data": [
        "views/login_templates.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "sc_login_animation/static/src/css/login_animation.css",
            "sc_login_animation/static/src/js/login_animation.js",
        ],
    },
    "installable": True,
    "auto_install": False,
    "application": False,
}
