# Routy - Smart Delivery System

A comprehensive delivery and logistics management system for **Odoo 18 Community Edition**.

## Features

### 🚚 Core Operations
- **Service Request Management**: Complete lifecycle management of delivery requests
- **Parcel Tracking**: Unique tracking numbers with real-time status updates
- **Job Management**: Driver task assignment and tracking
- **Route Planning**: Daily route optimization and calendar scheduling

### 📍 Logistics
- **Hub Management**: Distribution center and warehouse management
- **Linehaul Operations**: Inter-city transport planning and execution
- **GPS Tracking**: Real-time location tracking via mobile API

### 💰 Financial
- **Cash on Delivery (COD)**: COD amount tracking and collection
- **Payment Reconciliation**: Driver payment reconciliation wizards
- **Cost Tracking**: Operational cost management for linehauls

### 📱 Mobile Integration
- RESTful API for driver mobile applications
- GPS location updates
- Digital Proof of Delivery (signature + photo)
- Job status management

### 🛡️ Incident Management
- Incident reporting and tracking
- Severity and priority classification
- Resolution workflow
- Preventive measures documentation

## Models

1. **routy.service_request** - Main service requests
2. **routy.parcel** - Package/parcel tracking
3. **routy.job** - Driver tasks (pickup/delivery)
4. **routy.hub** - Distribution centers
5. **routy.linehaul** - Inter-city transport
6. **routy.route_plan** - Daily route plans
7. **routy.payment_record** - Payment collections
8. **routy.gps_log** - GPS tracking logs
9. **routy.partner_contract** - Partner contracts
10. **routy.incident** - Incident reports

## Security Groups

- **Driver**: View and update assigned jobs, GPS tracking
- **Dispatcher**: Create requests, assign drivers, manage operations
- **Manager**: Full system access and configuration

## Installation

1. Copy the `routy` folder to your Odoo addons directory
2. Update the apps list in Odoo
3. Install the "Routy - Smart Delivery System" module
4. Configure user groups for drivers, dispatchers, and managers

## Mobile API Endpoints

### Authentication
All endpoints require user authentication (`auth='user'`)

### Available Endpoints

- `GET /api/v1/routy/jobs/my` - Get driver's jobs
- `POST /api/v1/routy/jobs/<id>/accept` - Accept a job
- `POST /api/v1/routy/jobs/<id>/start` - Start a job
- `POST /api/v1/routy/jobs/<id>/complete` - Complete a job
- `POST /api/v1/routy/gps/update` - Update GPS location (JSON)
- `POST /api/v1/routy/parcels/<id>/deliver` - Mark parcel as delivered (JSON)
- `GET /api/v1/routy/parcels/<id>` - Get parcel details

## Configuration

### Sequences
The module automatically creates sequences for:
- Service Requests (SR00001)
- Parcels (TRK0000001)
- Jobs (JOB00001)
- Linehauls (LH00001)
- Payment Records (PAY00001)
- Partner Contracts (CONT00001)
- Incidents (INC00001)

## Technical Details

- **Odoo Version**: 18.0
- **License**: LGPL-3
- **Dependencies**: base, mail, contacts
- **Application**: Yes

## Module Structure

```
routy/
├── __init__.py
├── __manifest__.py
├── models/              # 10 models
├── views/               # XML views for all models
├── security/            # Access rights and rules
├── wizard/              # Assign driver & reconciliation wizards
├── controllers/         # Mobile API controllers
├── data/                # Sequences
├── reports/             # Report models (future)
└── static/description/  # Module description
```

## Workflow Examples

### Service Request Workflow
Draft → Confirmed → Assigned → In Progress → Delivered

### Parcel Workflow
Pending → Picked → In Transit → Out for Delivery → Delivered

### Job Workflow
Assigned → Accepted → In Progress → Completed

## Development

### Key Features Implemented:
- ✅ 10 fully functional models
- ✅ Complete CRUD views (List, Form, Kanban, Search)
- ✅ Smart buttons and statusbar workflows
- ✅ Security groups and record rules
- ✅ Wizards for complex operations
- ✅ Mobile API with 7 endpoints
- ✅ GPS tracking integration
- ✅ Proof of Delivery system
- ✅ Payment reconciliation

### Future Enhancements:
- Map view integration
- Advanced route optimization algorithms
- SMS/Email notifications
- Customer portal
- Analytics dashboards
- Integration with shipping carriers

## Support

For issues and questions, please open an issue on the project repository.

## License

LGPL-3

## Author

Your Company

---

**Note**: This module is designed for Odoo 18 Community Edition and follows Odoo development best practices.
