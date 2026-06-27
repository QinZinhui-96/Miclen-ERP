# Copyright 2026 Shachain
# License OPL-1 (Odoo Proprietary License v1.0)

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    login_animation_enabled = fields.Boolean(
        string="Login Animation",
        config_parameter="sc_login_animation.enabled",
        default=True,
    )
    login_animation_theme = fields.Selection(
        [("playful", "Playful"), ("professional", "Professional"), ("minimal", "Minimal")],
        string="Animation Theme",
        config_parameter="sc_login_animation.theme",
        default="playful",
    )
    login_animation_primary_color = fields.Char(
        string="Primary Color",
        config_parameter="sc_login_animation.primary_color",
        default="#6C3FF5",
    )
    login_animation_bg_color = fields.Char(
        string="Background Color",
        config_parameter="sc_login_animation.bg_color",
        default="#5B2FE8",
    )
