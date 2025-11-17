# -*- coding: utf-8 -*-

from odoo.tests import tagged
from odoo.exceptions import UserError, ValidationError
from odoo import fields
from .common import RoutyCommonCase
import base64


@tagged('post_install', '-at_install', 'routy')
class TestJob(RoutyCommonCase):
    """Test cases for Job model"""

    def test_01_create_job(self):
        """Test creating a job"""
        sr = self._create_service_request()
        job = self._create_job(sr)
        self.assertTrue(job, "Job should be created")
        self.assertTrue(job.name.startswith('JOB'), "Job should have JOB prefix")
        self.assertEqual(job.state, 'assigned', "New job should be assigned")

    def test_02_job_sequence(self):
        """Test job reference sequence"""
        sr = self._create_service_request()
        j1 = self._create_job(sr)
        j2 = self._create_job(sr)
        self.assertNotEqual(j1.name, j2.name, "Each job should have unique reference")

    def test_03_accept_job(self):
        """Test accepting a job"""
        sr = self._create_service_request()
        job = self._create_job(sr)

        job.action_accept()
        self.assertEqual(job.state, 'accepted')

    def test_04_start_job(self):
        """Test starting a job"""
        sr = self._create_service_request()
        job = self._create_job(sr)

        job.action_accept()
        job.action_start()
        self.assertEqual(job.state, 'in_progress')
        self.assertTrue(job.started_at, "Start timestamp should be set")

    def test_05_start_job_updates_service_request(self):
        """Test starting job updates service request state"""
        sr = self._create_service_request()
        sr.write({'state': 'assigned'})
        job = self._create_job(sr)

        job.action_start()
        self.assertEqual(sr.state, 'in_progress')

    def test_06_complete_pickup_job(self):
        """Test completing a pickup job"""
        sr = self._create_service_request()
        parcel = self._create_parcel(sr)
        job = self._create_job(sr, job_type='pickup')
        job.parcel_ids = [(6, 0, [parcel.id])]

        job.action_start()
        job.action_complete()

        self.assertEqual(job.state, 'completed')
        self.assertTrue(job.completed_at, "Complete timestamp should be set")
        self.assertEqual(parcel.state, 'picked', "Parcel should be marked as picked")
        self.assertTrue(sr.actual_pickup_date, "Actual pickup date should be set")

    def test_07_complete_delivery_job_without_pod(self):
        """Test cannot complete delivery job without POD"""
        sr = self._create_service_request()
        parcel = self._create_parcel(sr)
        job = self._create_job(sr, job_type='delivery')
        job.parcel_ids = [(6, 0, [parcel.id])]

        job.action_start()

        with self.assertRaises(UserError):
            job.action_complete()

    def test_08_complete_delivery_job_with_pod(self):
        """Test completing delivery job with POD"""
        sr = self._create_service_request()
        parcel = self._create_parcel(sr)
        parcel.pod_signature = base64.b64encode(b'signature')

        job = self._create_job(sr, job_type='delivery')
        job.parcel_ids = [(6, 0, [parcel.id])]

        job.action_start()
        job.action_complete()

        self.assertEqual(job.state, 'completed')

    def test_09_fail_job(self):
        """Test marking job as failed"""
        sr = self._create_service_request()
        job = self._create_job(sr)
        job.failure_reason = "Customer not available"

        job.action_start()
        job.action_fail()

        self.assertEqual(job.state, 'failed')
        self.assertTrue(job.completed_at)

    def test_10_fail_job_without_reason(self):
        """Test cannot fail job without reason"""
        sr = self._create_service_request()
        job = self._create_job(sr)

        job.action_start()

        with self.assertRaises(UserError):
            job.action_fail()

    def test_11_fail_delivery_job_marks_parcels_failed(self):
        """Test failing delivery job marks parcels as failed"""
        sr = self._create_service_request()
        parcel = self._create_parcel(sr)
        job = self._create_job(sr, job_type='delivery')
        job.parcel_ids = [(6, 0, [parcel.id])]
        job.failure_reason = "Address not found"

        job.action_start()
        job.action_fail()

        self.assertEqual(parcel.state, 'failed')

    def test_12_duration_computation(self):
        """Test job duration is computed correctly"""
        sr = self._create_service_request()
        job = self._create_job(sr)

        # No duration when not started
        self.assertEqual(job.duration, 0)

        # Set start and complete times manually for testing
        job.started_at = fields.Datetime.now()
        job.completed_at = fields.Datetime.to_datetime('2024-01-15 12:00:00')
        job.started_at = fields.Datetime.to_datetime('2024-01-15 10:00:00')

        job._compute_duration()
        self.assertEqual(job.duration, 2.0, "Duration should be 2 hours")

    def test_13_gps_log_count(self):
        """Test GPS log count computation"""
        sr = self._create_service_request()
        job = self._create_job(sr)

        self.assertEqual(job.gps_log_count, 0)

        # Create GPS logs
        self.env['routy.gps.log'].create({
            'job_id': job.id,
            'driver_id': self.driver_user.id,
            'latitude': 30.0444,
            'longitude': 31.2357,
        })

        self.assertEqual(job.gps_log_count, 1)

    def test_14_parcel_count(self):
        """Test parcel count computation"""
        sr = self._create_service_request()
        p1 = self._create_parcel(sr)
        p2 = self._create_parcel(sr)
        job = self._create_job(sr)

        self.assertEqual(job.parcel_count, 0)

        job.parcel_ids = [(6, 0, [p1.id, p2.id])]
        self.assertEqual(job.parcel_count, 2)

    def test_15_onchange_service_request_pickup(self):
        """Test onchange fills pickup location for pickup job"""
        sr = self._create_service_request()
        job = self.env['routy.job'].new({
            'service_request_id': sr.id,
            'job_type': 'pickup',
            'driver_id': self.driver_user.id,
        })
        job._onchange_service_request_job_type()

        self.assertEqual(job.location_address, sr.pickup_address)
        self.assertEqual(job.location_lat, sr.pickup_lat)
        self.assertEqual(job.location_lng, sr.pickup_lng)
        self.assertEqual(job.contact_phone, sr.pickup_phone)

    def test_16_onchange_service_request_delivery(self):
        """Test onchange fills delivery location for delivery job"""
        sr = self._create_service_request()
        job = self.env['routy.job'].new({
            'service_request_id': sr.id,
            'job_type': 'delivery',
            'driver_id': self.driver_user.id,
        })
        job._onchange_service_request_job_type()

        self.assertEqual(job.location_address, sr.delivery_address)
        self.assertEqual(job.location_lat, sr.delivery_lat)
        self.assertEqual(job.location_lng, sr.delivery_lng)

    def test_17_gps_coordinates_validation(self):
        """Test GPS coordinates validation"""
        sr = self._create_service_request()

        # Valid coordinates
        job = self._create_job(sr, location_lat=30.0, location_lng=31.0)
        self.assertTrue(job)

        # Invalid latitude
        with self.assertRaises(ValidationError):
            self._create_job(sr, location_lat=100.0)

        # Invalid longitude
        with self.assertRaises(ValidationError):
            self._create_job(sr, location_lng=200.0)

    def test_18_invalid_state_transitions(self):
        """Test invalid state transitions are blocked"""
        sr = self._create_service_request()
        job = self._create_job(sr)

        # Cannot complete without starting
        with self.assertRaises(UserError):
            job.action_complete()

        # Cannot accept already started job
        job.action_start()
        with self.assertRaises(UserError):
            job.action_accept()
