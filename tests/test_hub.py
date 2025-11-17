# -*- coding: utf-8 -*-

from odoo.tests import tagged
from odoo.exceptions import ValidationError
from .common import RoutyCommonCase


@tagged('post_install', '-at_install', 'routy')
class TestHub(RoutyCommonCase):
    """Test cases for Hub model"""

    def test_01_create_hub(self):
        """Test creating a hub"""
        hub = self.hub_main
        self.assertTrue(hub, "Hub should be created")
        self.assertEqual(hub.code, 'HUB-CAI')
        self.assertEqual(hub.hub_type, 'main')

    def test_02_unique_hub_code(self):
        """Test hub code should be unique"""
        with self.assertRaises(Exception):
            self.env['routy.hub'].create({
                'name': 'Duplicate Hub',
                'code': 'HUB-CAI',  # Same as hub_main
                'hub_type': 'distribution',
                'address': 'Test Address',
            })

    def test_03_gps_coordinates_validation(self):
        """Test GPS coordinates validation"""
        # Invalid latitude
        with self.assertRaises(ValidationError):
            self.env['routy.hub'].create({
                'name': 'Invalid Hub',
                'code': 'HUB-INV',
                'hub_type': 'distribution',
                'address': 'Test',
                'latitude': 100.0,
            })
