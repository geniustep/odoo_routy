# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class Job(models.Model):
    _name = 'routy.job'
    _description = 'Driver Job/Task'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_time desc, create_date desc'

    # Basic Information
    name = fields.Char(
        string='Job Reference',
        required=True,
        readonly=True,
        copy=False,
        default='New',
        tracking=True,
        index=True
    )
    job_type = fields.Selection([
        ('pickup', 'Pickup'),
        ('delivery', 'Delivery')
    ], string='Job Type', required=True, tracking=True)

    service_request_id = fields.Many2one(
        'routy.service_request',
        string='Service Request',
        required=True,
        ondelete='cascade',
        tracking=True,
        index=True
    )
    driver_id = fields.Many2one(
        'res.users',
        string='Driver',
        required=True,
        domain="[('groups_id', 'in', [%(routy.group_driver)d])]",
        tracking=True,
        index=True
    )

    # Location
    location_address = fields.Text(
        string='Location Address',
        required=True
    )
    location_lat = fields.Float(
        string='Latitude',
        digits=(10, 7)
    )
    location_lng = fields.Float(
        string='Longitude',
        digits=(10, 7)
    )
    contact_name = fields.Char(string='Contact Name')
    contact_phone = fields.Char(string='Contact Phone')

    # Status
    state = fields.Selection([
        ('assigned', 'Assigned'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='assigned', required=True, tracking=True)

    # Timestamps
    scheduled_time = fields.Datetime(
        string='Scheduled Time',
        tracking=True
    )
    started_at = fields.Datetime(
        string='Started At',
        readonly=True
    )
    completed_at = fields.Datetime(
        string='Completed At',
        readonly=True
    )
    duration = fields.Float(
        string='Duration (Hours)',
        compute='_compute_duration',
        store=True,
        help='Duration from start to completion'
    )

    # Relations
    gps_log_ids = fields.One2many(
        'routy.gps.log',
        'job_id',
        string='GPS Logs'
    )
    gps_log_count = fields.Integer(
        string='GPS Log Count',
        compute='_compute_gps_log_count'
    )
    route_plan_id = fields.Many2one(
        'routy.route_plan',
        string='Route Plan',
        index=True
    )
    parcel_ids = fields.Many2many(
        'routy.parcel',
        string='Parcels',
        help='Parcels associated with this job'
    )
    parcel_count = fields.Integer(
        string='Parcel Count',
        compute='_compute_parcel_count'
    )

    # Notes
    notes = fields.Text(string='Notes')
    failure_reason = fields.Text(
        string='Failure Reason',
        help='Reason for job failure'
    )

    # Related fields
    customer_id = fields.Many2one(
        'res.partner',
        related='service_request_id.customer_id',
        string='Customer',
        store=True
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        related='service_request_id.company_id',
        string='Company',
        store=True
    )

    @api.depends('gps_log_ids')
    def _compute_gps_log_count(self):
        """Compute GPS log count"""
        for record in self:
            record.gps_log_count = len(record.gps_log_ids)

    @api.depends('parcel_ids')
    def _compute_parcel_count(self):
        """Compute parcel count"""
        for record in self:
            record.parcel_count = len(record.parcel_ids)

    @api.depends('started_at', 'completed_at')
    def _compute_duration(self):
        """Calculate job duration"""
        for record in self:
            if record.started_at and record.completed_at:
                delta = record.completed_at - record.started_at
                record.duration = delta.total_seconds() / 3600.0  # Convert to hours
            else:
                record.duration = 0.0

    @api.model
    def create(self, vals):
        """Override create to generate sequence"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'routy.job'
            ) or 'New'
        return super(Job, self).create(vals)

    @api.onchange('service_request_id', 'job_type')
    def _onchange_service_request_job_type(self):
        """Set location based on job type"""
        if self.service_request_id and self.job_type:
            sr = self.service_request_id
            if self.job_type == 'pickup':
                self.location_address = sr.pickup_address
                self.location_lat = sr.pickup_lat
                self.location_lng = sr.pickup_lng
                self.contact_name = sr.pickup_contact
                self.contact_phone = sr.pickup_phone
            elif self.job_type == 'delivery':
                self.location_address = sr.delivery_address
                self.location_lat = sr.delivery_lat
                self.location_lng = sr.delivery_lng
                self.contact_name = sr.delivery_contact
                self.contact_phone = sr.delivery_phone

    def action_accept(self):
        """Driver accepts the job"""
        for record in self:
            if record.state != 'assigned':
                raise UserError(_('Only assigned jobs can be accepted.'))
            record.write({'state': 'accepted'})
        return True

    def action_start(self):
        """Start the job"""
        for record in self:
            if record.state not in ['accepted', 'assigned']:
                raise UserError(_('Only accepted or assigned jobs can be started.'))
            record.write({
                'state': 'in_progress',
                'started_at': fields.Datetime.now()
            })
            # Update service request state
            if record.service_request_id.state == 'assigned':
                record.service_request_id.write({'state': 'in_progress'})
        return True

    def action_complete(self):
        """Complete the job"""
        for record in self:
            if record.state != 'in_progress':
                raise UserError(_('Only in-progress jobs can be completed.'))

            # Update parcels
            if record.job_type == 'pickup':
                record.parcel_ids.action_mark_picked()
                record.service_request_id.write({
                    'actual_pickup_date': fields.Datetime.now()
                })
            elif record.job_type == 'delivery':
                # Check if all parcels have POD
                parcels_without_pod = record.parcel_ids.filtered(
                    lambda p: not p.pod_signature and not p.pod_photo
                )
                if parcels_without_pod:
                    raise UserError(_(
                        'Please provide proof of delivery for all parcels before completing the job.'
                    ))

            record.write({
                'state': 'completed',
                'completed_at': fields.Datetime.now()
            })
        return True

    def action_fail(self):
        """Mark job as failed"""
        for record in self:
            if record.state not in ['in_progress', 'accepted']:
                raise UserError(_('Only accepted or in-progress jobs can be marked as failed.'))
            if not record.failure_reason:
                raise UserError(_('Please provide a failure reason.'))

            record.write({
                'state': 'failed',
                'completed_at': fields.Datetime.now()
            })
            # Mark parcels as failed
            if record.job_type == 'delivery':
                record.parcel_ids.write({'state': 'failed'})
        return True

    def action_view_gps_logs(self):
        """Smart button to view GPS logs"""
        self.ensure_one()
        return {
            'name': _('GPS Logs'),
            'type': 'ir.actions.act_window',
            'res_model': 'routy.gps.log',
            'view_mode': 'tree,graph',
            'domain': [('job_id', '=', self.id)],
            'context': {'default_job_id': self.id}
        }

    @api.constrains('location_lat', 'location_lng')
    def _check_coordinates(self):
        """Validate GPS coordinates"""
        for record in self:
            if record.location_lat and not (-90 <= record.location_lat <= 90):
                raise ValidationError(_('Latitude must be between -90 and 90'))
            if record.location_lng and not (-180 <= record.location_lng <= 180):
                raise ValidationError(_('Longitude must be between -180 and 180'))
