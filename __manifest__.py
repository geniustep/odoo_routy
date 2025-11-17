# -*- coding: utf-8 -*-
{
    'name': 'Routy - Smart Delivery System',
    'version': '18.0.1.0.0',
    'category': 'Operations/Logistics',
    'summary': 'Complete delivery and logistics management system',
    'description': """
        Routy - Smart Delivery System
        ==============================

        A comprehensive delivery management system featuring:

        * Service Request Management
        * Parcel Tracking with POD (Proof of Delivery)
        * Driver Job Assignment & Route Planning
        * Hub & Linehaul Management
        * GPS Tracking & Real-time Monitoring
        * Payment Collection & Reconciliation
        * Partner Contract Management
        * Incident Reporting & Resolution
        * Mobile API for Driver Apps
        * Advanced Analytics & Reports
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'contacts',
    ],
    'data': [
        # Security
        'security/security.xml',
        'security/ir.model.access.csv',

        # Data
        'data/sequences.xml',
        'data/email_templates.xml',
        'data/cron_jobs.xml',

        # Wizards
        'wizard/assign_driver_wizard_views.xml',
        'wizard/reconciliation_wizard_views.xml',

        # Views - Core Models
        'views/service_request_views.xml',
        'views/parcel_views.xml',
        'views/job_views.xml',

        # Views - Logistics
        'views/hub_views.xml',
        'views/linehaul_views.xml',
        'views/route_plan_views.xml',

        # Views - Support
        'views/payment_record_views.xml',
        'views/partner_contract_views.xml',
        'views/incident_views.xml',

        # Dashboard
        'views/dashboard_views.xml',

        # Reports
        'reports/parcel_delivery_note.xml',

        # Menus
        'views/menus.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'routy/static/src/js/dashboard.js',
            'routy/static/src/xml/dashboard.xml',
        ],
    },
    'test': True,
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': ['static/description/icon.png'],
    'external_dependencies': {
        'python': [],
    },
}
