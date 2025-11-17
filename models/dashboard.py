# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime, timedelta


class RoutyDashboard(models.Model):
    _name = 'routy.dashboard'
    _description = 'Routy Dashboard'

    name = fields.Char(string='Dashboard', default='Routy Dashboard')

    @api.model
    def get_dashboard_data(self):
        """Get dashboard statistics"""
        today = fields.Date.today()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # Today's statistics
        today_requests = self.env['routy.service_request'].search_count([
            ('create_date', '>=', fields.Datetime.to_string(datetime.combine(today, datetime.min.time())))
        ])

        today_deliveries = self.env['routy.parcel'].search_count([
            ('state', '=', 'delivered'),
            ('delivered_at', '>=', fields.Datetime.to_string(datetime.combine(today, datetime.min.time())))
        ])

        # Active drivers
        active_drivers = self.env['routy.job'].search([
            ('state', 'in', ['in_progress', 'accepted'])
        ]).mapped('driver_id')

        # Revenue (today)
        today_revenue = sum(self.env['routy.service_request'].search([
            ('state', '=', 'delivered'),
            ('actual_delivery_date', '>=', fields.Datetime.to_string(datetime.combine(today, datetime.min.time())))
        ]).mapped('service_fee'))

        # Pending parcels
        pending_parcels = self.env['routy.parcel'].search_count([
            ('state', 'in', ['pending', 'picked', 'in_transit', 'out_for_delivery'])
        ])

        # Success rate (this week)
        week_total = self.env['routy.service_request'].search_count([
            ('create_date', '>=', fields.Datetime.to_string(datetime.combine(week_ago, datetime.min.time())))
        ])
        week_delivered = self.env['routy.service_request'].search_count([
            ('state', '=', 'delivered'),
            ('create_date', '>=', fields.Datetime.to_string(datetime.combine(week_ago, datetime.min.time())))
        ])
        success_rate = (week_delivered / week_total * 100) if week_total > 0 else 0

        # Incidents (open)
        open_incidents = self.env['routy.incident'].search_count([
            ('state', 'in', ['new', 'assigned', 'in_progress'])
        ])

        # Chart data - Last 7 days deliveries
        chart_data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_start = datetime.combine(day, datetime.min.time())
            day_end = datetime.combine(day, datetime.max.time())

            count = self.env['routy.parcel'].search_count([
                ('state', '=', 'delivered'),
                ('delivered_at', '>=', fields.Datetime.to_string(day_start)),
                ('delivered_at', '<=', fields.Datetime.to_string(day_end))
            ])

            chart_data.append({
                'date': day.strftime('%Y-%m-%d'),
                'label': day.strftime('%a'),
                'count': count
            })

        # Top drivers (this month)
        jobs_by_driver = {}
        completed_jobs = self.env['routy.job'].search([
            ('state', '=', 'completed'),
            ('completed_at', '>=', fields.Datetime.to_string(datetime.combine(month_ago, datetime.min.time())))
        ])

        for job in completed_jobs:
            driver_name = job.driver_id.name
            if driver_name not in jobs_by_driver:
                jobs_by_driver[driver_name] = 0
            jobs_by_driver[driver_name] += 1

        top_drivers = sorted(jobs_by_driver.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            'today_requests': today_requests,
            'today_deliveries': today_deliveries,
            'active_drivers': len(active_drivers),
            'today_revenue': today_revenue,
            'pending_parcels': pending_parcels,
            'success_rate': round(success_rate, 1),
            'open_incidents': open_incidents,
            'chart_data': chart_data,
            'top_drivers': [{'name': name, 'count': count} for name, count in top_drivers],
            'currency_symbol': self.env.company.currency_id.symbol,
        }
