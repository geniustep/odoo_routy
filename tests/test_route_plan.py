# -*- coding: utf-8 -*-

from odoo.tests import tagged
from .common import RoutyCommonCase


@tagged('post_install', '-at_install', 'routy')
class TestRoutePlan(RoutyCommonCase):
    """Test cases for Route Plan model"""

    def test_01_create_route_plan(self):
        """Test creating a route plan"""
        route_plan = self.env['routy.route_plan'].create({
            'driver_id': self.driver_user.id,
            'date': '2024-01-15',
            'notes': 'Daily route',
        })
        self.assertTrue(route_plan)
        self.assertEqual(route_plan.state, 'draft')
