# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AssignDriverWizard(models.TransientModel):
    _name = 'routy.assign.driver.wizard'
    _description = 'Assign Driver Wizard'

    service_request_id = fields.Many2one(
        'routy.service_request',
        string='Service Request',
        required=True,
        readonly=True
    )
    driver_id = fields.Many2one(
        'res.users',
        string='Driver',
        required=True
    )
    scheduled_pickup = fields.Datetime(
        string='Scheduled Pickup',
        default=fields.Datetime.now,
        required=True
    )
    scheduled_delivery = fields.Datetime(
        string='Scheduled Delivery'
    )
    create_pickup_job = fields.Boolean(
        string='Create Pickup Job',
        default=True
    )
    create_delivery_job = fields.Boolean(
        string='Create Delivery Job',
        default=True
    )
    notes = fields.Text(string='Notes')

    def action_assign(self):
        """Assign driver and create jobs"""
        self.ensure_one()

        if not self.service_request_id:
            raise UserError(_('Service request is required.'))

        # Update service request
        self.service_request_id.write({
            'assigned_driver_id': self.driver_id.id,
            'scheduled_pickup_date': self.scheduled_pickup,
            'scheduled_delivery_date': self.scheduled_delivery or self.scheduled_pickup,
            'state': 'assigned'
        })

        # Create pickup job
        if self.create_pickup_job:
            pickup_job = self.env['routy.job'].create({
                'job_type': 'pickup',
                'service_request_id': self.service_request_id.id,
                'driver_id': self.driver_id.id,
                'location_address': self.service_request_id.pickup_address,
                'location_lat': self.service_request_id.pickup_lat,
                'location_lng': self.service_request_id.pickup_lng,
                'contact_name': self.service_request_id.pickup_contact,
                'contact_phone': self.service_request_id.pickup_phone,
                'scheduled_time': self.scheduled_pickup,
                'notes': self.notes,
            })
            # Assign parcels to pickup job
            if self.service_request_id.parcel_ids:
                pickup_job.parcel_ids = [(6, 0, self.service_request_id.parcel_ids.ids)]

        # Create delivery job
        if self.create_delivery_job:
            delivery_time = self.scheduled_delivery or self.scheduled_pickup
            delivery_job = self.env['routy.job'].create({
                'job_type': 'delivery',
                'service_request_id': self.service_request_id.id,
                'driver_id': self.driver_id.id,
                'location_address': self.service_request_id.delivery_address,
                'location_lat': self.service_request_id.delivery_lat,
                'location_lng': self.service_request_id.delivery_lng,
                'contact_name': self.service_request_id.delivery_contact,
                'contact_phone': self.service_request_id.delivery_phone,
                'scheduled_time': delivery_time,
                'notes': self.notes,
            })
            # Assign parcels to delivery job
            if self.service_request_id.parcel_ids:
                delivery_job.parcel_ids = [(6, 0, self.service_request_id.parcel_ids.ids)]

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Driver %s has been assigned successfully!') % self.driver_id.name,
                'type': 'success',
                'sticky': False,
            }
        }
