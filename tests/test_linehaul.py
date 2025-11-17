# -*- coding: utf-8 -*-

from odoo.tests import tagged
from odoo.exceptions import ValidationError
from .common import RoutyCommonCase


@tagged('post_install', '-at_install', 'routy')
class TestLinehaul(RoutyCommonCase):
    """Test cases for Linehaul model"""

    def test_01_create_linehaul(self):
        """Test creating a linehaul"""
        linehaul = self.env['routy.linehaul'].create({
            'departure_hub_id': self.hub_main.id,
            'arrival_hub_id': self.hub_secondary.id,
            'driver_id': self.driver_user.id,
            'scheduled_departure': '2024-01-15 08:00:00',
            'scheduled_arrival': '2024-01-15 12:00:00',
        })
        self.assertTrue(linehaul)
        self.assertTrue(linehaul.name.startswith('LH'))

    def test_02_cannot_have_same_departure_arrival(self):
        """Test cannot create linehaul with same departure and arrival hub"""
        with self.assertRaises(ValidationError):
            self.env['routy.linehaul'].create({
                'departure_hub_id': self.hub_main.id,
                'arrival_hub_id': self.hub_main.id,
                'scheduled_departure': '2024-01-15 08:00:00',
            })
