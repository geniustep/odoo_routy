# -*- coding: utf-8 -*-

import json
import logging
import base64
from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class RoutyMobileAPI(http.Controller):
    """Mobile API for Routy Driver App"""

    def _check_authentication(self):
        """Check if user is authenticated and is a driver"""
        if not request.env.user or request.env.user._is_public():
            return False, {'error': 'Authentication required'}, 401

        # Check if user is a driver
        driver_group = request.env.ref('routy.group_driver')
        if driver_group not in request.env.user.groups_id:
            return False, {'error': 'User is not a driver'}, 403

        return True, None, None

    def _json_response(self, data, status=200):
        """Return JSON response"""
        return Response(
            json.dumps(data),
            status=status,
            mimetype='application/json'
        )

    @http.route('/api/v1/routy/jobs/my', type='http', auth='user', methods=['GET'], csrf=False)
    def get_my_jobs(self, **kwargs):
        """Get jobs assigned to the current driver"""
        auth_ok, error_data, status_code = self._check_authentication()
        if not auth_ok:
            return self._json_response(error_data, status_code)

        try:
            driver_id = request.env.user.id
            state_filter = kwargs.get('state', '')

            domain = [('driver_id', '=', driver_id)]
            if state_filter:
                domain.append(('state', '=', state_filter))

            jobs = request.env['routy.job'].search(domain, order='scheduled_time asc')

            job_list = []
            for job in jobs:
                job_list.append({
                    'id': job.id,
                    'name': job.name,
                    'job_type': job.job_type,
                    'state': job.state,
                    'service_request_id': job.service_request_id.id,
                    'service_request_name': job.service_request_id.name,
                    'customer_name': job.customer_id.name if job.customer_id else '',
                    'location_address': job.location_address,
                    'location_lat': job.location_lat,
                    'location_lng': job.location_lng,
                    'contact_name': job.contact_name,
                    'contact_phone': job.contact_phone,
                    'scheduled_time': job.scheduled_time.isoformat() if job.scheduled_time else None,
                    'parcel_count': job.parcel_count,
                    'notes': job.notes or '',
                })

            return self._json_response({
                'success': True,
                'jobs': job_list,
                'count': len(job_list)
            })

        except Exception as e:
            _logger.error('Error fetching jobs: %s', str(e))
            return self._json_response({'error': str(e)}, 500)

    @http.route('/api/v1/routy/jobs/<int:job_id>/accept', type='http', auth='user', methods=['POST'], csrf=False)
    def accept_job(self, job_id, **kwargs):
        """Accept a job"""
        auth_ok, error_data, status_code = self._check_authentication()
        if not auth_ok:
            return self._json_response(error_data, status_code)

        try:
            job = request.env['routy.job'].browse(job_id)

            if not job.exists():
                return self._json_response({'error': 'Job not found'}, 404)

            if job.driver_id.id != request.env.user.id:
                return self._json_response({'error': 'Not authorized'}, 403)

            job.action_accept()

            return self._json_response({
                'success': True,
                'message': 'Job accepted successfully',
                'job_id': job.id,
                'state': job.state
            })

        except Exception as e:
            _logger.error('Error accepting job: %s', str(e))
            return self._json_response({'error': str(e)}, 500)

    @http.route('/api/v1/routy/jobs/<int:job_id>/start', type='http', auth='user', methods=['POST'], csrf=False)
    def start_job(self, job_id, **kwargs):
        """Start a job"""
        auth_ok, error_data, status_code = self._check_authentication()
        if not auth_ok:
            return self._json_response(error_data, status_code)

        try:
            job = request.env['routy.job'].browse(job_id)

            if not job.exists():
                return self._json_response({'error': 'Job not found'}, 404)

            if job.driver_id.id != request.env.user.id:
                return self._json_response({'error': 'Not authorized'}, 403)

            job.action_start()

            return self._json_response({
                'success': True,
                'message': 'Job started successfully',
                'job_id': job.id,
                'state': job.state,
                'started_at': job.started_at.isoformat() if job.started_at else None
            })

        except Exception as e:
            _logger.error('Error starting job: %s', str(e))
            return self._json_response({'error': str(e)}, 500)

    @http.route('/api/v1/routy/jobs/<int:job_id>/complete', type='http', auth='user', methods=['POST'], csrf=False)
    def complete_job(self, job_id, **kwargs):
        """Complete a job"""
        auth_ok, error_data, status_code = self._check_authentication()
        if not auth_ok:
            return self._json_response(error_data, status_code)

        try:
            job = request.env['routy.job'].browse(job_id)

            if not job.exists():
                return self._json_response({'error': 'Job not found'}, 404)

            if job.driver_id.id != request.env.user.id:
                return self._json_response({'error': 'Not authorized'}, 403)

            job.action_complete()

            return self._json_response({
                'success': True,
                'message': 'Job completed successfully',
                'job_id': job.id,
                'state': job.state
            })

        except Exception as e:
            _logger.error('Error completing job: %s', str(e))
            return self._json_response({'error': str(e)}, 500)

    @http.route('/api/v1/routy/gps/update', type='json', auth='user', methods=['POST'], csrf=False)
    def update_gps(self, **kwargs):
        """Update GPS location for current job"""
        auth_ok, error_data, status_code = self._check_authentication()
        if not auth_ok:
            return error_data

        try:
            data = request.jsonrequest

            required_fields = ['job_id', 'latitude', 'longitude']
            for field in required_fields:
                if field not in data:
                    return {'error': f'Missing required field: {field}'}

            job_id = data.get('job_id')
            job = request.env['routy.job'].browse(job_id)

            if not job.exists():
                return {'error': 'Job not found'}

            if job.driver_id.id != request.env.user.id:
                return {'error': 'Not authorized'}

            # Create GPS log
            gps_log = request.env['routy.gps.log'].create({
                'job_id': job_id,
                'driver_id': request.env.user.id,
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'accuracy': data.get('accuracy', 0),
                'speed': data.get('speed', 0),
                'heading': data.get('heading', 0),
                'altitude': data.get('altitude', 0),
                'battery_level': data.get('battery_level', 0),
                'network_type': data.get('network_type', ''),
            })

            return {
                'success': True,
                'message': 'GPS location updated',
                'log_id': gps_log.id
            }

        except Exception as e:
            _logger.error('Error updating GPS: %s', str(e))
            return {'error': str(e)}

    @http.route('/api/v1/routy/parcels/<int:parcel_id>/deliver', type='json', auth='user', methods=['POST'], csrf=False)
    def deliver_parcel(self, parcel_id, **kwargs):
        """Mark parcel as delivered with POD"""
        auth_ok, error_data, status_code = self._check_authentication()
        if not auth_ok:
            return error_data

        try:
            data = request.jsonrequest

            parcel = request.env['routy.parcel'].browse(parcel_id)

            if not parcel.exists():
                return {'error': 'Parcel not found'}

            if parcel.assigned_driver_id.id != request.env.user.id:
                return {'error': 'Not authorized'}

            # Update parcel with POD
            update_vals = {
                'state': 'delivered',
                'delivered_at': request.env['ir.fields'].Datetime.now(),
                'recipient_name': data.get('recipient_name', ''),
                'pod_notes': data.get('notes', ''),
            }

            # Handle signature (base64)
            if data.get('signature'):
                update_vals['pod_signature'] = base64.b64decode(data['signature'])

            # Handle photo (base64)
            if data.get('photo'):
                update_vals['pod_photo'] = base64.b64decode(data['photo'])

            parcel.write(update_vals)

            return {
                'success': True,
                'message': 'Parcel delivered successfully',
                'parcel_id': parcel.id,
                'tracking_number': parcel.name
            }

        except Exception as e:
            _logger.error('Error delivering parcel: %s', str(e))
            return {'error': str(e)}

    @http.route('/api/v1/routy/parcels/<int:parcel_id>', type='http', auth='user', methods=['GET'], csrf=False)
    def get_parcel_details(self, parcel_id, **kwargs):
        """Get parcel details"""
        auth_ok, error_data, status_code = self._check_authentication()
        if not auth_ok:
            return self._json_response(error_data, status_code)

        try:
            parcel = request.env['routy.parcel'].browse(parcel_id)

            if not parcel.exists():
                return self._json_response({'error': 'Parcel not found'}, 404)

            return self._json_response({
                'success': True,
                'parcel': {
                    'id': parcel.id,
                    'name': parcel.name,
                    'description': parcel.description or '',
                    'weight': parcel.weight,
                    'declared_value': parcel.declared_value,
                    'state': parcel.state,
                    'service_request': parcel.service_request_id.name,
                    'customer': parcel.customer_id.name if parcel.customer_id else '',
                }
            })

        except Exception as e:
            _logger.error('Error fetching parcel: %s', str(e))
            return self._json_response({'error': str(e)}, 500)
