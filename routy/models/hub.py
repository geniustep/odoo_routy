# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Hub(models.Model):
    _name = 'routy.hub'
    _description = 'Distribution Hub/Center'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # Basic Information
    name = fields.Char(
        string='Hub Name',
        required=True,
        tracking=True,
        index=True
    )
    code = fields.Char(
        string='Hub Code',
        required=True,
        copy=False,
        tracking=True,
        index=True
    )
    hub_type = fields.Selection([
        ('main', 'Main Hub'),
        ('distribution', 'Distribution Center'),
        ('micro', 'Micro Hub')
    ], string='Hub Type', required=True, default='distribution', tracking=True)

    # Location
    address = fields.Text(string='Address', required=True)
    city = fields.Char(string='City')
    state_id = fields.Many2one(
        'res.country.state',
        string='State',
        ondelete='restrict'
    )
    country_id = fields.Many2one(
        'res.country',
        string='Country',
        ondelete='restrict'
    )
    zip = fields.Char(string='ZIP Code')
    latitude = fields.Float(
        string='Latitude',
        digits=(10, 7),
        help='GPS Latitude coordinate'
    )
    longitude = fields.Float(
        string='Longitude',
        digits=(10, 7),
        help='GPS Longitude coordinate'
    )

    # Capacity
    max_capacity = fields.Integer(
        string='Max Capacity',
        help='Maximum number of parcels the hub can handle',
        default=1000
    )
    current_load = fields.Integer(
        string='Current Load',
        compute='_compute_current_load',
        help='Current number of parcels in hub'
    )
    load_percentage = fields.Float(
        string='Load %',
        compute='_compute_load_percentage',
        help='Current load as percentage of max capacity'
    )

    # Operations
    operating_hours_start = fields.Float(
        string='Opening Time',
        default=8.0,
        help='Operating hours start (24-hour format)'
    )
    operating_hours_end = fields.Float(
        string='Closing Time',
        default=20.0,
        help='Operating hours end (24-hour format)'
    )
    is_active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True
    )

    # Relations
    manager_id = fields.Many2one(
        'res.users',
        string='Hub Manager',
        tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        help='External partner if this is a partner hub',
        ondelete='restrict'
    )

    # Stats (computed)
    parcel_count = fields.Integer(
        string='Parcel Count',
        compute='_compute_parcel_count',
        help='Number of parcels currently in this hub'
    )
    active_job_count = fields.Integer(
        string='Active Jobs',
        compute='_compute_active_job_count',
        help='Number of active jobs from this hub'
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    # Image
    image = fields.Binary(
        string='Hub Image',
        attachment=True
    )

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code, company_id)', 'Hub code must be unique per company!')
    ]

    @api.depends('max_capacity')
    def _compute_current_load(self):
        """Calculate current load based on parcels in hub"""
        # This is a placeholder - you would need to add a hub_id field to parcels
        # or track parcel movements through hubs
        for record in self:
            # For now, just set to 0
            # In a real implementation, you'd count parcels with current_hub_id = record.id
            record.current_load = 0

    @api.depends('current_load', 'max_capacity')
    def _compute_load_percentage(self):
        """Calculate load percentage"""
        for record in self:
            if record.max_capacity > 0:
                record.load_percentage = (record.current_load / record.max_capacity) * 100
            else:
                record.load_percentage = 0.0

    def _compute_parcel_count(self):
        """Compute parcel count"""
        # Placeholder implementation
        for record in self:
            record.parcel_count = 0

    def _compute_active_job_count(self):
        """Compute active job count"""
        # Placeholder implementation
        for record in self:
            record.active_job_count = 0

    def action_view_parcels(self):
        """Smart button to view parcels in hub"""
        self.ensure_one()
        return {
            'name': _('Parcels in Hub'),
            'type': 'ir.actions.act_window',
            'res_model': 'routy.parcel',
            'view_mode': 'tree,form',
            'domain': [],  # Add appropriate domain when hub tracking is implemented
            'context': {}
        }

    def action_view_jobs(self):
        """Smart button to view jobs from hub"""
        self.ensure_one()
        return {
            'name': _('Hub Jobs'),
            'type': 'ir.actions.act_window',
            'res_model': 'routy.job',
            'view_mode': 'tree,form',
            'domain': [],  # Add appropriate domain when hub tracking is implemented
            'context': {}
        }

    @api.constrains('latitude', 'longitude')
    def _check_coordinates(self):
        """Validate GPS coordinates"""
        for record in self:
            if record.latitude and not (-90 <= record.latitude <= 90):
                raise ValidationError(_('Latitude must be between -90 and 90'))
            if record.longitude and not (-180 <= record.longitude <= 180):
                raise ValidationError(_('Longitude must be between -180 and 180'))

    @api.constrains('operating_hours_start', 'operating_hours_end')
    def _check_operating_hours(self):
        """Validate operating hours"""
        for record in self:
            if not (0 <= record.operating_hours_start < 24):
                raise ValidationError(_('Opening time must be between 0 and 24'))
            if not (0 <= record.operating_hours_end <= 24):
                raise ValidationError(_('Closing time must be between 0 and 24'))
            if record.operating_hours_start >= record.operating_hours_end:
                raise ValidationError(_('Opening time must be before closing time'))

    @api.constrains('max_capacity')
    def _check_max_capacity(self):
        """Validate max capacity"""
        for record in self:
            if record.max_capacity < 0:
                raise ValidationError(_('Max capacity cannot be negative'))
