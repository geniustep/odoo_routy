# -*- coding: utf-8 -*-

from odoo.tests import tagged
from odoo.exceptions import UserError, ValidationError
from .common import RoutyCommonCase


@tagged('post_install', '-at_install', 'routy')
class TestServiceRequest(RoutyCommonCase):
    """Test cases for Service Request model"""

    def test_01_create_service_request(self):
        """Test creating a service request"""
        sr = self._create_service_request()
        self.assertTrue(sr, "Service request should be created")
        self.assertTrue(sr.name.startswith('SR'), "Service request should have SR prefix")
        self.assertEqual(sr.state, 'draft', "New service request should be in draft state")

    def test_02_service_request_sequence(self):
        """Test that sequence is auto-generated"""
        sr1 = self._create_service_request()
        sr2 = self._create_service_request()
        self.assertNotEqual(sr1.name, sr2.name, "Each service request should have unique number")

    def test_03_confirm_service_request_without_parcels(self):
        """Test confirming service request without parcels should fail"""
        sr = self._create_service_request()
        with self.assertRaises(UserError):
            sr.action_confirm()

    def test_04_confirm_service_request_with_parcels(self):
        """Test confirming service request with parcels"""
        sr = self._create_service_request()
        self._create_parcel(sr)
        sr.action_confirm()
        self.assertEqual(sr.state, 'confirmed', "Service request should be confirmed")

    def test_05_parcel_count_computation(self):
        """Test parcel count is computed correctly"""
        sr = self._create_service_request()
        self.assertEqual(sr.parcel_count, 0, "New SR should have 0 parcels")

        self._create_parcel(sr)
        self.assertEqual(sr.parcel_count, 1, "SR should have 1 parcel")

        self._create_parcel(sr)
        self.assertEqual(sr.parcel_count, 2, "SR should have 2 parcels")

    def test_06_cancel_service_request(self):
        """Test canceling service request"""
        sr = self._create_service_request()
        sr.action_cancel()
        self.assertEqual(sr.state, 'cancelled', "Service request should be cancelled")

    def test_07_cannot_cancel_delivered(self):
        """Test cannot cancel delivered service request"""
        sr = self._create_service_request()
        sr.write({'state': 'delivered'})
        with self.assertRaises(UserError):
            sr.action_cancel()

    def test_08_gps_coordinates_validation(self):
        """Test GPS coordinates validation"""
        # Valid coordinates
        sr = self._create_service_request(
            pickup_lat=30.0444,
            pickup_lng=31.2357
        )
        self.assertTrue(sr, "Valid coordinates should be accepted")

        # Invalid latitude
        with self.assertRaises(ValidationError):
            self._create_service_request(pickup_lat=100.0)

        # Invalid longitude
        with self.assertRaises(ValidationError):
            self._create_service_request(pickup_lng=200.0)

    def test_09_assign_driver_wizard(self):
        """Test assign driver functionality"""
        sr = self._create_service_request()
        self._create_parcel(sr)
        sr.action_confirm()

        # Assign driver via wizard
        wizard = self.env['routy.assign.driver.wizard'].create({
            'service_request_id': sr.id,
            'driver_id': self.driver_user.id,
            'scheduled_pickup': '2024-01-15 10:00:00',
            'create_pickup_job': True,
            'create_delivery_job': True,
        })
        wizard.action_assign()

        self.assertEqual(sr.assigned_driver_id, self.driver_user)
        self.assertEqual(sr.state, 'assigned')
        self.assertEqual(len(sr.job_ids), 2, "Should create 2 jobs (pickup + delivery)")

    def test_10_view_parcels_action(self):
        """Test view parcels smart button action"""
        sr = self._create_service_request()
        action = sr.action_view_parcels()
        self.assertEqual(action['res_model'], 'routy.parcel')
        self.assertIn(('service_request_id', '=', sr.id), action['domain'])

    def test_11_view_jobs_action(self):
        """Test view jobs smart button action"""
        sr = self._create_service_request()
        action = sr.action_view_jobs()
        self.assertEqual(action['res_model'], 'routy.job')

    def test_12_currency_default(self):
        """Test currency is set to company currency by default"""
        sr = self._create_service_request()
        self.assertEqual(sr.currency_id, self.env.company.currency_id)

    def test_13_company_default(self):
        """Test company is set to current company by default"""
        sr = self._create_service_request()
        self.assertEqual(sr.company_id, self.env.company)
