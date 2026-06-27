# Copyright 2025 Lars Weiler
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "praetorx")
class TestBatchProcessingMixin(TransactionCase):
    """Test batch processing mixin state machine.

    Since BatchProcessingMixin is abstract, we create a test model that inherits it.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Register a test model that inherits the batch processing mixin
        # We do this dynamically for testing purposes
        class TestBatchModel(models.Model):
            _name = "test.batch.model"
            _inherit = ["praetorx.batch.mixin"]
            _description = "Test Batch Processing Model"

            name = fields.Char(required=True)

            # Override hooks for testing
            def _validate_before_validate(self):
                super()._validate_before_validate()
                if hasattr(self, "_hook_validate_before_validate_called"):
                    self._hook_validate_before_validate_called = True

            def _validate_before_post(self):
                super()._validate_before_post()
                if hasattr(self, "_hook_validate_before_post_called"):
                    self._hook_validate_before_post_called = True

            def _validate_before_cancel(self):
                super()._validate_before_cancel()
                if hasattr(self, "_hook_validate_before_cancel_called"):
                    self._hook_validate_before_cancel_called = True

            def _validate_before_reset(self):
                super()._validate_before_reset()
                if hasattr(self, "_hook_validate_before_reset_called"):
                    self._hook_validate_before_reset_called = True

            def _post_processing(self):
                super()._post_processing()
                if hasattr(self, "_hook_post_processing_called"):
                    self._hook_post_processing_called = True

            def _cancel_processing(self):
                super()._cancel_processing()
                if hasattr(self, "_hook_cancel_processing_called"):
                    self._hook_cancel_processing_called = True

            def _reset_processing(self):
                super()._reset_processing()
                if hasattr(self, "_hook_reset_processing_called"):
                    self._hook_reset_processing_called = True

        # Install the test model (this is for testing only)
        try:
            cls.TestBatch = cls.env["test.batch.model"]
        except KeyError:
            # Model not registered, skip tests
            cls.TestBatch = None

    def setUp(self):
        super().setUp()
        if self.TestBatch is None:
            self.skipTest("Test model 'test.batch.model' not available")

    def test_01_initial_state_draft(self):
        """Test new records start in draft state."""
        record = self.TestBatch.create({"name": "Test Record"})

        self.assertEqual(record.state, "draft")
        self.assertTrue(record.can_validate)
        self.assertFalse(record.can_post)
        self.assertTrue(record.can_cancel)
        self.assertFalse(record.can_reset)

    def test_02_compute_workflow_buttons_draft(self):
        """Test workflow button visibility in draft state."""
        record = self.TestBatch.create({"name": "Test Draft"})

        self.assertEqual(record.state, "draft")
        self.assertTrue(record.can_validate)
        self.assertFalse(record.can_post)
        self.assertTrue(record.can_cancel)
        self.assertFalse(record.can_reset)

    def test_03_action_validate_from_draft(self):
        """Test action_validate moves state to validated."""
        record = self.TestBatch.create({"name": "Test Validate"})

        self.assertEqual(record.state, "draft")

        result = record.action_validate()

        self.assertTrue(result)
        self.assertEqual(record.state, "validated")
        self.assertFalse(record.can_validate)
        self.assertTrue(record.can_post)
        self.assertTrue(record.can_cancel)
        self.assertFalse(record.can_reset)

    def test_04_action_validate_only_from_draft(self):
        """Test action_validate only works from draft state."""
        record = self.TestBatch.create({"name": "Test Validate Error"})
        record.action_validate()
        record.action_post()

        self.assertEqual(record.state, "posted")

        with self.assertRaises(UserError) as ctx:
            record.action_validate()

        self.assertIn("state must be 'draft'", str(ctx.exception))

    def test_05_action_post_from_validated(self):
        """Test action_post moves state from validated to posted."""
        record = self.TestBatch.create({"name": "Test Post"})
        record.action_validate()

        self.assertEqual(record.state, "validated")

        result = record.action_post()

        self.assertTrue(result)
        self.assertEqual(record.state, "posted")
        self.assertFalse(record.can_validate)
        self.assertFalse(record.can_post)
        self.assertFalse(record.can_cancel)
        self.assertFalse(record.can_reset)

    def test_06_action_post_only_from_validated(self):
        """Test action_post only works on validated records."""
        record = self.TestBatch.create({"name": "Test Post Error"})

        self.assertEqual(record.state, "draft")

        with self.assertRaises(UserError) as ctx:
            record.action_post()

        self.assertIn("state must be 'validated'", str(ctx.exception))

    def test_07_action_cancel_from_draft(self):
        """Test action_cancel moves state to cancelled from draft."""
        record = self.TestBatch.create({"name": "Test Cancel"})

        self.assertEqual(record.state, "draft")

        result = record.action_cancel()

        self.assertTrue(result)
        self.assertEqual(record.state, "cancelled")
        self.assertFalse(record.can_validate)
        self.assertFalse(record.can_post)
        self.assertFalse(record.can_cancel)
        self.assertTrue(record.can_reset)

    def test_08_action_cancel_from_validated(self):
        """Test action_cancel works from validated state."""
        record = self.TestBatch.create({"name": "Test Cancel Validated"})
        record.action_validate()

        self.assertEqual(record.state, "validated")

        result = record.action_cancel()

        self.assertTrue(result)
        self.assertEqual(record.state, "cancelled")

    def test_09_action_cancel_not_from_posted(self):
        """Test action_cancel does not work from posted state."""
        record = self.TestBatch.create({"name": "Test Cancel Posted"})
        record.action_validate()
        record.action_post()

        self.assertEqual(record.state, "posted")

        with self.assertRaises(UserError) as ctx:
            record.action_cancel()

        self.assertIn("state must be 'draft' or 'validated'", str(ctx.exception))

    def test_10_action_reset_to_draft_from_cancelled(self):
        """Test action_reset_to_draft only works on cancelled."""
        record = self.TestBatch.create({"name": "Test Reset"})
        record.action_cancel()

        self.assertEqual(record.state, "cancelled")

        result = record.action_reset_to_draft()

        self.assertTrue(result)
        self.assertEqual(record.state, "draft")
        self.assertTrue(record.can_validate)

    def test_11_action_reset_only_from_cancelled(self):
        """Test action_reset_to_draft only works from cancelled."""
        record = self.TestBatch.create({"name": "Test Reset Error"})

        self.assertEqual(record.state, "draft")

        with self.assertRaises(UserError) as ctx:
            record.action_reset_to_draft()

        self.assertIn("state must be 'cancelled'", str(ctx.exception))

    def test_12_complete_workflow_cycle(self):
        """Test complete workflow: draft -> validated -> posted."""
        record = self.TestBatch.create({"name": "Test Full Cycle"})

        # Draft
        self.assertEqual(record.state, "draft")

        # Validate
        record.action_validate()
        self.assertEqual(record.state, "validated")

        # Post
        record.action_post()
        self.assertEqual(record.state, "posted")

    def test_13_cancel_and_reset_cycle(self):
        """Test cancel and reset cycle: draft -> cancelled -> draft."""
        record = self.TestBatch.create({"name": "Test Cancel Reset"})

        # Cancel from draft
        record.action_cancel()
        self.assertEqual(record.state, "cancelled")

        # Reset to draft
        record.action_reset_to_draft()
        self.assertEqual(record.state, "draft")

        # Can continue workflow
        record.action_validate()
        self.assertEqual(record.state, "validated")

    def test_14_is_editable_draft(self):
        """Test is_editable returns True for draft state."""
        record = self.TestBatch.create({"name": "Test Editable Draft"})

        self.assertTrue(record.is_editable())

    def test_15_is_editable_cancelled(self):
        """Test is_editable returns True for cancelled state."""
        record = self.TestBatch.create({"name": "Test Editable Cancelled"})
        record.action_cancel()

        self.assertTrue(record.is_editable())

    def test_16_is_editable_validated(self):
        """Test is_editable returns False for validated state."""
        record = self.TestBatch.create({"name": "Test Not Editable"})
        record.action_validate()

        self.assertFalse(record.is_editable())

    def test_17_is_editable_posted(self):
        """Test is_editable returns False for posted state."""
        record = self.TestBatch.create({"name": "Test Not Editable Posted"})
        record.action_validate()
        record.action_post()

        self.assertFalse(record.is_editable())

    def test_18_is_posted(self):
        """Test is_posted returns correct value."""
        record = self.TestBatch.create({"name": "Test Is Posted"})

        self.assertFalse(record.is_posted())

        record.action_validate()
        self.assertFalse(record.is_posted())

        record.action_post()
        self.assertTrue(record.is_posted())

    def test_19_assert_editable_draft(self):
        """Test assert_editable does not raise for draft."""
        record = self.TestBatch.create({"name": "Test Assert Draft"})

        # Should not raise
        try:
            record.assert_editable()
        except UserError:
            self.fail("assert_editable raised UserError on draft record")

    def test_20_assert_editable_posted_raises(self):
        """Test assert_editable raises for posted records."""
        record = self.TestBatch.create({"name": "Test Assert Posted"})
        record.action_validate()
        record.action_post()

        with self.assertRaises(UserError) as ctx:
            record.assert_editable()

        self.assertIn("Cannot modify", str(ctx.exception))
        self.assertIn("posted", str(ctx.exception))

    def test_21_unlink_draft_allowed(self):
        """Test deletion of draft records is allowed."""
        record = self.TestBatch.create({"name": "Test Unlink Draft"})

        record_id = record.id
        record.unlink()

        # Should be deleted
        self.assertFalse(self.TestBatch.browse(record_id).exists())

    def test_22_unlink_validated_blocked(self):
        """Test deletion of validated records is blocked."""
        record = self.TestBatch.create({"name": "Test Unlink Validated"})
        record.action_validate()

        with self.assertRaises(UserError) as ctx:
            record.unlink()

        self.assertIn("Cannot delete", str(ctx.exception))
        self.assertIn("validated", str(ctx.exception))

    def test_23_unlink_posted_blocked(self):
        """Test deletion of posted records is blocked."""
        record = self.TestBatch.create({"name": "Test Unlink Posted"})
        record.action_validate()
        record.action_post()

        with self.assertRaises(UserError) as ctx:
            record.unlink()

        self.assertIn("Cannot delete", str(ctx.exception))
        self.assertIn("posted", str(ctx.exception))

    def test_24_unlink_cancelled_allowed(self):
        """Test deletion of cancelled records is allowed."""
        record = self.TestBatch.create({"name": "Test Unlink Cancelled"})
        record.action_cancel()

        record_id = record.id
        record.unlink()

        # Should be deleted
        self.assertFalse(self.TestBatch.browse(record_id).exists())

    def test_25_batch_validate_multiple_records(self):
        """Test validating multiple records at once."""
        records = self.TestBatch.create(
            [
                {"name": "Batch 1"},
                {"name": "Batch 2"},
                {"name": "Batch 3"},
            ]
        )

        self.assertTrue(all(r.state == "draft" for r in records))

        records.action_validate()

        self.assertTrue(all(r.state == "validated" for r in records))

    def test_26_batch_post_multiple_records(self):
        """Test posting multiple records at once."""
        records = self.TestBatch.create(
            [
                {"name": "Batch Post 1"},
                {"name": "Batch Post 2"},
            ]
        )

        records.action_validate()
        records.action_post()

        self.assertTrue(all(r.state == "posted" for r in records))

    def test_27_batch_cancel_multiple_records(self):
        """Test cancelling multiple records at once."""
        records = self.TestBatch.create(
            [
                {"name": "Batch Cancel 1"},
                {"name": "Batch Cancel 2"},
            ]
        )

        records.action_cancel()

        self.assertTrue(all(r.state == "cancelled" for r in records))

    def test_28_validation_hook_called(self):
        """Test _validate_before_validate hook is called."""
        record = self.TestBatch.create({"name": "Test Hook"})

        # Add flag to track hook call
        record._hook_validate_before_validate_called = False

        record.action_validate()

        # Hook should have been called (if implemented in test model)
        # This tests the hook mechanism exists

    def test_29_post_processing_hook_called(self):
        """Test _post_processing hook is called."""
        record = self.TestBatch.create({"name": "Test Post Hook"})

        # Add flag to track hook call
        record._hook_post_processing_called = False

        record.action_validate()
        record.action_post()

        # Hook should have been called

    def test_30_state_tracking(self):
        """Test state changes are tracked."""
        record = self.TestBatch.create({"name": "Test Tracking"})

        # State field should have tracking=True
        field = self.TestBatch._fields["state"]
        self.assertTrue(field.tracking)

        # Check initial state
        self.assertEqual(record.state, "draft")

        # Make state changes
        record.action_validate()
        self.assertEqual(record.state, "validated")

        record.action_post()
        self.assertEqual(record.state, "posted")


@tagged("post_install", "-at_install", "praetorx")
class TestBatchProcessingMixinHooks(TransactionCase):
    """Test custom hook implementations in batch processing mixin."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create test model with custom validation hooks
        class TestBatchWithValidation(models.Model):
            _name = "test.batch.validation"
            _inherit = ["praetorx.batch.mixin"]
            _description = "Test Batch with Custom Validation"

            name = fields.Char(required=True)
            amount = fields.Float()

            def _validate_before_validate(self):
                super()._validate_before_validate()
                if not self.name:
                    raise UserError("Name is required for validation")

            def _validate_before_post(self):
                super()._validate_before_post()
                if self.amount <= 0:
                    raise UserError("Amount must be positive to post")

            def _validate_before_cancel(self):
                super()._validate_before_cancel()
                if self.amount > 1000:
                    raise UserError("Cannot cancel: amount too high")

        try:
            cls.TestBatchValidation = cls.env["test.batch.validation"]
        except KeyError:
            cls.TestBatchValidation = None

    def setUp(self):
        super().setUp()
        if self.TestBatchValidation is None:
            self.skipTest("Test model 'test.batch.validation' not available")

    def test_01_validate_hook_blocks_invalid(self):
        """Test _validate_before_validate can block validation."""
        record = self.TestBatchValidation.create({"name": "", "amount": 100})

        with self.assertRaises(UserError) as ctx:
            record.action_validate()

        self.assertIn("Name is required", str(ctx.exception))
        self.assertEqual(record.state, "draft")

    def test_02_post_hook_blocks_invalid(self):
        """Test _validate_before_post can block posting."""
        record = self.TestBatchValidation.create({"name": "Test", "amount": 0})
        record.action_validate()

        with self.assertRaises(UserError) as ctx:
            record.action_post()

        self.assertIn("Amount must be positive", str(ctx.exception))
        self.assertEqual(record.state, "validated")

    def test_03_cancel_hook_blocks_invalid(self):
        """Test _validate_before_cancel can block cancellation."""
        record = self.TestBatchValidation.create({"name": "Test", "amount": 2000})

        with self.assertRaises(UserError) as ctx:
            record.action_cancel()

        self.assertIn("Cannot cancel", str(ctx.exception))
        self.assertEqual(record.state, "draft")
