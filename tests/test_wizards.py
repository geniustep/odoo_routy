# -*- coding: utf-8 -*-

from odoo.tests import tagged
from .common import RoutyCommonCase


@tagged('post_install', '-at_install', 'routy')
class TestWizards(RoutyCommonCase):
    """Test cases for Wizards"""

    def test_01_assign_driver_wizard(self):
        """Test assign driver wizard"""
        sr = self._create_service_request()
        self._create_parcel(sr)
        sr.action_confirm()

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
        self.assertEqual(len(sr.job_ids), 2)
