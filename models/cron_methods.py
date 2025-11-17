# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class GPSLog(models.Model):
    _inherit = 'routy.gps.log'

    @api.model
    def _cron_clean_old_logs(self):
        """Clean GPS logs older than 90 days"""
        try:
            days_to_keep = 90
            cutoff_date = fields.Datetime.now() - timedelta(days=days_to_keep)

            old_logs = self.search([
                ('timestamp', '<', cutoff_date)
            ])

            count = len(old_logs)
            old_logs.unlink()

            _logger.info(f'Cleaned {count} GPS logs older than {days_to_keep} days')
        except Exception as e:
            _logger.error(f'Error cleaning old GPS logs: {str(e)}')


class ServiceRequest(models.Model):
    _inherit = 'routy.service_request'

    @api.model
    def _cron_check_delayed_requests(self):
        """Check and flag delayed service requests"""
        try:
            now = fields.Datetime.now()

            # Find requests with past scheduled delivery date but not delivered
            delayed_requests = self.search([
                ('scheduled_delivery_date', '<', now),
                ('state', 'in', ['confirmed', 'assigned', 'in_progress']),
            ])

            for request in delayed_requests:
                # Create incident if not exists
                incident_exists = self.env['routy.incident'].search_count([
                    ('service_request_id', '=', request.id),
                    ('incident_type', '=', 'delay'),
                    ('state', 'in', ['new', 'assigned', 'in_progress'])
                ])

                if not incident_exists:
                    self.env['routy.incident'].create({
                        'title': f'Delayed Delivery - {request.name}',
                        'incident_type': 'delay',
                        'priority': 'high',
                        'description': f'Service request {request.name} is delayed. '
                                     f'Scheduled delivery was {request.scheduled_delivery_date}',
                        'service_request_id': request.id,
                        'state': 'new',
                    })

            _logger.info(f'Checked delayed requests: {len(delayed_requests)} found')
        except Exception as e:
            _logger.error(f'Error checking delayed requests: {str(e)}')

    @api.model
    def _cron_send_daily_summary(self):
        """Send daily summary email to managers"""
        try:
            today = fields.Date.today()
            today_start = datetime.combine(today, datetime.min.time())

            # Get statistics
            total_requests = self.search_count([
                ('create_date', '>=', fields.Datetime.to_string(today_start))
            ])

            delivered = self.search_count([
                ('state', '=', 'delivered'),
                ('actual_delivery_date', '>=', fields.Datetime.to_string(today_start))
            ])

            pending = self.search_count([
                ('state', 'in', ['confirmed', 'assigned', 'in_progress'])
            ])

            # Send email to managers
            managers = self.env.ref('routy.group_manager').users

            for manager in managers:
                if manager.email:
                    # You can create email template or send directly
                    _logger.info(f'Daily summary: {total_requests} requests, '
                               f'{delivered} delivered, {pending} pending')

        except Exception as e:
            _logger.error(f'Error sending daily summary: {str(e)}')


class Job(models.Model):
    _inherit = 'routy.job'

    @api.model
    def _cron_send_driver_reminders(self):
        """Send reminders to drivers for jobs scheduled in next 2 hours"""
        try:
            now = fields.Datetime.now()
            two_hours_later = now + timedelta(hours=2)

            upcoming_jobs = self.search([
                ('scheduled_time', '>=', now),
                ('scheduled_time', '<=', two_hours_later),
                ('state', '=', 'assigned'),
            ])

            for job in upcoming_jobs:
                # Send notification/email to driver
                if job.driver_id:
                    job.message_post(
                        body=f'Reminder: You have a {job.job_type} job scheduled at '
                             f'{job.scheduled_time.strftime("%H:%M")} - '
                             f'{job.location_address}',
                        subject='Job Reminder',
                        message_type='notification',
                        subtype_xmlid='mail.mt_comment',
                        partner_ids=[job.driver_id.partner_id.id]
                    )

            _logger.info(f'Sent reminders for {len(upcoming_jobs)} upcoming jobs')
        except Exception as e:
            _logger.error(f'Error sending driver reminders: {str(e)}')


class Incident(models.Model):
    _inherit = 'routy.incident'

    @api.model
    def _cron_auto_close_old_incidents(self):
        """Auto-close incidents resolved more than 30 days ago"""
        try:
            days_threshold = 30
            cutoff_date = fields.Datetime.now() - timedelta(days=days_threshold)

            old_incidents = self.search([
                ('state', '=', 'resolved'),
                ('write_date', '<', cutoff_date)
            ])

            count = len(old_incidents)
            old_incidents.write({'state': 'closed'})

            _logger.info(f'Auto-closed {count} old incidents')
        except Exception as e:
            _logger.error(f'Error auto-closing incidents: {str(e)}')
