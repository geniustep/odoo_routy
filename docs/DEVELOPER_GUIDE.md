# Routy Developer Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Development Environment Setup](#development-environment-setup)
3. [Project Structure](#project-structure)
4. [Model Development](#model-development)
5. [View Development](#view-development)
6. [Security Implementation](#security-implementation)
7. [API Development](#api-development)
8. [Testing](#testing)
9. [Best Practices](#best-practices)
10. [Common Patterns](#common-patterns)
11. [Troubleshooting](#troubleshooting)

---

## Introduction

Routy is a comprehensive delivery management system built for Odoo 18 Community Edition. This guide will help developers understand the codebase and contribute effectively.

### Technology Stack

- **Framework:** Odoo 18.0
- **Language:** Python 3.10+
- **Database:** PostgreSQL 14+
- **Frontend:** XML views, JavaScript (Odoo framework)
- **License:** LGPL-3

---

## Development Environment Setup

### Prerequisites

```bash
# Install Python 3.10+
sudo apt-get update
sudo apt-get install python3.10 python3.10-dev

# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Install system dependencies
sudo apt-get install libpq-dev libxml2-dev libxslt1-dev \
  libldap2-dev libsasl2-dev libjpeg-dev zlib1g-dev
```

### Odoo Installation

```bash
# Clone Odoo 18
git clone https://github.com/odoo/odoo.git --depth 1 --branch 18.0

# Create virtual environment
python3.10 -m venv odoo-venv
source odoo-venv/bin/activate

# Install Python dependencies
pip install -r odoo/requirements.txt
```

### Routy Module Setup

```bash
# Clone Routy module to addons directory
cd odoo/addons
git clone <routy-repository-url> routy

# Or symlink from development directory
ln -s /path/to/routy /path/to/odoo/addons/routy

# Update module list
./odoo-bin -c odoo.conf -d your_database -u routy

# Install module
./odoo-bin -c odoo.conf -d your_database -i routy
```

### Configuration

Create `odoo.conf`:

```ini
[options]
addons_path = /path/to/odoo/addons,/path/to/custom/addons
admin_passwd = admin
db_host = localhost
db_port = 5432
db_user = odoo
db_password = odoo
http_port = 8069
logfile = /var/log/odoo/odoo.log
log_level = debug
```

---

## Project Structure

```
routy/
├── __init__.py                 # Module initialization
├── __manifest__.py             # Module metadata
├── README.md                   # User documentation
│
├── models/                     # Data models
│   ├── __init__.py
│   ├── service_request.py      # Main service request model
│   ├── parcel.py               # Parcel tracking
│   ├── job.py                  # Driver jobs
│   ├── hub.py                  # Distribution hubs
│   ├── linehaul.py             # Inter-city transport
│   ├── route_plan.py           # Route planning
│   ├── payment_record.py       # Payment tracking
│   ├── gps_log.py              # GPS logs
│   ├── partner_contract.py     # Partner contracts
│   └── incident.py             # Incident management
│
├── views/                      # UI views (XML)
│   ├── service_request_views.xml
│   ├── parcel_views.xml
│   ├── job_views.xml
│   ├── hub_views.xml
│   ├── linehaul_views.xml
│   ├── route_plan_views.xml
│   ├── payment_record_views.xml
│   ├── incident_views.xml
│   └── menus.xml               # Menu structure
│
├── security/                   # Access control
│   ├── security.xml            # Groups and rules
│   └── ir.model.access.csv     # Access rights
│
├── wizard/                     # Transient models
│   ├── __init__.py
│   ├── assign_driver_wizard.py
│   ├── assign_driver_wizard_views.xml
│   ├── reconciliation_wizard.py
│   └── reconciliation_wizard_views.xml
│
├── controllers/                # HTTP controllers
│   ├── __init__.py
│   └── mobile_api.py           # Mobile API endpoints
│
├── data/                       # Data files
│   └── sequences.xml           # Sequence definitions
│
├── reports/                    # Report definitions
│   └── __init__.py
│
├── static/                     # Static assets
│   └── description/
│       └── index.html          # Module description
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_service_request.py
│   ├── test_parcel.py
│   ├── test_job.py
│   └── test_mobile_api.py
│
└── docs/                       # Documentation
    ├── API_DOCUMENTATION.md
    ├── DEVELOPER_GUIDE.md
    └── CONTRIBUTING.md
```

---

## Model Development

### Creating a New Model

```python
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class MyModel(models.Model):
    """Model description"""

    _name = 'routy.my_model'
    _description = 'My Model Description'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Fields
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True,
        index=True,
        help='Model name'
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], string='Status', default='draft', required=True, tracking=True)

    # Relations
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='restrict'
    )

    # Computed fields
    total_amount = fields.Monetary(
        string='Total',
        compute='_compute_total_amount',
        store=True,
        currency_field='currency_id'
    )

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )

    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
        required=True
    )

    # Compute methods
    @api.depends('line_ids.amount')
    def _compute_total_amount(self):
        """Compute total amount from lines"""
        for record in self:
            record.total_amount = sum(record.line_ids.mapped('amount'))

    # CRUD overrides
    @api.model
    def create(self, vals):
        """Override create to add custom logic"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'routy.my_model'
            ) or 'New'
        return super(MyModel, self).create(vals)

    def write(self, vals):
        """Override write to add custom logic"""
        # Add validation before write
        if 'state' in vals:
            self._validate_state_change(vals['state'])
        return super(MyModel, self).write(vals)

    def unlink(self):
        """Override unlink to prevent deletion"""
        if any(rec.state == 'done' for rec in self):
            raise UserError(_('Cannot delete records in Done state.'))
        return super(MyModel, self).unlink()

    # Business logic
    def action_confirm(self):
        """Confirm the record"""
        for record in self:
            if not record.line_ids:
                raise UserError(_('Cannot confirm without lines.'))
            record.write({'state': 'confirmed'})
        return True

    def action_done(self):
        """Mark as done"""
        self.write({'state': 'done'})
        return True

    # Constraints
    @api.constrains('total_amount')
    def _check_total_amount(self):
        """Validate total amount"""
        for record in self:
            if record.total_amount < 0:
                raise ValidationError(_('Total amount cannot be negative.'))

    # Onchange methods
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Update fields when partner changes"""
        if self.partner_id:
            # Auto-fill related fields
            pass
```

### Field Types Reference

```python
# Basic types
name = fields.Char(string='Text', size=100)
description = fields.Text(string='Long Text')
active = fields.Boolean(string='Active', default=True)
sequence = fields.Integer(string='Sequence', default=10)
amount = fields.Float(string='Amount', digits=(10, 2))
price = fields.Monetary(string='Price', currency_field='currency_id')

# Date/Time
date = fields.Date(string='Date', default=fields.Date.today)
datetime = fields.Datetime(string='DateTime', default=fields.Datetime.now)

# Selection
state = fields.Selection([
    ('draft', 'Draft'),
    ('done', 'Done')
], string='State', default='draft')

# Relations
partner_id = fields.Many2one('res.partner', string='Partner')
line_ids = fields.One2many('model.line', 'parent_id', string='Lines')
tag_ids = fields.Many2many('model.tag', string='Tags')

# Computed
total = fields.Float(compute='_compute_total', store=True)

# Related
partner_name = fields.Char(related='partner_id.name', store=True)

# Binary
image = fields.Binary(string='Image', attachment=True)
```

---

## View Development

### Form View Example

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_my_model_form" model="ir.ui.view">
        <field name="name">routy.my.model.form</field>
        <field name="model">routy.my_model</field>
        <field name="arch" type="xml">
            <form string="My Model">
                <header>
                    <button name="action_confirm" string="Confirm"
                            type="object" class="oe_highlight"
                            invisible="state != 'draft'"/>
                    <button name="action_done" string="Mark Done"
                            type="object" class="oe_highlight"
                            invisible="state != 'confirmed'"/>
                    <field name="state" widget="statusbar"
                           statusbar_visible="draft,confirmed,done"/>
                </header>
                <sheet>
                    <div class="oe_button_box" name="button_box">
                        <button name="action_view_related"
                                type="object"
                                class="oe_stat_button"
                                icon="fa-list">
                            <field name="related_count" widget="statinfo"
                                   string="Related"/>
                        </button>
                    </div>
                    <div class="oe_title">
                        <h1>
                            <field name="name" placeholder="Name..."/>
                        </h1>
                    </div>
                    <group>
                        <group>
                            <field name="partner_id"/>
                            <field name="date"/>
                        </group>
                        <group>
                            <field name="total_amount"/>
                            <field name="currency_id" invisible="1"/>
                        </group>
                    </group>
                    <notebook>
                        <page string="Lines">
                            <field name="line_ids">
                                <tree editable="bottom">
                                    <field name="name"/>
                                    <field name="quantity"/>
                                    <field name="amount"/>
                                </tree>
                            </field>
                        </page>
                        <page string="Other Info">
                            <group>
                                <field name="company_id"/>
                                <field name="create_date"/>
                            </group>
                        </page>
                    </notebook>
                </sheet>
                <div class="oe_chatter">
                    <field name="message_follower_ids"/>
                    <field name="activity_ids"/>
                    <field name="message_ids"/>
                </div>
            </form>
        </field>
    </record>
</odoo>
```

### Tree View Example

```xml
<record id="view_my_model_tree" model="ir.ui.view">
    <field name="name">routy.my.model.tree</field>
    <field name="model">routy.my_model</field>
    <field name="arch" type="xml">
        <tree string="My Models" decoration-info="state=='draft'"
              decoration-success="state=='done'">
            <field name="name"/>
            <field name="partner_id"/>
            <field name="date"/>
            <field name="total_amount"/>
            <field name="state" widget="badge"
                   decoration-info="state == 'draft'"
                   decoration-success="state == 'done'"/>
        </tree>
    </field>
</record>
```

### Search View Example

```xml
<record id="view_my_model_search" model="ir.ui.view">
    <field name="name">routy.my.model.search</field>
    <field name="model">routy.my_model</field>
    <field name="arch" type="xml">
        <search string="Search My Models">
            <field name="name"/>
            <field name="partner_id"/>
            <filter string="Draft" name="draft"
                    domain="[('state', '=', 'draft')]"/>
            <filter string="Confirmed" name="confirmed"
                    domain="[('state', '=', 'confirmed')]"/>
            <separator/>
            <filter string="This Month" name="this_month"
                    domain="[('date', '>=', (context_today() - relativedelta(months=1)).strftime('%Y-%m-01'))]"/>
            <group expand="0" string="Group By">
                <filter string="Partner" name="partner"
                        context="{'group_by': 'partner_id'}"/>
                <filter string="State" name="state"
                        context="{'group_by': 'state'}"/>
                <filter string="Date" name="date"
                        context="{'group_by': 'date'}"/>
            </group>
        </search>
    </field>
</record>
```

---

## Security Implementation

### Groups Definition (security.xml)

```xml
<record id="group_my_user" model="res.groups">
    <field name="name">User</field>
    <field name="category_id" ref="module_category_routy"/>
    <field name="implied_ids" eval="[(4, ref('base.group_user'))]"/>
</record>

<record id="group_my_manager" model="res.groups">
    <field name="name">Manager</field>
    <field name="category_id" ref="module_category_routy"/>
    <field name="implied_ids" eval="[(4, ref('group_my_user'))]"/>
</record>
```

### Access Rights (ir.model.access.csv)

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_my_model_user,routy.my_model.user,model_routy_my_model,group_my_user,1,1,1,0
access_my_model_manager,routy.my_model.manager,model_routy_my_model,group_my_manager,1,1,1,1
```

### Record Rules

```xml
<record id="my_model_user_rule" model="ir.rule">
    <field name="name">User: Own Records Only</field>
    <field name="model_id" ref="model_routy_my_model"/>
    <field name="domain_force">[('create_uid', '=', user.id)]</field>
    <field name="groups" eval="[(4, ref('group_my_user'))]"/>
    <field name="perm_read" eval="True"/>
    <field name="perm_write" eval="True"/>
    <field name="perm_create" eval="True"/>
    <field name="perm_unlink" eval="False"/>
</record>
```

---

## API Development

### Creating an API Endpoint

```python
from odoo import http
from odoo.http import request, Response
import json

class MyAPI(http.Controller):

    def _json_response(self, data, status=200):
        """Return JSON response"""
        return Response(
            json.dumps(data),
            status=status,
            mimetype='application/json'
        )

    @http.route('/api/v1/my-endpoint', type='http', auth='user',
                methods=['GET'], csrf=False)
    def get_data(self, **kwargs):
        """Get data endpoint"""
        try:
            # Get data
            records = request.env['routy.my_model'].search([])

            data = [{
                'id': rec.id,
                'name': rec.name,
            } for rec in records]

            return self._json_response({
                'success': True,
                'data': data
            })

        except Exception as e:
            return self._json_response({
                'error': str(e)
            }, 500)

    @http.route('/api/v1/my-endpoint', type='json', auth='user',
                methods=['POST'], csrf=False)
    def create_data(self, **kwargs):
        """Create data endpoint (JSON-RPC)"""
        try:
            data = request.jsonrequest

            record = request.env['routy.my_model'].create({
                'name': data.get('name'),
                'partner_id': data.get('partner_id'),
            })

            return {
                'success': True,
                'id': record.id
            }

        except Exception as e:
            return {'error': str(e)}
```

---

## Testing

### Unit Test Example

See the tests section for comprehensive examples.

---

## Best Practices

### 1. Code Style

- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings to all methods
- Keep methods small and focused

### 2. Performance

- Use `@api.depends` properly for computed fields
- Add `store=True` for frequently accessed computed fields
- Use `index=True` for searchable fields
- Batch operations when possible

### 3. Security

- Always define access rights
- Use record rules for row-level security
- Validate user input
- Use `sudo()` carefully

### 4. User Experience

- Provide clear error messages
- Use tracking for important fields
- Add help text to fields
- Design intuitive workflows

---

## Common Patterns

### 1. Smart Buttons

```python
def action_view_related(self):
    """Open related records"""
    self.ensure_one()
    return {
        'name': _('Related Records'),
        'type': 'ir.actions.act_window',
        'res_model': 'related.model',
        'view_mode': 'tree,form',
        'domain': [('parent_id', '=', self.id)],
        'context': {'default_parent_id': self.id}
    }
```

### 2. Wizards

```python
class MyWizard(models.TransientModel):
    _name = 'my.wizard'
    _description = 'My Wizard'

    def action_process(self):
        """Process wizard action"""
        active_id = self.env.context.get('active_id')
        record = self.env['my.model'].browse(active_id)
        # Process logic
        return {'type': 'ir.actions.act_window_close'}
```

### 3. Sequences

```xml
<record id="seq_my_model" model="ir.sequence">
    <field name="name">My Model Sequence</field>
    <field name="code">routy.my_model</field>
    <field name="prefix">MM</field>
    <field name="padding">5</field>
    <field name="number_next">1</field>
    <field name="number_increment">1</field>
</record>
```

---

## Troubleshooting

### Common Issues

1. **Module not found**
   - Check addons_path in odoo.conf
   - Restart Odoo server
   - Update apps list

2. **Access denied errors**
   - Check security/ir.model.access.csv
   - Verify user groups
   - Check record rules

3. **Field not updating**
   - Check if field has `readonly=True`
   - Verify compute dependencies
   - Check write permissions

4. **View not showing**
   - Check XML syntax
   - Verify view priority
   - Check access rights

---

## Contributing

See CONTRIBUTING.md for contribution guidelines.

---

## Resources

- [Odoo Official Documentation](https://www.odoo.com/documentation/18.0/)
- [Odoo Developer Guide](https://www.odoo.com/documentation/18.0/developer.html)
- [Python PEP 8 Style Guide](https://pep8.org/)

---

## License

This documentation is part of the Routy module, licensed under LGPL-3.
