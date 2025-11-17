# -*- coding: utf-8 -*-

from odoo.tests import tagged
from odoo.exceptions import ValidationError
from .common import RoutyCommonCase


@tagged('post_install', '-at_install', 'routy')
class TestPaymentRecord(RoutyCommonCase):
    """Test cases for Payment Record model"""

    def test_01_create_payment_record(self):
        """Test creating a payment record"""
        payment = self.env['routy.payment_record'].create({
            'driver_id': self.driver_user.id,
            'payment_type': 'cod_collection',
            'amount': 500.0,
            'payment_method': 'cash',
        })
        self.assertTrue(payment)
        self.assertTrue(payment.name.startswith('PAY'))

    def test_02_negative_amount_validation(self):
        """Test cannot create payment with negative amount"""
        with self.assertRaises(ValidationError):
            self.env['routy.payment_record'].create({
                'driver_id': self.driver_user.id,
                'payment_type': 'cod_collection',
                'amount': -100.0,
                'payment_method': 'cash',
            })
