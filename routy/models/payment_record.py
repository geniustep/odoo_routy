# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PaymentRecord(models.Model):
    _name = 'routy.payment_record'
    _description = 'Payment Collection Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Basic Information
    name = fields.Char(
        string='Payment Reference',
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
        tracking=True,
        index=True
    )
    parcel_id = fields.Many2one(
        'routy.parcel',
        string='Parcel',
        tracking=True,
        index=True
    )
    driver_id = fields.Many2one(
        'res.users',
        string='Collecting Driver',
        required=True,
        domain="[('groups_id', 'in', [%(routy.group_driver)d])]",
        tracking=True,
        index=True
    )

    # Payment Details
    amount = fields.Monetary(
        string='Amount',
        currency_field='currency_id',
        required=True,
        tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('wallet', 'E-Wallet'),
        ('bank_transfer', 'Bank Transfer')
    ], string='Payment Method', required=True, default='cash', tracking=True)

    # Status
    state = fields.Selection([
        ('pending', 'Pending'),
        ('collected', 'Collected'),
        ('reconciled', 'Reconciled')
    ], string='Status', default='pending', required=True, tracking=True, index=True)

    # Timestamps
    collected_at = fields.Datetime(
        string='Collected At',
        readonly=True,
        tracking=True
    )
    reconciled_at = fields.Datetime(
        string='Reconciled At',
        readonly=True,
        tracking=True
    )

    # Reconciliation
    expected_amount = fields.Monetary(
        string='Expected Amount',
        currency_field='currency_id',
        help='Expected amount to be collected'
    )
    reconciliation_difference = fields.Monetary(
        string='Difference',
        compute='_compute_reconciliation_difference',
        store=True,
        currency_field='currency_id',
        help='Difference between expected and collected amount'
    )
    reconciled_by_id = fields.Many2one(
        'res.users',
        string='Reconciled By',
        readonly=True
    )
    reconciliation_notes = fields.Text(
        string='Reconciliation Notes'
    )

    # Relations
    customer_id = fields.Many2one(
        'res.partner',
        related='service_request_id.customer_id',
        string='Customer',
        store=True
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    @api.depends('expected_amount', 'amount')
    def _compute_reconciliation_difference(self):
        """Calculate difference between expected and actual amount"""
        for record in self:
            record.reconciliation_difference = record.amount - record.expected_amount

    @api.model
    def create(self, vals):
        """Override create to generate sequence"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'routy.payment_record'
            ) or 'New'
        return super(PaymentRecord, self).create(vals)

    @api.onchange('service_request_id')
    def _onchange_service_request(self):
        """Set expected amount from service request COD"""
        if self.service_request_id:
            self.expected_amount = self.service_request_id.cod_amount
            if not self.amount:
                self.amount = self.service_request_id.cod_amount

    def action_collect(self):
        """Mark payment as collected"""
        for record in self:
            if record.state != 'pending':
                raise UserError(_('Only pending payments can be marked as collected.'))
            if not record.amount:
                raise UserError(_('Please specify the collected amount.'))
            record.write({
                'state': 'collected',
                'collected_at': fields.Datetime.now()
            })
        return True

    def action_reconcile(self):
        """Reconcile the payment"""
        for record in self:
            if record.state != 'collected':
                raise UserError(_('Only collected payments can be reconciled.'))
            record.write({
                'state': 'reconciled',
                'reconciled_at': fields.Datetime.now(),
                'reconciled_by_id': self.env.user.id
            })
        return True

    def action_open_reconciliation_wizard(self):
        """Open reconciliation wizard"""
        return {
            'name': _('Reconcile Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'routy.reconciliation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_payment_record_ids': [(6, 0, self.ids)],
            }
        }
