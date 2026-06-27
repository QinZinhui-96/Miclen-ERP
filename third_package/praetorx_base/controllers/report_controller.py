# Copyright 2025 Lars Weiler
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

"""Custom report controller to support configurable PDF display mode.

This controller overrides the default Odoo report download behavior
to optionally open PDFs inline (in browser tab) instead of forcing download.

The behavior is controlled by the system parameter 'praetorx.report_display_mode':
- 'download' (default): Force download (Content-Disposition: attachment)
- 'inline': Open in browser tab (Content-Disposition: inline)
"""

import logging

from odoo import http
from odoo.http import request

from odoo.addons.web.controllers.report import ReportController

_logger = logging.getLogger(__name__)


class PraetorxReportController(ReportController):
    """Override report controller for configurable PDF display."""

    @http.route(["/report/download"], type="http", auth="user")
    def report_download(self, data, context=None, token=None, readonly=True):
        """Override to support inline PDF display based on system configuration.

        When praetorx.report_display_mode is set to 'inline', PDFs will open
        in a new browser tab instead of being downloaded.
        """
        # Get the response from parent
        response = super().report_download(data, context, token, readonly)

        # Check if we should modify the Content-Disposition header
        try:
            display_mode = (
                request.env["ir.config_parameter"].sudo().get_param("praetorx.report_display_mode", "download")
            )

            if display_mode == "inline":
                # Get current Content-Disposition header
                content_disp = response.headers.get("Content-Disposition", "")

                if content_disp and "attachment;" in content_disp:
                    # Replace 'attachment' with 'inline' to open in browser
                    new_content_disp = content_disp.replace("attachment;", "inline;")
                    response.headers["Content-Disposition"] = new_content_disp
                    _logger.debug("Report display mode: inline (open in browser)")

        except Exception as e:
            # If anything fails, just return original response
            _logger.warning("Error modifying report display mode: %s", e)

        return response
