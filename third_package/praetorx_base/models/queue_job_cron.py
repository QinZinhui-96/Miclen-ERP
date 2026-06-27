# Copyright 2025 Lars Weiler
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

import json
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class QueueJobCron(models.Model):
    """Queue Job for Background Processing.

    This model provides a pattern for queuing background jobs that process
    records in batches via cron jobs. Useful for operations that should not
    block the UI or need to be processed asynchronously.

    Example usage:
        self.env['praetorx.queue.job'].create({
            'name': 'Process Invoices',
            'model_name': 'account.move',
            'method_name': '_compute_taxes',
            'record_ids': json.dumps([1, 2, 3, 4, 5])
        })
    """

    _name = "praetorx.queue.job"
    _description = "Queue Job for Background Processing"
    _order = "create_date desc"
    _rec_name = "name"

    name = fields.Char(string="Job Name", required=True, help="Descriptive name for this job")
    model_name = fields.Char(string="Model", required=True, help="Technical name of the model (e.g., 'account.move')")
    method_name = fields.Char(string="Method", required=True, help="Name of the method to call on the records")
    record_ids = fields.Text(string="Record IDs", help="JSON list of record IDs to process")
    state = fields.Selection(
        selection=[("pending", "Pending"), ("processing", "Processing"), ("done", "Done"), ("failed", "Failed")],
        default="pending",
        required=True,
        help="Current state of the job",
    )
    error_message = fields.Text(string="Error Message", help="Error details if job failed")
    started_at = fields.Datetime(string="Started At", readonly=True, help="When the job started processing")
    finished_at = fields.Datetime(
        string="Finished At", readonly=True, help="When the job finished (successfully or with error)"
    )
    create_uid = fields.Many2one("res.users", string="Created By", readonly=True)
    create_date = fields.Datetime(string="Created On", readonly=True)

    @api.model
    def _cron_process_jobs(self, batch_size=100):
        """Process pending jobs in batches.

        This method is called by the cron job. It processes jobs in FIFO order
        (oldest first) to ensure fairness.

        Args:
            batch_size: Maximum number of jobs to process in one run
        """
        jobs = self.search([("state", "=", "pending")], limit=batch_size, order="create_date asc")

        if not jobs:
            _logger.debug("No pending queue jobs to process")
            return

        _logger.info(f"Processing {len(jobs)} queue job(s)")

        for job in jobs:
            try:
                job._process_job()
            except Exception as e:
                # Catch-all to prevent one failing job from stopping the batch
                _logger.exception(f"Unexpected error processing job {job.id}: {e}")
                job.write(
                    {
                        "state": "failed",
                        "error_message": f"Unexpected error: {str(e)}",
                        "finished_at": fields.Datetime.now(),
                    }
                )

    def _process_job(self):
        """Process a single job.

        This method:
        1. Validates the job configuration
        2. Loads the model and records
        3. Calls the specified method
        4. Updates the job state
        """
        self.ensure_one()

        if self.state != "pending":
            _logger.warning(f"Job {self.id} is not pending (state={self.state}), skipping")
            return

        self.write({"state": "processing", "started_at": fields.Datetime.now()})

        try:
            # Validate model exists
            if self.model_name not in self.env:
                raise UserError(f"Model '{self.model_name}' does not exist")

            Model = self.env[self.model_name]

            # Parse and validate record IDs
            try:
                ids = json.loads(self.record_ids or "[]")
            except json.JSONDecodeError as e:
                raise UserError(f"Invalid JSON in record_ids: {e}")

            if not ids:
                _logger.warning(f"Job {self.id} has no record IDs, marking as done")
                self.write({"state": "done", "finished_at": fields.Datetime.now()})
                return

            # Load records
            records = Model.browse(ids)
            existing_records = records.exists()

            if len(existing_records) != len(ids):
                missing = set(ids) - set(existing_records.ids)
                _logger.warning(f"Job {self.id}: {len(missing)} record(s) no longer exist: {missing}")

            if not existing_records:
                _logger.warning(f"Job {self.id}: No valid records found, marking as done")
                self.write({"state": "done", "finished_at": fields.Datetime.now()})
                return

            # Validate method exists
            if not hasattr(existing_records, self.method_name):
                raise UserError(f"Method '{self.method_name}' does not exist on model '{self.model_name}'")

            # Call the method
            _logger.info(
                f"Job {self.id}: Calling {self.model_name}.{self.method_name}() on {len(existing_records)} record(s)"
            )

            method = getattr(existing_records, self.method_name)
            result = method()

            _logger.info(f"Job {self.id}: Completed successfully")

            self.write({"state": "done", "finished_at": fields.Datetime.now()})

            return result

        except Exception as e:
            _logger.exception(f"Job {self.id} failed: {e}")
            self.write({"state": "failed", "error_message": str(e), "finished_at": fields.Datetime.now()})

    def action_retry(self):
        """Reset failed jobs to pending state for retry."""
        failed_jobs = self.filtered(lambda j: j.state == "failed")
        if not failed_jobs:
            raise UserError("No failed jobs selected")

        failed_jobs.write({"state": "pending", "error_message": False, "started_at": False, "finished_at": False})

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Jobs Reset",
                "message": f"{len(failed_jobs)} job(s) reset to pending",
                "type": "success",
                "sticky": False,
            },
        }

    def action_cancel(self):
        """Cancel pending or processing jobs."""
        active_jobs = self.filtered(lambda j: j.state in ("pending", "processing"))
        if not active_jobs:
            raise UserError("No active jobs selected")

        active_jobs.write(
            {"state": "failed", "error_message": "Cancelled by user", "finished_at": fields.Datetime.now()}
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Jobs Cancelled",
                "message": f"{len(active_jobs)} job(s) cancelled",
                "type": "warning",
                "sticky": False,
            },
        }
