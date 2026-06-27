# Copyright 2025 Lars Weiler
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from markupsafe import Markup

from odoo import api, models


class ValidationMixin(models.AbstractModel):
    """Validation Mixin with HTML Summary.

    This abstract model provides a reusable pattern for validation logic
    with HTML-formatted summaries. Inherit from this mixin to add validation
    capabilities to any model.

    Example usage:
        class MyModel(models.Model):
            _name = 'my.model'
            _inherit = ['praetorx.validation.mixin']

            def validate_all(self):
                results = []
                if not self.required_field:
                    results.append({
                        'level': 'error',
                        'message': 'Required field is missing',
                        'field': 'required_field'
                    })
                if self.amount < 0:
                    results.append({
                        'level': 'warning',
                        'message': 'Amount is negative',
                        'field': 'amount'
                    })
                return results

        # In view, add a field to display the summary:
        validation_summary = fields.Html(
            compute='_compute_validation_summary',
            sanitize=False
        )

        @api.depends('required_field', 'amount')
        def _compute_validation_summary(self):
            for record in self:
                record.validation_summary = record.get_validation_summary_html()
    """

    _name = "praetorx.validation.mixin"
    _description = "Validation Mixin with HTML Summary"

    def validate_all(self):
        """Validate record and return list of validation results.

        Override this method in inheriting models to implement specific
        validation logic.

        Returns:
            list: List of dicts with keys:
                - level (str): 'error' or 'warning'
                - message (str): Human-readable validation message
                - field (str, optional): Technical field name
                - code (str, optional): Error code for programmatic handling

        Example:
            [
                {
                    'level': 'error',
                    'message': 'Total amount must be positive',
                    'field': 'amount_total',
                    'code': 'INVALID_AMOUNT'
                },
                {
                    'level': 'warning',
                    'message': 'Payment term is approaching',
                    'field': 'payment_date',
                    'code': 'PAYMENT_DUE_SOON'
                }
            ]
        """
        return []

    def get_validation_summary_html(self):
        """Generate HTML summary of validation results.

        This method calls validate_all() and formats the results as HTML
        with appropriate styling using Bootstrap alert classes.

        Returns:
            Markup: HTML-safe formatted validation summary
        """
        results = self.validate_all()

        if not results:
            return Markup(
                '<div class="alert alert-success mb-0"><i class="fa fa-check-circle"></i> All validations passed</div>'
            )

        errors = [r for r in results if r.get("level") == "error"]
        warnings = [r for r in results if r.get("level") == "warning"]

        html_parts = ['<div class="validation-summary">']

        if errors:
            html_parts.append(
                '<div class="alert alert-danger mb-2">'
                '<strong><i class="fa fa-times-circle"></i> Errors:</strong>'
                '<ul class="mb-0 mt-2">'
            )
            for error in errors:
                message = error.get("message", "Unknown error")
                field = error.get("field", "")
                field_label = f" ({field})" if field else ""
                html_parts.append(f"<li>{message}{field_label}</li>")
            html_parts.append("</ul></div>")

        if warnings:
            html_parts.append(
                '<div class="alert alert-warning mb-0">'
                '<strong><i class="fa fa-exclamation-triangle"></i> Warnings:</strong>'
                '<ul class="mb-0 mt-2">'
            )
            for warning in warnings:
                message = warning.get("message", "Unknown warning")
                field = warning.get("field", "")
                field_label = f" ({field})" if field else ""
                html_parts.append(f"<li>{message}{field_label}</li>")
            html_parts.append("</ul></div>")

        html_parts.append("</div>")

        return Markup("".join(html_parts))

    def is_valid(self):
        """Check if record passes all validations.

        Returns True only if there are no errors. Warnings are allowed.

        Returns:
            bool: True if valid (no errors), False otherwise
        """
        results = self.validate_all()
        return not any(r.get("level") == "error" for r in results)

    def has_warnings(self):
        """Check if record has any validation warnings.

        Returns:
            bool: True if warnings exist, False otherwise
        """
        results = self.validate_all()
        return any(r.get("level") == "warning" for r in results)

    def get_validation_errors(self):
        """Get list of error messages only.

        Returns:
            list: List of error message strings
        """
        results = self.validate_all()
        return [r.get("message", "Unknown error") for r in results if r.get("level") == "error"]

    def get_validation_warnings(self):
        """Get list of warning messages only.

        Returns:
            list: List of warning message strings
        """
        results = self.validate_all()
        return [r.get("message", "Unknown warning") for r in results if r.get("level") == "warning"]

    def assert_valid(self):
        """Raise UserError if validation fails.

        This is useful for blocking operations that require valid data.

        Raises:
            UserError: If validation errors exist, with combined error messages
        """
        from odoo.exceptions import UserError

        if not self.is_valid():
            errors = self.get_validation_errors()
            error_msg = "\n".join(f"• {err}" for err in errors)
            raise UserError(f"Validation failed:\n{error_msg}")

    @api.model
    def get_validation_summary_for_records(self, records):
        """Get combined validation summary for multiple records.

        Useful for batch validation displays.

        Args:
            records: Recordset to validate

        Returns:
            Markup: HTML summary for all records
        """
        if not records:
            return Markup('<div class="alert alert-info mb-0">No records to validate</div>')

        all_errors = []
        all_warnings = []

        for record in records:
            results = record.validate_all()
            for result in results:
                message = result.get("message", "")
                rec_label = record.display_name or f"ID {record.id}"
                labeled_msg = f"{rec_label}: {message}"

                if result.get("level") == "error":
                    all_errors.append(labeled_msg)
                elif result.get("level") == "warning":
                    all_warnings.append(labeled_msg)

        if not all_errors and not all_warnings:
            return Markup(
                '<div class="alert alert-success mb-0">'
                f'<i class="fa fa-check-circle"></i> '
                f"All {len(records)} record(s) passed validation"
                "</div>"
            )

        html_parts = ['<div class="validation-summary-batch">']

        if all_errors:
            html_parts.append(
                f'<div class="alert alert-danger mb-2">'
                f'<strong><i class="fa fa-times-circle"></i> '
                f"{len(all_errors)} Error(s):</strong>"
                f'<ul class="mb-0 mt-2">'
            )
            for error in all_errors:
                html_parts.append(f"<li>{error}</li>")
            html_parts.append("</ul></div>")

        if all_warnings:
            html_parts.append(
                f'<div class="alert alert-warning mb-0">'
                f'<strong><i class="fa fa-exclamation-triangle"></i> '
                f"{len(all_warnings)} Warning(s):</strong>"
                f'<ul class="mb-0 mt-2">'
            )
            for warning in all_warnings:
                html_parts.append(f"<li>{warning}</li>")
            html_parts.append("</ul></div>")

        html_parts.append("</div>")

        return Markup("".join(html_parts))
