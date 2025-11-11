# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Incident(models.Model):
    _name = 'routy.incident'
    _description = 'Incident Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'reported_at desc, create_date desc'

    # Basic Information
    name = fields.Char(
        string='Incident Reference',
        required=True,
        readonly=True,
        copy=False,
        default='New',
        tracking=True,
        index=True
    )
    incident_type = fields.Selection([
        ('delay', 'Delay'),
        ('damage', 'Damage'),
        ('loss', 'Loss'),
        ('accident', 'Accident'),
        ('customer_complaint', 'Customer Complaint'),
        ('theft', 'Theft'),
        ('vehicle_breakdown', 'Vehicle Breakdown'),
        ('other', 'Other')
    ], string='Incident Type', required=True, tracking=True, index=True)

    # Related Records
    service_request_id = fields.Many2one(
        'routy.service_request',
        string='Service Request',
        tracking=True,
        index=True
    )
    parcel_id = fields.Many2one(
        'routy.parcel',
        string='Parcel',
        tracking=True,
        index=True
    )
    job_id = fields.Many2one(
        'routy.job',
        string='Job',
        tracking=True,
        index=True
    )
    driver_id = fields.Many2one(
        'res.users',
        string='Driver',
        tracking=True,
        index=True
    )
    customer_id = fields.Many2one(
        'res.partner',
        related='service_request_id.customer_id',
        string='Customer',
        store=True
    )

    # Details
    title = fields.Char(
        string='Incident Title',
        required=True
    )
    description = fields.Text(
        string='Description',
        required=True,
        help='Detailed description of the incident'
    )
    reported_by_id = fields.Many2one(
        'res.users',
        string='Reported By',
        default=lambda self: self.env.user,
        required=True,
        tracking=True
    )
    reported_at = fields.Datetime(
        string='Reported At',
        default=fields.Datetime.now,
        required=True,
        tracking=True
    )

    # Location
    incident_location = fields.Text(string='Incident Location')
    incident_lat = fields.Float(string='Latitude', digits=(10, 7))
    incident_lng = fields.Float(string='Longitude', digits=(10, 7))

    # Severity
    severity = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Severity', default='medium', required=True, tracking=True)

    # Priority
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Important'),
        ('2', 'Urgent'),
        ('3', 'Very Urgent')
    ], string='Priority', default='0', tracking=True)

    # Resolution
    state = fields.Selection([
        ('reported', 'Reported'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ], string='Status', default='reported', required=True, tracking=True, index=True)

    resolution_notes = fields.Text(
        string='Resolution Notes',
        help='Description of how the incident was resolved'
    )
    resolved_by_id = fields.Many2one(
        'res.users',
        string='Resolved By',
        readonly=True,
        tracking=True
    )
    resolved_at = fields.Datetime(
        string='Resolved At',
        readonly=True,
        tracking=True
    )
    closed_at = fields.Datetime(
        string='Closed At',
        readonly=True
    )

    # Impact
    financial_impact = fields.Monetary(
        string='Financial Impact',
        currency_field='currency_id',
        help='Estimated or actual financial cost of the incident'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    # Attachments
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Attachments',
        help='Photos, documents related to the incident'
    )
    attachment_count = fields.Integer(
        string='Attachment Count',
        compute='_compute_attachment_count'
    )

    # Action Taken
    action_taken = fields.Text(
        string='Action Taken',
        help='Description of actions taken to address the incident'
    )
    preventive_measures = fields.Text(
        string='Preventive Measures',
        help='Measures to prevent similar incidents in the future'
    )

    # Tags
    tag_ids = fields.Many2many(
        'routy.incident.tag',
        string='Tags'
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        """Compute attachment count"""
        for record in self:
            record.attachment_count = len(record.attachment_ids)

    @api.model
    def create(self, vals):
        """Override create to generate sequence"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'routy.incident'
            ) or 'New'
        return super(Incident, self).create(vals)

    def action_investigate(self):
        """Move incident to investigating state"""
        for record in self:
            if record.state != 'reported':
                raise UserError(_('Only reported incidents can be moved to investigating.'))
            record.write({'state': 'investigating'})
        return True

    def action_resolve(self):
        """Mark incident as resolved"""
        for record in self:
            if record.state not in ['reported', 'investigating']:
                raise UserError(_('Only reported or investigating incidents can be resolved.'))
            if not record.resolution_notes:
                raise UserError(_('Please provide resolution notes before resolving.'))
            record.write({
                'state': 'resolved',
                'resolved_at': fields.Datetime.now(),
                'resolved_by_id': self.env.user.id
            })
        return True

    def action_close(self):
        """Close the incident"""
        for record in self:
            if record.state != 'resolved':
                raise UserError(_('Only resolved incidents can be closed.'))
            record.write({
                'state': 'closed',
                'closed_at': fields.Datetime.now()
            })
        return True

    def action_reopen(self):
        """Reopen a closed incident"""
        for record in self:
            if record.state not in ['resolved', 'closed']:
                raise UserError(_('Only resolved or closed incidents can be reopened.'))
            record.write({'state': 'investigating'})
        return True

    def action_view_attachments(self):
        """Smart button to view attachments"""
        self.ensure_one()
        return {
            'name': _('Attachments'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.attachment_ids.ids)],
            'context': {'default_res_model': self._name, 'default_res_id': self.id}
        }


class IncidentTag(models.Model):
    _name = 'routy.incident.tag'
    _description = 'Incident Tag'
    _order = 'name'

    name = fields.Char(string='Tag Name', required=True, translate=True)
    color = fields.Integer(string='Color Index')

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'Tag name must be unique!')
    ]
