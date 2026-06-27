# Copyright 2025 Lars Weiler
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Extend settings with Praetorx base configuration."""

    _name = "res.config.settings"
    _inherit = "res.config.settings"

    # Report Display Settings
    praetorx_report_display_mode = fields.Selection(
        selection=[
            ("download", "Download PDF"),
            ("inline", "Open in Browser Tab"),
        ],
        string="PDF Report Display",
        config_parameter="praetorx.report_display_mode",
        default="download",
        help="Controls how PDF reports are displayed:\n"
        "- Download: Save file to disk (default Odoo behavior)\n"
        "- Open in Browser: Display PDF in new browser tab",
    )
