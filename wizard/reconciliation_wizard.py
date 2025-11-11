# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ReconciliationWizard(models.TransientModel):
    _name = 'routy.reconciliation.wizard'
    _description = 'Payment Reconciliation Wizard'

    driver_id = fields.Many2one(
        'res.users',
        string='Driver',
        required=True,
        domain="[('groups_id', 'in', [%(routy.group_driver)d])]"
    )
    date = fields.Date(
        string='Date',
        default=fields.Date.context_today,
        required=True
    )
    payment_record_ids = fields.Many2many(
        'routy.payment_record',
        string='Payment Records',
        domain="[('driver_id', '=', driver_id), ('state', '=', 'collected')]"
    )
    total_expected = fields.Monetary(
        string='Total Expected',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id'
    )
    total_collected = fields.Monetary(
        string='Total Collected',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id'
    )
    difference = fields.Monetary(
        string='Difference',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
        help='Positive means excess, negative means shortage'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )
    notes = fields.Text(string='Reconciliation Notes')

    @api.depends('payment_record_ids', 'payment_record_ids.expected_amount', 'payment_record_ids.amount')
    def _compute_totals(self):
        """Calculate totals and difference"""
        for record in self:
            record.total_expected = sum(record.payment_record_ids.mapped('expected_amount'))
            record.total_collected = sum(record.payment_record_ids.mapped('amount'))
            record.difference = record.total_collected - record.total_expected

    @api.onchange('driver_id', 'date')
    def _onchange_driver_date(self):
        """Auto-load payment records for driver and date"""
        if self.driver_id and self.date:
            # Find collected but not reconciled payments for this driver on this date
            payments = self.env['routy.payment_record'].search([
                ('driver_id', '=', self.driver_id.id),
                ('state', '=', 'collected'),
                ('collected_at', '>=', self.date.strftime('%Y-%m-%d 00:00:00')),
                ('collected_at', '<=', self.date.strftime('%Y-%m-%d 23:59:59')),
            ])
            self.payment_record_ids = [(6, 0, payments.ids)]

    def action_reconcile(self):
        """Reconcile the selected payments"""
        self.ensure_one()

        if not self.payment_record_ids:
            raise UserError(_('Please select at least one payment record to reconcile.'))

        # Mark all payments as reconciled
        self.payment_record_ids.write({
            'state': 'reconciled',
            'reconciled_at': fields.Datetime.now(),
            'reconciled_by_id': self.env.user.id,
            'reconciliation_notes': self.notes,
        })

        # Create notification
        message = _('Reconciled %d payment records for driver %s.\n') % (
            len(self.payment_record_ids),
            self.driver_id.name
        )
        message += _('Total Expected: %.2f\n') % self.total_expected
        message += _('Total Collected: %.2f\n') % self.total_collected

        if self.difference > 0:
            message += _('Excess: %.2f') % self.difference
        elif self.difference < 0:
            message += _('Shortage: %.2f') % abs(self.difference)
        else:
            message += _('Balanced: No difference')

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': message,
                'type': 'success' if abs(self.difference) < 0.01 else 'warning',
                'sticky': True,
            }
        }

    def action_preview(self):
        """Preview reconciliation details"""
        self.ensure_one()
        return {
            'name': _('Reconciliation Preview'),
            'type': 'ir.actions.act_window',
            'res_model': 'routy.payment_record',
            'view_mode': 'list',
            'domain': [('id', 'in', self.payment_record_ids.ids)],
            'target': 'new',
        }
