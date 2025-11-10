# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PartnerContract(models.Model):
    _name = 'routy.partner_contract'
    _description = 'Partner Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Basic Information
    name = fields.Char(
        string='Contract Number',
        required=True,
        readonly=True,
        copy=False,
        default='New',
        tracking=True,
        index=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        tracking=True,
        index=True
    )
    partner_type = fields.Selection([
        ('carrier', 'Carrier Company'),
        ('freelancer', 'Freelance Driver'),
        ('hub', 'Hub Partner')
    ], string='Partner Type', required=True, tracking=True)

    # Contract Period
    start_date = fields.Date(
        string='Start Date',
        required=True,
        tracking=True
    )
    end_date = fields.Date(
        string='End Date',
        tracking=True
    )
    is_active = fields.Boolean(
        string='Active',
        compute='_compute_is_active',
        store=True,
        help='Computed based on current date and contract period'
    )

    # Financial Terms
    rate_per_km = fields.Monetary(
        string='Rate per KM',
        currency_field='currency_id',
        help='Payment per kilometer'
    )
    rate_per_delivery = fields.Monetary(
        string='Rate per Delivery',
        currency_field='currency_id',
        help='Fixed payment per delivery'
    )
    minimum_guarantee = fields.Monetary(
        string='Minimum Guarantee',
        currency_field='currency_id',
        help='Minimum monthly payment guarantee'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    # Performance
    sla_target = fields.Float(
        string='SLA Target (%)',
        default=95.0,
        help='Target success rate percentage'
    )
    actual_performance = fields.Float(
        string='Actual Performance (%)',
        compute='_compute_actual_performance',
        help='Calculated performance percentage'
    )
    performance_score = fields.Selection([
        ('excellent', 'Excellent (>95%)'),
        ('good', 'Good (85-95%)'),
        ('average', 'Average (75-85%)'),
        ('poor', 'Poor (<75%)')
    ], string='Performance Score', compute='_compute_performance_score')

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated')
    ], string='Status', default='draft', required=True, tracking=True)

    # Documents
    contract_file = fields.Binary(
        string='Contract Document',
        attachment=True
    )
    contract_filename = fields.Char(string='Filename')

    # Statistics (computed from jobs/deliveries)
    total_deliveries = fields.Integer(
        string='Total Deliveries',
        compute='_compute_statistics'
    )
    successful_deliveries = fields.Integer(
        string='Successful Deliveries',
        compute='_compute_statistics'
    )
    total_distance_km = fields.Float(
        string='Total Distance (km)',
        compute='_compute_statistics',
        digits=(10, 2)
    )

    # Terms & Conditions
    terms = fields.Html(string='Terms & Conditions')
    notes = fields.Text(string='Notes')

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    @api.depends('start_date', 'end_date')
    def _compute_is_active(self):
        """Check if contract is currently active based on dates"""
        today = fields.Date.context_today(self)
        for record in self:
            if record.state != 'active':
                record.is_active = False
            elif record.start_date and record.start_date > today:
                record.is_active = False
            elif record.end_date and record.end_date < today:
                record.is_active = False
            else:
                record.is_active = True

    def _compute_actual_performance(self):
        """Calculate actual performance based on deliveries"""
        # Placeholder - would calculate from actual job data
        for record in self:
            if record.total_deliveries > 0:
                record.actual_performance = (
                    record.successful_deliveries / record.total_deliveries
                ) * 100
            else:
                record.actual_performance = 0.0

    @api.depends('actual_performance')
    def _compute_performance_score(self):
        """Compute performance score category"""
        for record in self:
            if record.actual_performance >= 95:
                record.performance_score = 'excellent'
            elif record.actual_performance >= 85:
                record.performance_score = 'good'
            elif record.actual_performance >= 75:
                record.performance_score = 'average'
            else:
                record.performance_score = 'poor'

    def _compute_statistics(self):
        """Compute delivery statistics"""
        # Placeholder - would query actual job/delivery data
        for record in self:
            record.total_deliveries = 0
            record.successful_deliveries = 0
            record.total_distance_km = 0.0

    @api.model
    def create(self, vals):
        """Override create to generate sequence"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'routy.partner_contract'
            ) or 'New'
        return super(PartnerContract, self).create(vals)

    def action_activate(self):
        """Activate the contract"""
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_('Only draft contracts can be activated.'))
            record.write({'state': 'active'})
        return True

    def action_terminate(self):
        """Terminate the contract"""
        for record in self:
            if record.state not in ['active', 'draft']:
                raise ValidationError(_('Cannot terminate a contract that is not active or draft.'))
            record.write({'state': 'terminated'})
        return True

    def action_view_deliveries(self):
        """Smart button to view partner deliveries"""
        self.ensure_one()
        # This would show jobs/deliveries associated with this partner
        return {
            'name': _('Deliveries'),
            'type': 'ir.actions.act_window',
            'res_model': 'routy.job',
            'view_mode': 'tree,form',
            'domain': [],  # Add appropriate domain based on partner linkage
            'context': {}
        }

    def action_view_performance(self):
        """View performance dashboard"""
        self.ensure_one()
        # Placeholder for performance dashboard
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Performance'),
                'message': _('Performance: %.2f%%') % self.actual_performance,
                'type': 'info',
            }
        }

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Validate contract dates"""
        for record in self:
            if record.start_date and record.end_date:
                if record.start_date > record.end_date:
                    raise ValidationError(_('Start date must be before end date.'))

    @api.constrains('sla_target')
    def _check_sla_target(self):
        """Validate SLA target"""
        for record in self:
            if not (0 <= record.sla_target <= 100):
                raise ValidationError(_('SLA target must be between 0 and 100.'))
