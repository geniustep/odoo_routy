# -*- coding: utf-8 -*-

from odoo.tests import tagged, HttpCase
from odoo.tests.common import get_db_name
import json
import base64


@tagged('post_install', '-at_install', 'routy')
class TestMobileAPI(HttpCase):
    """Test cases for Mobile API endpoints"""

    def setUp(self):
        super(TestMobileAPI, self).setUp()

        # Create security groups
        self.group_driver = self.env.ref('routy.group_driver')

        # Create test driver user
        self.driver_user = self.env['res.users'].create({
            'name': 'API Test Driver',
            'login': 'api_driver',
            'password': 'api_driver',
            'email': 'api_driver@test.com',
            'groups_id': [(6, 0, [self.group_driver.id])]
        })

        # Create test customer
        self.customer = self.env['res.partner'].create({
            'name': 'API Test Customer',
            'email': 'customer@test.com',
            'phone': '+201234567890'
        })

        # Authenticate as driver
        self.authenticate('api_driver', 'api_driver')

    def test_01_get_my_jobs_unauthenticated(self):
        """Test getting jobs without authentication"""
        # Logout
        self.logout()

        response = self.url_open('/api/v1/routy/jobs/my')
        self.assertEqual(response.status_code, 401)

    def test_02_get_my_jobs_empty(self):
        """Test getting jobs when driver has no jobs"""
        response = self.url_open('/api/v1/routy/jobs/my')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 0)
        self.assertEqual(len(data['jobs']), 0)

    def test_03_get_my_jobs_with_jobs(self):
        """Test getting jobs when driver has jobs"""
        # Create service request and job
        sr = self.env['routy.service_request'].create({
            'customer_id': self.customer.id,
            'service_type': 'local',
            'pickup_address': '123 Pickup St',
            'pickup_phone': '+201111111111',
            'delivery_address': '456 Delivery St',
            'delivery_phone': '+202222222222',
        })

        job = self.env['routy.job'].create({
            'job_type': 'pickup',
            'service_request_id': sr.id,
            'driver_id': self.driver_user.id,
            'location_address': sr.pickup_address,
            'contact_phone': sr.pickup_phone,
        })

        response = self.url_open('/api/v1/routy/jobs/my')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['jobs'][0]['id'], job.id)
        self.assertEqual(data['jobs'][0]['job_type'], 'pickup')

    def test_04_get_my_jobs_filtered_by_state(self):
        """Test filtering jobs by state"""
        sr = self.env['routy.service_request'].create({
            'customer_id': self.customer.id,
            'service_type': 'local',
            'pickup_address': '123 Pickup St',
            'pickup_phone': '+201111111111',
            'delivery_address': '456 Delivery St',
            'delivery_phone': '+202222222222',
        })

        # Create assigned and accepted jobs
        job1 = self.env['routy.job'].create({
            'job_type': 'pickup',
            'service_request_id': sr.id,
            'driver_id': self.driver_user.id,
            'location_address': sr.pickup_address,
            'state': 'assigned',
        })

        job2 = self.env['routy.job'].create({
            'job_type': 'delivery',
            'service_request_id': sr.id,
            'driver_id': self.driver_user.id,
            'location_address': sr.delivery_address,
            'state': 'accepted',
        })

        # Get only assigned jobs
        response = self.url_open('/api/v1/routy/jobs/my?state=assigned')
        data = json.loads(response.content)
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['jobs'][0]['state'], 'assigned')

    def test_05_accept_job(self):
        """Test accepting a job"""
        sr = self.env['routy.service_request'].create({
            'customer_id': self.customer.id,
            'service_type': 'local',
            'pickup_address': '123 Pickup St',
            'pickup_phone': '+201111111111',
            'delivery_address': '456 Delivery St',
            'delivery_phone': '+202222222222',
        })

        job = self.env['routy.job'].create({
            'job_type': 'pickup',
            'service_request_id': sr.id,
            'driver_id': self.driver_user.id,
            'location_address': sr.pickup_address,
        })

        response = self.url_open(f'/api/v1/routy/jobs/{job.id}/accept',
                                data={})
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['state'], 'accepted')

        # Verify in database
        job.invalidate_recordset()
        self.assertEqual(job.state, 'accepted')

    def test_06_accept_nonexistent_job(self):
        """Test accepting non-existent job returns 404"""
        response = self.url_open('/api/v1/routy/jobs/999999/accept',
                                data={})
        self.assertEqual(response.status_code, 404)

    def test_07_start_job(self):
        """Test starting a job"""
        sr = self.env['routy.service_request'].create({
            'customer_id': self.customer.id,
            'service_type': 'local',
            'pickup_address': '123 Pickup St',
            'pickup_phone': '+201111111111',
            'delivery_address': '456 Delivery St',
            'delivery_phone': '+202222222222',
        })

        job = self.env['routy.job'].create({
            'job_type': 'pickup',
            'service_request_id': sr.id,
            'driver_id': self.driver_user.id,
            'location_address': sr.pickup_address,
            'state': 'accepted',
        })

        response = self.url_open(f'/api/v1/routy/jobs/{job.id}/start',
                                data={})
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['state'], 'in_progress')
        self.assertIsNotNone(data.get('started_at'))

    def test_08_complete_job(self):
        """Test completing a job"""
        sr = self.env['routy.service_request'].create({
            'customer_id': self.customer.id,
            'service_type': 'local',
            'pickup_address': '123 Pickup St',
            'pickup_phone': '+201111111111',
            'delivery_address': '456 Delivery St',
            'delivery_phone': '+202222222222',
        })

        parcel = self.env['routy.parcel'].create({
            'service_request_id': sr.id,
            'description': 'Test parcel',
            'weight': 1.0,
        })

        job = self.env['routy.job'].create({
            'job_type': 'pickup',
            'service_request_id': sr.id,
            'driver_id': self.driver_user.id,
            'location_address': sr.pickup_address,
            'state': 'in_progress',
            'parcel_ids': [(6, 0, [parcel.id])],
        })

        response = self.url_open(f'/api/v1/routy/jobs/{job.id}/complete',
                                data={})
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['state'], 'completed')

    def test_09_get_parcel_details(self):
        """Test getting parcel details"""
        sr = self.env['routy.service_request'].create({
            'customer_id': self.customer.id,
            'service_type': 'local',
            'pickup_address': '123 Pickup St',
            'pickup_phone': '+201111111111',
            'delivery_address': '456 Delivery St',
            'delivery_phone': '+202222222222',
            'assigned_driver_id': self.driver_user.id,
        })

        parcel = self.env['routy.parcel'].create({
            'service_request_id': sr.id,
            'description': 'Electronics',
            'weight': 2.5,
            'declared_value': 1000.0,
        })

        response = self.url_open(f'/api/v1/routy/parcels/{parcel.id}')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['parcel']['id'], parcel.id)
        self.assertEqual(data['parcel']['description'], 'Electronics')
        self.assertEqual(data['parcel']['weight'], 2.5)

    def test_10_unauthorized_job_access(self):
        """Test driver cannot access another driver's job"""
        # Create another driver
        other_driver = self.env['res.users'].create({
            'name': 'Other Driver',
            'login': 'other_driver',
            'email': 'other@test.com',
            'groups_id': [(6, 0, [self.group_driver.id])]
        })

        sr = self.env['routy.service_request'].create({
            'customer_id': self.customer.id,
            'service_type': 'local',
            'pickup_address': '123 Pickup St',
            'pickup_phone': '+201111111111',
            'delivery_address': '456 Delivery St',
            'delivery_phone': '+202222222222',
        })

        # Create job for other driver
        job = self.env['routy.job'].create({
            'job_type': 'pickup',
            'service_request_id': sr.id,
            'driver_id': other_driver.id,
            'location_address': sr.pickup_address,
        })

        # Try to accept as current driver
        response = self.url_open(f'/api/v1/routy/jobs/{job.id}/accept',
                                data={})
        self.assertEqual(response.status_code, 403)
