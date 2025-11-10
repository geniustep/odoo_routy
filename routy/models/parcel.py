# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class Parcel(models.Model):
    _name = 'routy.parcel'
    _description = 'Parcel/Package'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Basic Information
    name = fields.Char(
        string='Tracking Number',
        required=True,
        readonly=True,
        copy=False,
        default='New',
        tracking=True,
        index=True
    )
    service_request_id = fields.Many2one(
        'routy.service_request',
        string='Service Request',
        required=True,
        ondelete='cascade',
        tracking=True,
        index=True
    )
    description = fields.Text(
        string='Content Description',
        help='Description of package contents'
    )

    # Physical Properties
    weight = fields.Float(
        string='Weight (kg)',
        digits=(10, 2),
        help='Weight in kilograms',
        tracking=True
    )
    length = fields.Float(
        string='Length (cm)',
        digits=(10, 2),
        help='Length in centimeters'
    )
    width = fields.Float(
        string='Width (cm)',
        digits=(10, 2),
        help='Width in centimeters'
    )
    height = fields.Float(
        string='Height (cm)',
        digits=(10, 2),
        help='Height in centimeters'
    )
    volume = fields.Float(
        string='Volume (cm³)',
        compute='_compute_volume',
        store=True,
        digits=(10, 2),
        help='Calculated volume in cubic centimeters'
    )
    declared_value = fields.Monetary(
        string='Declared Value',
        currency_field='currency_id',
        help='Declared value of the package contents',
        tracking=True
    )

    # Status
    state = fields.Selection([
        ('pending', 'Pending'),
        ('picked', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('out_for_delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('returned', 'Returned')
    ], string='Status', default='pending', required=True, tracking=True)

    # Timestamps
    picked_at = fields.Datetime(
        string='Picked Up At',
        readonly=True,
        tracking=True
    )
    delivered_at = fields.Datetime(
        string='Delivered At',
        readonly=True,
        tracking=True
    )

    # POD (Proof of Delivery)
    pod_signature = fields.Binary(
        string='Signature',
        help='Digital signature of recipient',
        attachment=True
    )
    pod_photo = fields.Binary(
        string='Delivery Photo',
        help='Photo proof of delivery',
        attachment=True
    )
    pod_notes = fields.Text(
        string='Delivery Notes',
        help='Notes from delivery'
    )
    recipient_name = fields.Char(
        string='Actual Recipient Name',
        help='Name of the person who received the package'
    )

    # Relations
    current_job_id = fields.Many2one(
        'routy.job',
        string='Current Job',
        help='Current job handling this parcel',
        index=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='service_request_id.currency_id',
        string='Currency',
        store=True
    )

    # Related fields for easy access
    customer_id = fields.Many2one(
        'res.partner',
        related='service_request_id.customer_id',
        string='Customer',
        store=True,
        index=True
    )
    assigned_driver_id = fields.Many2one(
        'res.users',
        related='service_request_id.assigned_driver_id',
        string='Assigned Driver',
        store=True
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        related='service_request_id.company_id',
        string='Company',
        store=True
    )

    @api.depends('length', 'width', 'height')
    def _compute_volume(self):
        """Calculate volume from dimensions"""
        for record in self:
            if record.length and record.width and record.height:
                record.volume = record.length * record.width * record.height
            else:
                record.volume = 0.0

    @api.model
    def create(self, vals):
        """Override create to generate tracking number"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'routy.parcel'
            ) or 'New'
        return super(Parcel, self).create(vals)

    def action_mark_picked(self):
        """Mark parcel as picked up"""
        for record in self:
            if record.state != 'pending':
                raise UserError(_('Only pending parcels can be marked as picked.'))
            record.write({
                'state': 'picked',
                'picked_at': fields.Datetime.now()
            })
        return True

    def action_mark_in_transit(self):
        """Mark parcel as in transit"""
        for record in self:
            if record.state not in ['picked', 'pending']:
                raise UserError(_('Only picked or pending parcels can be marked as in transit.'))
            record.write({'state': 'in_transit'})
        return True

    def action_mark_out_for_delivery(self):
        """Mark parcel as out for delivery"""
        for record in self:
            if record.state not in ['in_transit', 'picked']:
                raise UserError(_('Only in-transit or picked parcels can be marked as out for delivery.'))
            record.write({'state': 'out_for_delivery'})
        return True

    def action_mark_delivered(self):
        """Mark parcel as delivered"""
        for record in self:
            if record.state != 'out_for_delivery':
                raise UserError(_('Only parcels out for delivery can be marked as delivered.'))
            if not record.pod_signature and not record.pod_photo:
                raise UserError(_('Please provide proof of delivery (signature or photo).'))
            record.write({
                'state': 'delivered',
                'delivered_at': fields.Datetime.now()
            })
            # Update service request if all parcels delivered
            service_request = record.service_request_id
            if all(p.state == 'delivered' for p in service_request.parcel_ids):
                service_request.write({
                    'state': 'delivered',
                    'actual_delivery_date': fields.Datetime.now()
                })
        return True

    def action_mark_failed(self):
        """Mark delivery as failed"""
        for record in self:
            if record.state not in ['out_for_delivery', 'in_transit']:
                raise UserError(_('Only parcels in delivery can be marked as failed.'))
            record.write({'state': 'failed'})
        return True

    @api.constrains('weight', 'length', 'width', 'height')
    def _check_dimensions(self):
        """Validate physical dimensions"""
        for record in self:
            if record.weight and record.weight < 0:
                raise ValidationError(_('Weight cannot be negative'))
            if record.length and record.length < 0:
                raise ValidationError(_('Length cannot be negative'))
            if record.width and record.width < 0:
                raise ValidationError(_('Width cannot be negative'))
            if record.height and record.height < 0:
                raise ValidationError(_('Height cannot be negative'))
