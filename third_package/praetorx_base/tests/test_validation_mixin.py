# Copyright 2025 Lars Weiler
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from unittest.mock import patch

from markupsafe import Markup

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "praetorx")
class TestValidationMixin(TransactionCase):
    """Test validation mixin functionality.

    Since ValidationMixin is abstract, we test via the registered model.
    Odoo 19 makes model attributes read-only, so we use unittest.mock.patch
    instead of direct attribute assignment.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env["res.partner"]
        cls.valid_partner = cls.Partner.create(
            {"name": "Valid Partner", "email": "valid@example.com"}
        )
        cls.invalid_partner = cls.Partner.create(
            {"name": "Invalid Partner", "email": ""}
        )
        cls.MixinModel = type(cls.env["praetorx.validation.mixin"])

    def test_01_validate_all_default_empty(self):
        """Test validate_all returns empty list by default."""
        Mixin = self.env["praetorx.validation.mixin"]
        results = Mixin.validate_all()
        self.assertEqual(results, [])

    def test_02_validation_summary_html_success(self):
        """Test HTML summary shows success when no errors."""
        Mixin = self.env["praetorx.validation.mixin"]
        html = Mixin.get_validation_summary_html()
        self.assertIsInstance(html, Markup)
        self.assertIn("alert-success", str(html))
        self.assertIn("All validations passed", str(html))
        self.assertIn("fa-check-circle", str(html))

    def test_03_validation_summary_html_with_errors(self):
        """Test HTML summary shows errors correctly."""
        Mixin = self.env["praetorx.validation.mixin"]
        mock_results = [
            {"level": "error", "message": "Email is required", "field": "email"},
            {"level": "error", "message": "Phone number is invalid", "field": "phone"},
        ]
        with patch.object(self.MixinModel, "validate_all", return_value=mock_results):
            html = Mixin.get_validation_summary_html()
        self.assertIsInstance(html, Markup)
        self.assertIn("alert-danger", str(html))
        self.assertIn("Errors:", str(html))
        self.assertIn("Email is required", str(html))
        self.assertIn("Phone number is invalid", str(html))
        self.assertIn("fa-times-circle", str(html))

    def test_04_validation_summary_html_with_warnings(self):
        """Test HTML summary shows warnings correctly."""
        Mixin = self.env["praetorx.validation.mixin"]
        mock_results = [
            {"level": "warning", "message": "Address is incomplete", "field": "street"},
            {"level": "warning", "message": "No payment terms set", "field": "payment_term_id"},
        ]
        with patch.object(self.MixinModel, "validate_all", return_value=mock_results):
            html = Mixin.get_validation_summary_html()
        self.assertIsInstance(html, Markup)
        self.assertIn("alert-warning", str(html))
        self.assertIn("Warnings:", str(html))
        self.assertIn("Address is incomplete", str(html))
        self.assertIn("No payment terms set", str(html))
        self.assertIn("fa-exclamation-triangle", str(html))

    def test_05_validation_summary_html_with_mixed(self):
        """Test HTML summary shows both errors and warnings."""
        Mixin = self.env["praetorx.validation.mixin"]
        mock_results = [
            {"level": "error", "message": "Critical error", "field": "field1"},
            {"level": "warning", "message": "Minor warning", "field": "field2"},
        ]
        with patch.object(self.MixinModel, "validate_all", return_value=mock_results):
            html = Mixin.get_validation_summary_html()
        html_str = str(html)
        self.assertIn("alert-danger", html_str)
        self.assertIn("alert-warning", html_str)
        self.assertIn("Critical error", html_str)
        self.assertIn("Minor warning", html_str)

    def test_06_is_valid_with_no_errors(self):
        """Test is_valid returns True when no errors."""
        Mixin = self.env["praetorx.validation.mixin"]
        with patch.object(self.MixinModel, "validate_all", return_value=[]):
            self.assertTrue(Mixin.is_valid())

    def test_07_is_valid_with_errors(self):
        """Test is_valid returns False when errors exist."""
        Mixin = self.env["praetorx.validation.mixin"]
        mock_results = [{"level": "error", "message": "Error occurred"}]
        with patch.object(self.MixinModel, "validate_all", return_value=mock_results):
            self.assertFalse(Mixin.is_valid())

    def test_08_is_valid_with_only_warnings(self):
        """Test is_valid returns True when only warnings (no errors)."""
        Mixin = self.env["praetorx.validation.mixin"]
        mock_results = [{"level": "warning", "message": "Warning message"}]
        with patch.object(self.MixinModel, "validate_all", return_value=mock_results):
            self.assertTrue(Mixin.is_valid())

    def test_09_has_warnings_true(self):
        """Test has_warnings returns True when warnings exist."""
        Mixin = self.env["praetorx.validation.mixin"]
        mock_results = [{"level": "warning", "message": "Warning"}]
        with patch.object(self.MixinModel, "validate_all", return_value=mock_results):
            self.assertTrue(Mixin.has_warnings())

    def test_10_has_warnings_false(self):
        """Test has_warnings returns False when no warnings."""
        Mixin = self.env["praetorx.validation.mixin"]
        with patch.object(self.MixinModel, "validate_all", return_value=[]):
            self.assertFalse(Mixin.has_warnings())

    def test_11_get_validation_errors(self):
        """Test get_validation_errors returns only error messages."""
        Mixin = self.env["praetorx.validation.mixin"]
        mock_results = [
            {"level": "error", "message": "Error 1"},
            {"level": "warning", "message": "Warning 1"},
            {"level": "error", "message": "Error 2"},
        ]
        with patch.object(self.MixinModel, "validate_all", return_value=mock_results):
            errors = Mixin.get_validation_errors()
        self.assertEqual(len(errors), 2)
        self.assertIn("Error 1", errors)
        self.assertIn("Error 2", errors)
        self.assertNotIn("Warning 1", errors)

    def test_12_get_validation_warnings(self):
        """Test get_validation_warnings returns only warning messages."""
        Mixin = self.env["praetorx.validation.mixin"]
        mock_results = [
            {"level": "error", "message": "Error 1"},
            {"level": "warning", "message": "Warning 1"},
            {"level": "warning", "message": "Warning 2"},
        ]
        with patch.object(self.MixinModel, "validate_all", return_value=mock_results):
            warnings = Mixin.get_validation_warnings()
        self.assertEqual(len(warnings), 2)
        self.assertIn("Warning 1", warnings)
        self.assertIn("Warning 2", warnings)
        self.assertNotIn("Error 1", warnings)

    def test_13_assert_valid_passes(self):
        """Test assert_valid does not raise when valid."""
        Mixin = self.env["praetorx.validation.mixin"]
        with patch.object(self.MixinModel, "validate_all", return_value=[]):
            try:
                Mixin.assert_valid()
            except UserError:
                self.fail("assert_valid raised UserError on valid record")

    def test_14_assert_valid_raises_on_errors(self):
        """Test assert_valid raises UserError on errors."""
        Mixin = self.env["praetorx.validation.mixin"]
        mock_results = [
            {"level": "error", "message": "Error 1"},
            {"level": "error", "message": "Error 2"},
        ]
        with patch.object(self.MixinModel, "validate_all", return_value=mock_results):
            with self.assertRaises(UserError) as ctx:
                Mixin.assert_valid()
        error_msg = str(ctx.exception)
        self.assertIn("Validation failed", error_msg)
        self.assertIn("Error 1", error_msg)
        self.assertIn("Error 2", error_msg)

    def test_15_assert_valid_with_warnings_only(self):
        """Test assert_valid does not raise on warnings only."""
        Mixin = self.env["praetorx.validation.mixin"]
        mock_results = [{"level": "warning", "message": "Warning"}]
        with patch.object(self.MixinModel, "validate_all", return_value=mock_results):
            try:
                Mixin.assert_valid()
            except UserError:
                self.fail("assert_valid raised UserError on warnings only")

    def test_16_validation_summary_for_records_empty(self):
        """Test get_validation_summary_for_records with empty recordset."""
        Mixin = self.env["praetorx.validation.mixin"]
        empty_recordset = Mixin.browse([])
        html = Mixin.get_validation_summary_for_records(empty_recordset)
        self.assertIsInstance(html, Markup)
        self.assertIn("alert-info", str(html))
        self.assertIn("No records to validate", str(html))

    def test_17_validation_summary_for_records_all_valid(self):
        """Test get_validation_summary_for_records with all valid records."""
        Mixin = self.env["praetorx.validation.mixin"]
        partners = self.Partner.browse([self.valid_partner.id])
        PartnerModel = type(self.valid_partner)
        with patch.object(PartnerModel, "validate_all", create=True, return_value=[]):
            html = Mixin.get_validation_summary_for_records(partners)
        html_str = str(html)
        self.assertIn("alert-success", html_str)
        self.assertIn("passed validation", html_str)

    def test_18_validation_summary_for_records_with_errors(self):
        """Test get_validation_summary_for_records with errors."""
        Mixin = self.env["praetorx.validation.mixin"]
        partners = self.Partner.browse([self.valid_partner.id])
        mock_results = [{"level": "error", "message": "Test error"}]
        PartnerModel = type(self.valid_partner)
        with patch.object(PartnerModel, "validate_all", create=True, return_value=mock_results):
            html = Mixin.get_validation_summary_for_records(partners)
        html_str = str(html)
        self.assertIn("alert-danger", html_str)
        self.assertIn("Test error", html_str)
        self.assertIn(self.valid_partner.display_name, html_str)

    def test_19_validation_result_without_field(self):
        """Test validation result without field name."""
        Mixin = self.env["praetorx.validation.mixin"]
        mock_results = [{"level": "error", "message": "Error without field"}]
        with patch.object(self.MixinModel, "validate_all", return_value=mock_results):
            html = Mixin.get_validation_summary_html()
        html_str = str(html)
        self.assertIn("Error without field", html_str)
        self.assertNotIn("()", html_str)

    def test_20_validation_result_with_field(self):
        """Test validation result with field name."""
        Mixin = self.env["praetorx.validation.mixin"]
        mock_results = [
            {"level": "error", "message": "Error with field", "field": "email"}
        ]
        with patch.object(self.MixinModel, "validate_all", return_value=mock_results):
            html = Mixin.get_validation_summary_html()
        html_str = str(html)
        self.assertIn("Error with field", html_str)
        self.assertIn("(email)", html_str)
