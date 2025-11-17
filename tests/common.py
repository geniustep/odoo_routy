# -*- coding: utf-8 -*-

from odoo.tests import common


class RoutyCommonCase(common.TransactionCase):
    """Base test class for Routy tests"""

    @classmethod
    def setUpClass(cls):
        super(RoutyCommonCase, cls).setUpClass()

        # Create security groups
        cls.group_driver = cls.env.ref('routy.group_driver')
        cls.group_dispatcher = cls.env.ref('routy.group_dispatcher')
        cls.group_manager = cls.env.ref('routy.group_manager')

        # Create test users
        cls.driver_user = cls.env['res.users'].create({
            'name': 'Test Driver',
            'login': 'test_driver',
            'email': 'driver@test.com',
            'groups_id': [(6, 0, [cls.group_driver.id])]
        })

        cls.dispatcher_user = cls.env['res.users'].create({
            'name': 'Test Dispatcher',
            'login': 'test_dispatcher',
            'email': 'dispatcher@test.com',
            'groups_id': [(6, 0, [cls.group_dispatcher.id])]
        })

        cls.manager_user = cls.env['res.users'].create({
            'name': 'Test Manager',
            'login': 'test_manager',
            'email': 'manager@test.com',
            'groups_id': [(6, 0, [cls.group_manager.id])]
        })

        # Create test customer
        cls.customer = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'customer@test.com',
            'phone': '+201234567890'
        })

        # Create test hubs
        cls.hub_main = cls.env['routy.hub'].create({
            'name': 'Main Hub Cairo',
            'code': 'HUB-CAI',
            'hub_type': 'main',
            'address': '123 Main Street, Cairo',
            'city': 'Cairo',
            'latitude': 30.0444,
            'longitude': 31.2357,
        })

        cls.hub_secondary = cls.env['routy.hub'].create({
            'name': 'Distribution Center Alex',
            'code': 'HUB-ALX',
            'hub_type': 'distribution',
            'address': '456 Alex Street, Alexandria',
            'city': 'Alexandria',
            'latitude': 31.2001,
            'longitude': 29.9187,
        })

    def _create_service_request(self, customer=None, **kwargs):
        """Helper to create service request"""
        vals = {
            'customer_id': (customer or self.customer).id,
            'service_type': 'local',
            'pickup_address': '123 Pickup Street',
            'pickup_phone': '+201111111111',
            'pickup_lat': 30.0444,
            'pickup_lng': 31.2357,
            'delivery_address': '456 Delivery Street',
            'delivery_phone': '+202222222222',
            'delivery_lat': 30.0500,
            'delivery_lng': 31.2400,
            'service_fee': 50.0,
            'cod_amount': 200.0,
        }
        vals.update(kwargs)
        return self.env['routy.service_request'].create(vals)

    def _create_parcel(self, service_request, **kwargs):
        """Helper to create parcel"""
        vals = {
            'service_request_id': service_request.id,
            'description': 'Test Package',
            'weight': 2.5,
            'length': 30.0,
            'width': 20.0,
            'height': 15.0,
            'declared_value': 500.0,
        }
        vals.update(kwargs)
        return self.env['routy.parcel'].create(vals)

    def _create_job(self, service_request, driver=None, **kwargs):
        """Helper to create job"""
        vals = {
            'job_type': 'pickup',
            'service_request_id': service_request.id,
            'driver_id': (driver or self.driver_user).id,
            'location_address': service_request.pickup_address,
            'location_lat': service_request.pickup_lat,
            'location_lng': service_request.pickup_lng,
            'contact_phone': service_request.pickup_phone,
        }
        vals.update(kwargs)
        return self.env['routy.job'].create(vals)
