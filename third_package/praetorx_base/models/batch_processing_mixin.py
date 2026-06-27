# Copyright 2025 Lars Weiler
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import api, fields, models
from odoo.exceptions import UserError


class BatchProcessingMixin(models.AbstractModel):
    """Batch Processing Mixin for Parent-Child Patterns.

    This abstract model provides a reusable state machine pattern for
    batch/header documents with line items (parent-child relationship).
    Common in accounting, invoicing, settlements, etc.

    Example usage:
        class Settlement(models.Model):
            _name = 'my.settlement'
            _inherit = ['praetorx.batch.mixin']

            line_ids = fields.One2many('my.settlement.line', 'settlement_id')

            def action_post(self):
                # Call super for state transition
                super().action_post()
                # Custom posting logic
                for record in self:
                    record._create_journal_entries()

            def _validate_before_post(self):
                # Override to add specific validation
                super()._validate_before_post()
                if not self.line_ids:
                    raise UserError("Cannot post without lines")
    """

    _name = "praetorx.batch.mixin"
    _description = "Batch Processing Mixin for Parent-Child Patterns"

    state = fields.Selection(
        selection=[("draft", "Draft"), ("validated", "Validated"), ("posted", "Posted"), ("cancelled", "Cancelled")],
        default="draft",
        required=True,
        string="Status",
        help="Current state of the document in the workflow",
    )

    # Workflow action buttons visibility
    can_validate = fields.Boolean(compute="_compute_workflow_buttons", string="Can Validate")
    can_post = fields.Boolean(compute="_compute_workflow_buttons", string="Can Post")
    can_cancel = fields.Boolean(compute="_compute_workflow_buttons", string="Can Cancel")
    can_reset = fields.Boolean(compute="_compute_workflow_buttons", string="Can Reset to Draft")

    @api.depends("state")
    def _compute_workflow_buttons(self):
        """Compute which workflow buttons should be visible."""
        for record in self:
            record.can_validate = record.state == "draft"
            record.can_post = record.state == "validated"
            record.can_cancel = record.state in ("draft", "validated")
            record.can_reset = record.state == "cancelled"

    def action_validate(self):
        """Validate the batch and all children.

        This method:
        1. Runs validation checks
        2. Optionally validates child lines
        3. Transitions to 'validated' state

        Override _validate_before_validate() to add custom validation logic.
        """
        for record in self:
            if record.state != "draft":
                raise UserError(
                    f"Cannot validate {record.display_name}: state must be 'draft' (current: {record.state})"
                )

            # Run validation hooks
            record._validate_before_validate()

            # Validate child lines if they exist and have validation method
            if hasattr(record, "line_ids") and record.line_ids:
                line_model = record.line_ids._name
                if hasattr(record.env[line_model], "_validate_lines"):
                    record.line_ids._validate_lines()

            record.state = "validated"

        return True

    def action_post(self):
        """Post the batch.

        This method:
        1. Checks state is 'validated'
        2. Runs pre-post validation
        3. Transitions to 'posted' state
        4. Triggers post hooks

        Override _validate_before_post() for pre-post checks.
        Override _post_processing() for post-post actions.
        """
        for record in self:
            if record.state != "validated":
                raise UserError(
                    f"Cannot post {record.display_name}: state must be 'validated' (current: {record.state})"
                )

            # Run pre-post validation
            record._validate_before_post()

            record.state = "posted"

            # Run post-posting hooks
            record._post_processing()

        return True

    def action_cancel(self):
        """Cancel the batch.

        Batches can be cancelled from 'draft' or 'validated' states.
        Override _validate_before_cancel() to add restrictions.
        Override _cancel_processing() for cleanup actions.
        """
        for record in self:
            if record.state not in ("draft", "validated"):
                raise UserError(
                    f"Cannot cancel {record.display_name}: "
                    f"state must be 'draft' or 'validated' (current: {record.state})"
                )

            # Run pre-cancel validation
            record._validate_before_cancel()

            record.state = "cancelled"

            # Run post-cancel hooks
            record._cancel_processing()

        return True

    def action_reset_to_draft(self):
        """Reset cancelled batch to draft state.

        Only cancelled batches can be reset.
        Override _validate_before_reset() to add restrictions.
        Override _reset_processing() for cleanup actions.
        """
        for record in self:
            if record.state != "cancelled":
                raise UserError(
                    f"Cannot reset {record.display_name}: state must be 'cancelled' (current: {record.state})"
                )

            # Run pre-reset validation
            record._validate_before_reset()

            record.state = "draft"

            # Run post-reset hooks
            record._reset_processing()

        return True

    # Validation hooks - override in inheriting models

    def _validate_before_validate(self):
        """Hook: Validation before transitioning to 'validated' state.

        Override this to add custom validation logic.
        Raise UserError to prevent state transition.

        Example:
            def _validate_before_validate(self):
                super()._validate_before_validate()
                if not self.line_ids:
                    raise UserError("Cannot validate without lines")
        """
        pass

    def _validate_before_post(self):
        """Hook: Validation before transitioning to 'posted' state.

        Override this to add custom validation logic.
        Raise UserError to prevent state transition.

        Example:
            def _validate_before_post(self):
                super()._validate_before_post()
                if self.amount_total <= 0:
                    raise UserError("Cannot post with zero or negative total")
        """
        pass

    def _validate_before_cancel(self):
        """Hook: Validation before transitioning to 'cancelled' state.

        Override this to add custom validation logic.
        Raise UserError to prevent state transition.

        Example:
            def _validate_before_cancel(self):
                super()._validate_before_cancel()
                if self.has_posted_entries:
                    raise UserError("Cannot cancel: posted entries exist")
        """
        pass

    def _validate_before_reset(self):
        """Hook: Validation before resetting to 'draft' state.

        Override this to add custom validation logic.
        Raise UserError to prevent state transition.

        Example:
            def _validate_before_reset(self):
                super()._validate_before_reset()
                if self.has_linked_documents:
                    raise UserError("Cannot reset: linked documents exist")
        """
        pass

    # Processing hooks - override in inheriting models

    def _post_processing(self):
        """Hook: Actions after transitioning to 'posted' state.

        Override this to add custom post-posting logic.

        Example:
            def _post_processing(self):
                super()._post_processing()
                self._create_journal_entries()
                self._send_notification_emails()
        """
        pass

    def _cancel_processing(self):
        """Hook: Actions after transitioning to 'cancelled' state.

        Override this to add custom cancellation logic.

        Example:
            def _cancel_processing(self):
                super()._cancel_processing()
                self._reverse_journal_entries()
                self._notify_stakeholders()
        """
        pass

    def _reset_processing(self):
        """Hook: Actions after resetting to 'draft' state.

        Override this to add custom reset logic.

        Example:
            def _reset_processing(self):
                super()._reset_processing()
                self.line_ids.unlink()
                self._clear_computed_fields()
        """
        pass

    # Utility methods

    def is_editable(self):
        """Check if record is in an editable state.

        Returns:
            bool: True if state is 'draft' or 'cancelled', False otherwise
        """
        self.ensure_one()
        return self.state in ("draft", "cancelled")

    def is_posted(self):
        """Check if record is posted.

        Returns:
            bool: True if state is 'posted', False otherwise
        """
        self.ensure_one()
        return self.state == "posted"

    def assert_editable(self):
        """Raise UserError if record is not editable.

        Useful to prevent modifications in non-editable states.

        Raises:
            UserError: If state is not 'draft' or 'cancelled'
        """
        if not self.is_editable():
            raise UserError(f"Cannot modify {self.display_name}: document is {self.state}")

    @api.ondelete(at_uninstall=False)
    def _unlink_if_draft_or_cancelled(self):
        """Prevent deletion of posted or validated records.

        Override this method to customize deletion rules.
        """
        for record in self:
            if record.state in ("posted", "validated"):
                raise UserError(f"Cannot delete {record.display_name}: document is {record.state}. Cancel it first.")
