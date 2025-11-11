# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class Linehaul(models.Model):
    _name = 'routy.linehaul'
    _description = 'Linehaul - Inter-city Transport'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_departure desc'

    # Basic Information
    name = fields.Char(
        string='Linehaul Reference',
        required=True,
        readonly=True,
        copy=False,
        default='New',
        tracking=True,
        index=True
    )
    departure_hub_id = fields.Many2one(
        'routy.hub',
        string='Departure Hub',
        required=True,
        tracking=True,
        index=True
    )
    arrival_hub_id = fields.Many2one(
        'routy.hub',
        string='Arrival Hub',
        required=True,
        tracking=True,
        index=True
    )
    driver_id = fields.Many2one(
        'res.users',
        string='Driver',
        tracking=True
    )
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string='Vehicle',
        help='Vehicle used for transport (requires fleet module)'
    )

    # Schedule
    scheduled_departure = fields.Datetime(
        string='Scheduled Departure',
        required=True,
        tracking=True
    )
    scheduled_arrival = fields.Datetime(
        string='Scheduled Arrival',
        required=True,
        tracking=True
    )
    actual_departure = fields.Datetime(
        string='Actual Departure',
        readonly=True,
        tracking=True
    )
    actual_arrival = fields.Datetime(
        string='Actual Arrival',
        readonly=True,
        tracking=True
    )

    # Cargo
    parcel_ids = fields.Many2many(
        'routy.parcel',
        string='Parcels',
        help='Parcels being transported'
    )
    parcel_count = fields.Integer(
        string='Parcel Count',
        compute='_compute_parcel_count',
        store=True
    )
    total_weight = fields.Float(
        string='Total Weight (kg)',
        compute='_compute_total_weight',
        store=True,
        digits=(10, 2)
    )

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('in_transit', 'In Transit'),
        ('arrived', 'Arrived'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)

    # Tracking
    distance_km = fields.Float(
        string='Distance (km)',
        digits=(10, 2),
        help='Distance in kilometers'
    )
    duration_hours = fields.Float(
        string='Duration (Hours)',
        compute='_compute_duration',
        store=True,
        help='Actual duration from departure to arrival'
    )
    estimated_duration_hours = fields.Float(
        string='Estimated Duration',
        compute='_compute_estimated_duration',
        store=True,
        help='Estimated duration based on schedule'
    )

    # Costs
    fuel_cost = fields.Monetary(
        string='Fuel Cost',
        currency_field='currency_id'
    )
    driver_cost = fields.Monetary(
        string='Driver Cost',
        currency_field='currency_id'
    )
    other_costs = fields.Monetary(
        string='Other Costs',
        currency_field='currency_id'
    )
    total_cost = fields.Monetary(
        string='Total Cost',
        compute='_compute_total_cost',
        store=True,
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
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
        """Compute parcel count"""
        for record in self:
            record.parcel_count = len(record.parcel_ids)

    @api.depends('parcel_ids.weight')
    def _compute_total_weight(self):
        """Compute total weight of all parcels"""
        for record in self:
            record.total_weight = sum(record.parcel_ids.mapped('weight'))

    @api.depends('actual_departure', 'actual_arrival')
    def _compute_duration(self):
        """Calculate actual duration"""
        for record in self:
            if record.actual_departure and record.actual_arrival:
                delta = record.actual_arrival - record.actual_departure
                record.duration_hours = delta.total_seconds() / 3600.0
            else:
                record.duration_hours = 0.0

    @api.depends('scheduled_departure', 'scheduled_arrival')
    def _compute_estimated_duration(self):
        """Calculate estimated duration"""
        for record in self:
            if record.scheduled_departure and record.scheduled_arrival:
                delta = record.scheduled_arrival - record.scheduled_departure
                record.estimated_duration_hours = delta.total_seconds() / 3600.0
            else:
                record.estimated_duration_hours = 0.0

    @api.depends('fuel_cost', 'driver_cost', 'other_costs')
    def _compute_total_cost(self):
        """Calculate total cost"""
        for record in self:
            record.total_cost = (
                record.fuel_cost +
                record.driver_cost +
                record.other_costs
            )

    @api.model
    def create(self, vals):
        """Override create to generate sequence"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'routy.linehaul'
            ) or 'New'
        return super(Linehaul, self).create(vals)

    def action_confirm(self):
        """Confirm the linehaul"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft linehauls can be confirmed.'))
            if not record.driver_id:
                raise UserError(_('Please assign a driver before confirming.'))
            if not record.parcel_ids:
                raise UserError(_('Please add parcels before confirming.'))
            record.write({'state': 'confirmed'})
        return True

    def action_depart(self):
        """Mark as departed"""
        for record in self:
            if record.state != 'confirmed':
                raise UserError(_('Only confirmed linehauls can depart.'))
            record.write({
                'state': 'in_transit',
                'actual_departure': fields.Datetime.now()
            })
            # Update parcels to in_transit
            record.parcel_ids.write({'state': 'in_transit'})
        return True

    def action_arrive(self):
        """Mark as arrived"""
        for record in self:
            if record.state != 'in_transit':
                raise UserError(_('Only in-transit linehauls can arrive.'))
            record.write({
                'state': 'arrived',
                'actual_arrival': fields.Datetime.now()
            })
        return True

    def action_cancel(self):
        """Cancel the linehaul"""
        for record in self:
            if record.state == 'arrived':
                raise UserError(_('Cannot cancel an arrived linehaul.'))
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
            'domain': [('id', 'in', self.parcel_ids.ids)],
            'context': {}
        }

    @api.constrains('departure_hub_id', 'arrival_hub_id')
    def _check_hubs(self):
        """Validate hubs"""
        for record in self:
            if record.departure_hub_id == record.arrival_hub_id:
                raise ValidationError(_('Departure and arrival hubs must be different.'))

    @api.constrains('scheduled_departure', 'scheduled_arrival')
    def _check_schedule(self):
        """Validate schedule"""
        for record in self:
            if record.scheduled_departure and record.scheduled_arrival:
                if record.scheduled_departure >= record.scheduled_arrival:
                    raise ValidationError(_('Scheduled departure must be before scheduled arrival.'))
