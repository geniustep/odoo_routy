# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class GPSLog(models.Model):
    _name = 'routy.gps.log'
    _description = 'GPS Tracking Log'
    _order = 'timestamp desc'
    _rec_name = 'timestamp'

    # Relations
    job_id = fields.Many2one(
        'routy.job',
        string='Job',
        required=True,
        ondelete='cascade',
        index=True
    )
    driver_id = fields.Many2one(
        'res.users',
        string='Driver',
        required=True,
        index=True
    )

    # Location
    latitude = fields.Float(
        string='Latitude',
        required=True,
        digits=(10, 7)
    )
    longitude = fields.Float(
        string='Longitude',
        required=True,
        digits=(10, 7)
    )

    # Accuracy & Speed
    accuracy = fields.Float(
        string='Accuracy (m)',
        help='GPS accuracy in meters'
    )
    speed = fields.Float(
        string='Speed (km/h)',
        help='Speed in kilometers per hour'
    )
    heading = fields.Float(
        string='Heading (degrees)',
        help='Direction in degrees (0-360)'
    )
    altitude = fields.Float(
        string='Altitude (m)',
        help='Altitude in meters above sea level'
    )

    # Timestamp
    timestamp = fields.Datetime(
        string='Timestamp',
        required=True,
        default=fields.Datetime.now,
        index=True
    )
    date = fields.Date(
        string='Date',
        compute='_compute_date',
        store=True,
        index=True,
        help='Date extracted from timestamp for faster queries'
    )

    # Battery & Network
    battery_level = fields.Float(
        string='Battery Level (%)',
        help='Device battery level percentage'
    )
    network_type = fields.Char(
        string='Network Type',
        help='Network connection type (WiFi, 4G, etc.)'
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        related='job_id.company_id',
        string='Company',
        store=True
    )

    @api.depends('timestamp')
    def _compute_date(self):
        """Extract date from timestamp for indexing"""
        for record in self:
            if record.timestamp:
                record.date = record.timestamp.date()
            else:
                record.date = False

    @api.constrains('latitude', 'longitude')
    def _check_coordinates(self):
        """Validate GPS coordinates"""
        for record in self:
            if not (-90 <= record.latitude <= 90):
                raise ValidationError(_('Latitude must be between -90 and 90'))
            if not (-180 <= record.longitude <= 180):
                raise ValidationError(_('Longitude must be between -180 and 180'))

    @api.constrains('heading')
    def _check_heading(self):
        """Validate heading"""
        for record in self:
            if record.heading and not (0 <= record.heading <= 360):
                raise ValidationError(_('Heading must be between 0 and 360 degrees'))

    @api.constrains('speed')
    def _check_speed(self):
        """Validate speed"""
        for record in self:
            if record.speed and record.speed < 0:
                raise ValidationError(_('Speed cannot be negative'))

    @api.constrains('battery_level')
    def _check_battery(self):
        """Validate battery level"""
        for record in self:
            if record.battery_level and not (0 <= record.battery_level <= 100):
                raise ValidationError(_('Battery level must be between 0 and 100'))

    @api.model
    def create_gps_log(self, vals):
        """
        Helper method for API to create GPS log
        Expected vals: {
            'job_id': int,
            'driver_id': int,
            'latitude': float,
            'longitude': float,
            'accuracy': float (optional),
            'speed': float (optional),
            'heading': float (optional),
            'altitude': float (optional),
            'battery_level': float (optional),
            'network_type': str (optional),
        }
        """
        return self.create(vals)

    @api.model
    def get_job_track(self, job_id):
        """Get all GPS logs for a specific job"""
        logs = self.search([
            ('job_id', '=', job_id)
        ], order='timestamp asc')

        return [{
            'lat': log.latitude,
            'lng': log.longitude,
            'timestamp': log.timestamp.isoformat(),
            'speed': log.speed,
            'heading': log.heading,
        } for log in logs]

    @api.model
    def get_driver_current_location(self, driver_id):
        """Get the most recent GPS location for a driver"""
        log = self.search([
            ('driver_id', '=', driver_id)
        ], order='timestamp desc', limit=1)

        if log:
            return {
                'lat': log.latitude,
                'lng': log.longitude,
                'timestamp': log.timestamp.isoformat(),
                'speed': log.speed,
                'accuracy': log.accuracy,
            }
        return False
