# Copyright 2025 Lars Weiler
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

import json

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install", "praetorx")
class TestQueueJob(TransactionCase):
    """Test queue job background processing functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.QueueJob = cls.env["praetorx.queue.job"]
        cls.Partner = cls.env["res.partner"]

        # Create test partners for job processing
        cls.test_partners = cls.Partner.create(
            [{"name": f"Test Partner {i}", "email": f"test{i}@example.com"} for i in range(5)]
        )

    def test_01_create_job(self):
        """Test job creation with required fields."""
        job = self.QueueJob.create(
            {
                "name": "Test Job",
                "model_name": "res.partner",
                "method_name": "write",
                "record_ids": json.dumps([1, 2, 3]),
            }
        )

        self.assertEqual(job.state, "pending")
        self.assertFalse(job.started_at)
        self.assertFalse(job.finished_at)
        self.assertFalse(job.error_message)
        self.assertEqual(job.name, "Test Job")
        self.assertEqual(job.model_name, "res.partner")
        self.assertEqual(job.method_name, "write")

    def test_02_process_job_success(self):
        """Test successful job processing."""
        job = self.QueueJob.create(
            {
                "name": "Test Success",
                "model_name": "res.partner",
                "method_name": "exists",
                "record_ids": json.dumps(self.test_partners.ids),
            }
        )

        self.assertEqual(job.state, "pending")

        job._process_job()

        self.assertEqual(job.state, "done")
        self.assertTrue(job.started_at)
        self.assertTrue(job.finished_at)
        self.assertFalse(job.error_message)
        self.assertLessEqual(job.started_at, job.finished_at)

    def test_03_process_job_failure_invalid_model(self):
        """Test job failure with invalid model."""
        job = self.QueueJob.create(
            {
                "name": "Test Invalid Model",
                "model_name": "nonexistent.model",
                "method_name": "exists",
                "record_ids": json.dumps([1]),
            }
        )

        job._process_job()

        self.assertEqual(job.state, "failed")
        self.assertIn("does not exist", job.error_message)
        self.assertTrue(job.finished_at)

    def test_04_process_job_failure_invalid_method(self):
        """Test job failure with invalid method."""
        job = self.QueueJob.create(
            {
                "name": "Test Invalid Method",
                "model_name": "res.partner",
                "method_name": "nonexistent_method_xyz",
                "record_ids": json.dumps(self.test_partners.ids),
            }
        )

        job._process_job()

        self.assertEqual(job.state, "failed")
        self.assertIn("does not exist", job.error_message)

    def test_05_process_job_empty_record_ids(self):
        """Test job with empty record IDs is marked as done."""
        job = self.QueueJob.create(
            {
                "name": "Test Empty Records",
                "model_name": "res.partner",
                "method_name": "exists",
                "record_ids": json.dumps([]),
            }
        )

        job._process_job()

        self.assertEqual(job.state, "done")
        self.assertTrue(job.finished_at)

    def test_06_process_job_invalid_json(self):
        """Test job with invalid JSON in record_ids."""
        job = self.QueueJob.create(
            {
                "name": "Test Invalid JSON",
                "model_name": "res.partner",
                "method_name": "exists",
                "record_ids": "not-valid-json[",
            }
        )

        job._process_job()

        self.assertEqual(job.state, "failed")
        self.assertIn("Invalid JSON", job.error_message)

    def test_07_process_job_nonexistent_records(self):
        """Test job with nonexistent record IDs."""
        job = self.QueueJob.create(
            {
                "name": "Test Nonexistent Records",
                "model_name": "res.partner",
                "method_name": "exists",
                "record_ids": json.dumps([99999, 99998, 99997]),
            }
        )

        job._process_job()

        # Should complete successfully, just log warnings about missing records
        self.assertEqual(job.state, "done")

    def test_08_process_job_mixed_existing_and_missing_records(self):
        """Test job with mix of existing and missing records."""
        mixed_ids = self.test_partners.ids[:2] + [99999, 99998]

        job = self.QueueJob.create(
            {
                "name": "Test Mixed Records",
                "model_name": "res.partner",
                "method_name": "exists",
                "record_ids": json.dumps(mixed_ids),
            }
        )

        job._process_job()

        # Should process existing records successfully
        self.assertEqual(job.state, "done")

    def test_09_cron_batch_processing(self):
        """Test cron processes multiple jobs in batch."""
        # Create multiple pending jobs
        jobs = []
        for i in range(5):
            job = self.QueueJob.create(
                {
                    "name": f"Batch Job {i}",
                    "model_name": "res.partner",
                    "method_name": "exists",
                    "record_ids": json.dumps(self.test_partners.ids),
                }
            )
            jobs.append(job)

        # Process with batch_size=3
        self.QueueJob._cron_process_jobs(batch_size=3)

        done_jobs = self.QueueJob.search([("id", "in", [j.id for j in jobs]), ("state", "=", "done")])
        self.assertEqual(len(done_jobs), 3)

        pending_jobs = self.QueueJob.search([("id", "in", [j.id for j in jobs]), ("state", "=", "pending")])
        self.assertEqual(len(pending_jobs), 2)

    def test_10_cron_fifo_order(self):
        """Test cron processes jobs in FIFO order (oldest first)."""
        # Create jobs with slight delays to ensure order
        job1 = self.QueueJob.create(
            {
                "name": "First Job",
                "model_name": "res.partner",
                "method_name": "exists",
                "record_ids": json.dumps([]),
            }
        )

        job2 = self.QueueJob.create(
            {
                "name": "Second Job",
                "model_name": "res.partner",
                "method_name": "exists",
                "record_ids": json.dumps([]),
            }
        )

        job3 = self.QueueJob.create(
            {
                "name": "Third Job",
                "model_name": "res.partner",
                "method_name": "exists",
                "record_ids": json.dumps([]),
            }
        )

        # Process one job
        self.QueueJob._cron_process_jobs(batch_size=1)

        # First job should be processed
        job1.invalidate_recordset()
        self.assertEqual(job1.state, "done")
        self.assertEqual(job2.state, "pending")
        self.assertEqual(job3.state, "pending")

    def test_11_skip_non_pending_jobs(self):
        """Test _process_job skips non-pending jobs."""
        job = self.QueueJob.create(
            {
                "name": "Test Skip",
                "model_name": "res.partner",
                "method_name": "exists",
                "record_ids": json.dumps([]),
            }
        )

        # Manually set to 'done'
        job.write({"state": "done"})

        # Try to process - should skip
        job._process_job()

        # Should remain done, no started_at timestamp
        self.assertEqual(job.state, "done")
        self.assertFalse(job.started_at)

    def test_12_action_retry(self):
        """Test action_retry resets failed jobs to pending."""
        job = self.QueueJob.create(
            {
                "name": "Test Retry",
                "model_name": "nonexistent.model",
                "method_name": "exists",
                "record_ids": json.dumps([]),
            }
        )

        # Process to fail it
        job._process_job()

        self.assertEqual(job.state, "failed")
        self.assertTrue(job.error_message)
        self.assertTrue(job.finished_at)

        # Retry
        result = job.action_retry()

        self.assertEqual(job.state, "pending")
        self.assertFalse(job.error_message)
        self.assertFalse(job.started_at)
        self.assertFalse(job.finished_at)

        # Check notification returned
        self.assertEqual(result["type"], "ir.actions.client")
        self.assertIn("success", result["params"]["type"])

    def test_13_action_retry_only_failed_jobs(self):
        """Test action_retry only works on failed jobs."""
        job = self.QueueJob.create(
            {
                "name": "Test Retry Pending",
                "model_name": "res.partner",
                "method_name": "exists",
                "record_ids": json.dumps([]),
            }
        )

        # Try to retry a pending job
        with self.assertRaises(UserError) as ctx:
            job.action_retry()

        self.assertIn("No failed jobs", str(ctx.exception))

    def test_14_action_cancel(self):
        """Test action_cancel cancels active jobs."""
        job = self.QueueJob.create(
            {
                "name": "Test Cancel",
                "model_name": "res.partner",
                "method_name": "exists",
                "record_ids": json.dumps([]),
            }
        )

        self.assertEqual(job.state, "pending")

        result = job.action_cancel()

        self.assertEqual(job.state, "failed")
        self.assertEqual(job.error_message, "Cancelled by user")
        self.assertTrue(job.finished_at)

        # Check notification returned
        self.assertEqual(result["type"], "ir.actions.client")
        self.assertIn("warning", result["params"]["type"])

    def test_15_action_cancel_only_active_jobs(self):
        """Test action_cancel only works on active jobs."""
        job = self.QueueJob.create(
            {
                "name": "Test Cancel Done",
                "model_name": "res.partner",
                "method_name": "exists",
                "record_ids": json.dumps([]),
            }
        )

        # Process it
        job._process_job()
        self.assertEqual(job.state, "done")

        # Try to cancel a done job
        with self.assertRaises(UserError) as ctx:
            job.action_cancel()

        self.assertIn("No active jobs", str(ctx.exception))

    def test_16_cron_handles_unexpected_errors(self):
        """Test cron handles unexpected errors gracefully."""
        # Create a job that will fail unexpectedly
        job = self.QueueJob.create(
            {
                "name": "Test Unexpected Error",
                "model_name": "res.partner",
                "method_name": "invalid",
                "record_ids": json.dumps([1]),
            }
        )

        # Cron should not raise, just mark job as failed
        self.QueueJob._cron_process_jobs()

        job.invalidate_recordset()
        self.assertEqual(job.state, "failed")
        self.assertTrue(job.error_message)

    def test_17_timestamps_accuracy(self):
        """Test started_at and finished_at timestamps are accurate."""
        job = self.QueueJob.create(
            {
                "name": "Timestamp Test",
                "model_name": "res.partner",
                "method_name": "exists",
                "record_ids": json.dumps(self.test_partners.ids),
            }
        )

        self.assertFalse(job.started_at)
        self.assertFalse(job.finished_at)

        job._process_job()

        self.assertTrue(job.started_at)
        self.assertTrue(job.finished_at)
        self.assertLessEqual(job.started_at, job.finished_at)

        # Check timestamps are recent (within last minute)
        from odoo import fields

        now = fields.Datetime.now()
        from datetime import timedelta

        self.assertGreater(job.started_at, now - timedelta(minutes=1))
        self.assertGreater(job.finished_at, now - timedelta(minutes=1))

    def test_18_cron_with_no_pending_jobs(self):
        """Test cron handles empty queue gracefully."""
        # Clear all pending jobs
        pending = self.QueueJob.search([("state", "=", "pending")])
        pending.write({"state": "done"})

        # Should not raise
        self.QueueJob._cron_process_jobs()

    def test_19_job_with_method_returning_value(self):
        """Test job processes methods that return values."""
        job = self.QueueJob.create(
            {
                "name": "Test Return Value",
                "model_name": "res.partner",
                "method_name": "read",
                "record_ids": json.dumps(self.test_partners.ids[:2]),
            }
        )

        result = job._process_job()

        self.assertEqual(job.state, "done")
        self.assertIsInstance(result, list)

    def test_20_multiple_jobs_batch_retry(self):
        """Test action_retry works on multiple failed jobs."""
        jobs = []
        for i in range(3):
            job = self.QueueJob.create(
                {
                    "name": f"Test Batch Retry {i}",
                    "model_name": "nonexistent.model",
                    "method_name": "exists",
                    "record_ids": json.dumps([]),
                }
            )
            jobs.append(job)

        # Fail all jobs
        for job in jobs:
            job._process_job()

        # Retry all at once
        jobs_recordset = self.QueueJob.browse([j.id for j in jobs])
        result = jobs_recordset.action_retry()

        for job in jobs:
            job.invalidate_recordset()
            self.assertEqual(job.state, "pending")

        self.assertIn("3 job(s)", result["params"]["message"])
