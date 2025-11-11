# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ServiceRequest(models.Model):
    _name = 'routy.service_request'
    _description = 'Service Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Basic Information
    name = fields.Char(
        string='Request Number',
        required=True,
        readonly=True,
        copy=False,
        default='New',
        tracking=True
    )
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer/Sender',
        required=True,
        tracking=True,
        index=True
    )
    service_type = fields.Selection([
        ('local', 'Local Delivery'),
        ('express', 'Express'),
        ('scheduled', 'Scheduled')
    ], string='Service Type', default='local', required=True, tracking=True)

    # Pickup Information
    pickup_address = fields.Text(string='Pickup Address', required=True)
    pickup_lat = fields.Float(string='Pickup Latitude', digits=(10, 7))
    pickup_lng = fields.Float(string='Pickup Longitude', digits=(10, 7))
    pickup_contact = fields.Char(string='Pickup Contact Name')
    pickup_phone = fields.Char(string='Pickup Phone', required=True)

    # Delivery Information
    delivery_address = fields.Text(string='Delivery Address', required=True)
    delivery_lat = fields.Float(string='Delivery Latitude', digits=(10, 7))
    delivery_lng = fields.Float(string='Delivery Longitude', digits=(10, 7))
    delivery_contact = fields.Char(string='Delivery Contact Name')
    delivery_phone = fields.Char(string='Delivery Phone', required=True)

    # Relations
    parcel_ids = fields.One2many(
        'routy.parcel',
        'service_request_id',
        string='Parcels'
    )
    parcel_count = fields.Integer(
        string='Parcel Count',
        compute='_compute_parcel_count',
        store=True
    )
    job_ids = fields.One2many(
        'routy.job',
        'service_request_id',
        string='Jobs'
    )

    # Financial
    service_fee = fields.Monetary(
        string='Service Fee',
        currency_field='currency_id',
        tracking=True
    )
    cod_amount = fields.Monetary(
        string='COD Amount',
        currency_field='currency_id',
        help='Cash on Delivery amount',
        tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    # Workflow
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)

    assigned_driver_id = fields.Many2one(
        'res.users',
        string='Assigned Driver',
        tracking=True,
        index=True
    )

    # Dates
    scheduled_pickup_date = fields.Datetime(
        string='Scheduled Pickup Date',
        tracking=True
    )
    scheduled_delivery_date = fields.Datetime(
        string='Scheduled Delivery Date',
        tracking=True
    )
    actual_pickup_date = fields.Datetime(
        string='Actual Pickup Date',
        readonly=True
    )
    actual_delivery_date = fields.Datetime(
        string='Actual Delivery Date',
        readonly=True
    )

    # Notes
    notes = fields.Text(string='Notes')

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    @api.depends('parcel_ids')
    def _compute_parcel_count(self):
        """Compute the number of parcels"""
        for record in self:
            record.parcel_count = len(record.parcel_ids)

    @api.model
    def create(self, vals):
        """Override create to generate sequence"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'routy.service_request'
            ) or 'New'
        return super(ServiceRequest, self).create(vals)

    def action_confirm(self):
        """Confirm the service request"""
        for record in self:
            if not record.parcel_ids:
                raise UserError(_('Cannot confirm a service request without parcels.'))
            record.write({'state': 'confirmed'})
        return True

    def action_assign_driver(self):
        """Open wizard to assign a driver"""
        self.ensure_one()
        return {
            'name': _('Assign Driver'),
            'type': 'ir.actions.act_window',
            'res_model': 'routy.assign.driver.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_service_request_id': self.id,
            }
        }

    def action_cancel(self):
        """Cancel the service request"""
        for record in self:
            if record.state == 'delivered':
                raise UserError(_('Cannot cancel a delivered service request.'))
            # Cancel related jobs
            record.job_ids.filtered(
                lambda j: j.state not in ['completed', 'cancelled']
            ).write({'state': 'cancelled'})
            record.write({'state': 'cancelled'})
        return True

    def action_view_parcels(self):
        """Smart button to view parcels"""
        self.ensure_one()
        return {
            'name': _('Parcels'),
            'type': 'ir.actions.act_window',
            'res_model': 'routy.parcel',
            'view_mode': 'tree,form',
            'domain': [('service_request_id', '=', self.id)],
            'context': {'default_service_request_id': self.id}
        }

    def action_view_jobs(self):
        """Smart button to view jobs"""
        self.ensure_one()
        return {
            'name': _('Jobs'),
            'type': 'ir.actions.act_window',
            'res_model': 'routy.job',
            'view_mode': 'tree,form',
            'domain': [('service_request_id', '=', self.id)],
            'context': {'default_service_request_id': self.id}
        }

    @api.constrains('pickup_lat', 'pickup_lng', 'delivery_lat', 'delivery_lng')
    def _check_coordinates(self):
        """Validate GPS coordinates"""
        for record in self:
            if record.pickup_lat and not (-90 <= record.pickup_lat <= 90):
                raise ValidationError(_('Pickup latitude must be between -90 and 90'))
            if record.pickup_lng and not (-180 <= record.pickup_lng <= 180):
                raise ValidationError(_('Pickup longitude must be between -180 and 180'))
            if record.delivery_lat and not (-90 <= record.delivery_lat <= 90):
                raise ValidationError(_('Delivery latitude must be between -90 and 90'))
            if record.delivery_lng and not (-180 <= record.delivery_lng <= 180):
                raise ValidationError(_('Delivery longitude must be between -180 and 180'))
