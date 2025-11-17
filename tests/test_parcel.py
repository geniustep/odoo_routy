# -*- coding: utf-8 -*-

from odoo.tests import tagged
from odoo.exceptions import UserError, ValidationError
from .common import RoutyCommonCase
import base64


@tagged('post_install', '-at_install', 'routy')
class TestParcel(RoutyCommonCase):
    """Test cases for Parcel model"""

    def test_01_create_parcel(self):
        """Test creating a parcel"""
        sr = self._create_service_request()
        parcel = self._create_parcel(sr)
        self.assertTrue(parcel, "Parcel should be created")
        self.assertTrue(parcel.name.startswith('TRK'), "Parcel should have TRK prefix")
        self.assertEqual(parcel.state, 'pending', "New parcel should be pending")

    def test_02_parcel_sequence(self):
        """Test parcel tracking number sequence"""
        sr = self._create_service_request()
        p1 = self._create_parcel(sr)
        p2 = self._create_parcel(sr)
        self.assertNotEqual(p1.name, p2.name, "Each parcel should have unique tracking number")

    def test_03_volume_computation(self):
        """Test volume is computed from dimensions"""
        sr = self._create_service_request()
        parcel = self._create_parcel(sr, length=30, width=20, height=15)
        self.assertEqual(parcel.volume, 9000, "Volume should be length * width * height")

    def test_04_volume_computation_missing_dimensions(self):
        """Test volume is 0 when dimensions are missing"""
        sr = self._create_service_request()
        parcel = self._create_parcel(sr, length=30, width=0, height=15)
        self.assertEqual(parcel.volume, 0, "Volume should be 0 when any dimension is 0")

    def test_05_negative_dimensions_validation(self):
        """Test negative dimensions are not allowed"""
        sr = self._create_service_request()
        with self.assertRaises(ValidationError):
            self._create_parcel(sr, weight=-5)

        with self.assertRaises(ValidationError):
            self._create_parcel(sr, length=-10)

    def test_06_mark_picked_workflow(self):
        """Test marking parcel as picked"""
        sr = self._create_service_request()
        parcel = self._create_parcel(sr)

        parcel.action_mark_picked()
        self.assertEqual(parcel.state, 'picked')
        self.assertTrue(parcel.picked_at, "Picked timestamp should be set")

    def test_07_mark_in_transit(self):
        """Test marking parcel as in transit"""
        sr = self._create_service_request()
        parcel = self._create_parcel(sr)

        parcel.action_mark_picked()
        parcel.action_mark_in_transit()
        self.assertEqual(parcel.state, 'in_transit')

    def test_08_mark_out_for_delivery(self):
        """Test marking parcel as out for delivery"""
        sr = self._create_service_request()
        parcel = self._create_parcel(sr)

        parcel.action_mark_picked()
        parcel.action_mark_in_transit()
        parcel.action_mark_out_for_delivery()
        self.assertEqual(parcel.state, 'out_for_delivery')

    def test_09_mark_delivered_without_pod(self):
        """Test cannot deliver without proof of delivery"""
        sr = self._create_service_request()
        parcel = self._create_parcel(sr)
        parcel.write({'state': 'out_for_delivery'})

        with self.assertRaises(UserError):
            parcel.action_mark_delivered()

    def test_10_mark_delivered_with_signature(self):
        """Test delivering parcel with signature"""
        sr = self._create_service_request()
        parcel = self._create_parcel(sr)
        parcel.write({'state': 'out_for_delivery'})

        # Add signature (dummy base64)
        parcel.pod_signature = base64.b64encode(b'signature_data')
        parcel.recipient_name = 'Ahmed Ali'

        parcel.action_mark_delivered()
        self.assertEqual(parcel.state, 'delivered')
        self.assertTrue(parcel.delivered_at, "Delivered timestamp should be set")

    def test_11_mark_delivered_with_photo(self):
        """Test delivering parcel with photo"""
        sr = self._create_service_request()
        parcel = self._create_parcel(sr)
        parcel.write({'state': 'out_for_delivery'})

        # Add photo (dummy base64)
        parcel.pod_photo = base64.b64encode(b'photo_data')

        parcel.action_mark_delivered()
        self.assertEqual(parcel.state, 'delivered')

    def test_12_deliver_updates_service_request(self):
        """Test delivering all parcels updates service request"""
        sr = self._create_service_request()
        p1 = self._create_parcel(sr)
        p2 = self._create_parcel(sr)

        # Mark both parcels as out for delivery
        p1.write({
            'state': 'out_for_delivery',
            'pod_signature': base64.b64encode(b'sig1')
        })
        p2.write({
            'state': 'out_for_delivery',
            'pod_signature': base64.b64encode(b'sig2')
        })

        # Deliver first parcel
        p1.action_mark_delivered()
        self.assertNotEqual(sr.state, 'delivered', "SR should not be delivered yet")

        # Deliver second parcel
        p2.action_mark_delivered()
        self.assertEqual(sr.state, 'delivered', "SR should be delivered when all parcels are")

    def test_13_mark_failed(self):
        """Test marking parcel as failed"""
        sr = self._create_service_request()
        parcel = self._create_parcel(sr)
        parcel.write({'state': 'out_for_delivery'})

        parcel.action_mark_failed()
        self.assertEqual(parcel.state, 'failed')

    def test_14_related_fields(self):
        """Test related fields are computed correctly"""
        sr = self._create_service_request()
        parcel = self._create_parcel(sr)

        self.assertEqual(parcel.customer_id, sr.customer_id)
        self.assertEqual(parcel.currency_id, sr.currency_id)
        self.assertEqual(parcel.company_id, sr.company_id)

    def test_15_invalid_state_transitions(self):
        """Test invalid state transitions are blocked"""
        sr = self._create_service_request()
        parcel = self._create_parcel(sr)

        # Cannot mark delivered from pending
        with self.assertRaises(UserError):
            parcel.action_mark_delivered()
