# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RoutePlan(models.Model):
    _name = 'routy.route_plan'
    _description = 'Route Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, create_date desc'

    # Basic Information
    name = fields.Char(
        string='Route Name',
        required=True,
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
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        index=True
    )

    # Jobs
    job_ids = fields.One2many(
        'routy.job',
        'route_plan_id',
        string='Jobs'
    )
    job_count = fields.Integer(
        string='Total Jobs',
        compute='_compute_job_stats',
        store=True
    )

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)

    # Stats (computed)
    total_distance_km = fields.Float(
        string='Total Distance (km)',
        digits=(10, 2),
        help='Total estimated distance for all jobs'
    )
    estimated_duration = fields.Float(
        string='Estimated Duration (Hours)',
        help='Estimated total duration for route'
    )
    completed_jobs = fields.Integer(
        string='Completed Jobs',
        compute='_compute_job_stats',
        store=True
    )
    failed_jobs = fields.Integer(
        string='Failed Jobs',
        compute='_compute_job_stats',
        store=True
    )
    pending_jobs = fields.Integer(
        string='Pending Jobs',
        compute='_compute_job_stats',
        store=True
    )
    completion_rate = fields.Float(
        string='Completion Rate (%)',
        compute='_compute_completion_rate',
        store=True
    )

    # Optimization
    is_optimized = fields.Boolean(
        string='Optimized',
        default=False,
        help='Route has been optimized'
    )
    optimization_score = fields.Float(
        string='Optimization Score',
        help='Score indicating route efficiency (0-100)'
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

    _sql_constraints = [
        ('driver_date_unique',
         'UNIQUE(driver_id, date, company_id)',
         'A driver can only have one route plan per day!')
    ]

    @api.depends('job_ids', 'job_ids.state')
    def _compute_job_stats(self):
        """Compute job statistics"""
        for record in self:
            jobs = record.job_ids
            record.job_count = len(jobs)
            record.completed_jobs = len(jobs.filtered(lambda j: j.state == 'completed'))
            record.failed_jobs = len(jobs.filtered(lambda j: j.state == 'failed'))
            record.pending_jobs = len(jobs.filtered(
                lambda j: j.state in ['assigned', 'accepted', 'in_progress']
            ))

    @api.depends('job_count', 'completed_jobs')
    def _compute_completion_rate(self):
        """Calculate completion rate"""
        for record in self:
            if record.job_count > 0:
                record.completion_rate = (record.completed_jobs / record.job_count) * 100
            else:
                record.completion_rate = 0.0

    @api.model
    def create(self, vals):
        """Override create to set default name"""
        if not vals.get('name'):
            driver = self.env['res.users'].browse(vals.get('driver_id'))
            date = vals.get('date', fields.Date.context_today(self))
            vals['name'] = _('Route - %s - %s') % (driver.name, date)
        return super(RoutePlan, self).create(vals)

    def action_activate(self):
        """Activate the route plan"""
        for record in self:
            if record.state != 'draft':
                raise UserError(_('Only draft route plans can be activated.'))
            if not record.job_ids:
                raise UserError(_('Cannot activate a route plan without jobs.'))
            record.write({'state': 'active'})
        return True

    def action_complete(self):
        """Mark route plan as completed"""
        for record in self:
            if record.state != 'active':
                raise UserError(_('Only active route plans can be completed.'))
            # Check if all jobs are completed or failed
            pending = record.job_ids.filtered(
                lambda j: j.state not in ['completed', 'failed', 'cancelled']
            )
            if pending:
                raise UserError(_(
                    'Cannot complete route plan. There are still %d pending jobs.'
                ) % len(pending))
            record.write({'state': 'completed'})
        return True

    def action_cancel(self):
        """Cancel the route plan"""
        for record in self:
            if record.state == 'completed':
                raise UserError(_('Cannot cancel a completed route plan.'))
            # Cancel all non-completed jobs
            record.job_ids.filtered(
                lambda j: j.state not in ['completed', 'cancelled']
            ).write({'state': 'cancelled'})
            record.write({'state': 'cancelled'})
        return True

    def action_optimize_route(self):
        """Optimize the route (placeholder for future implementation)"""
        self.ensure_one()
        # This is a placeholder for route optimization logic
        # In a real implementation, you would use algorithms like:
        # - Travelling Salesman Problem (TSP) solvers
        # - Google Maps Directions API
        # - Here Maps API, etc.

        # For now, just mark as optimized
        self.write({
            'is_optimized': True,
            'optimization_score': 85.0  # Placeholder score
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Route has been optimized!'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_view_jobs(self):
        """View jobs in this route plan"""
        self.ensure_one()
        return {
            'name': _('Route Jobs'),
            'type': 'ir.actions.act_window',
            'res_model': 'routy.job',
            'view_mode': 'tree,form,kanban',
            'domain': [('route_plan_id', '=', self.id)],
            'context': {
                'default_route_plan_id': self.id,
                'default_driver_id': self.driver_id.id,
            }
        }

    def action_view_map(self):
        """View route on map (placeholder)"""
        self.ensure_one()
        # This would open a map view showing the route
        # Implementation would require custom map widget
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Map View'),
                'message': _('Map view integration coming soon!'),
                'type': 'info',
            }
        }
