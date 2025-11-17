# -*- coding: utf-8 -*-

from odoo.tests import tagged
from .common import RoutyCommonCase


@tagged('post_install', '-at_install', 'routy')
class TestIncident(RoutyCommonCase):
    """Test cases for Incident model"""

    def test_01_create_incident(self):
        """Test creating an incident"""
        incident = self.env['routy.incident'].create({
            'title': 'Delivery Delay',
            'incident_type': 'delay',
            'priority': 'medium',
            'description': 'Package delayed due to traffic',
        })
        self.assertTrue(incident)
        self.assertTrue(incident.name.startswith('INC'))
        self.assertEqual(incident.state, 'new')
