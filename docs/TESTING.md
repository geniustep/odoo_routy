# Testing Guide for Routy

## Overview

This document describes how to run and write tests for the Routy module.

## Running Tests

### Run All Tests

```bash
# Run all Routy tests
./odoo-bin -c odoo.conf -d test_database -i routy --test-enable --stop-after-init

# Run with specific tags
./odoo-bin -c odoo.conf -d test_database -i routy --test-enable --test-tags routy --stop-after-init
```

### Run Specific Test Files

```bash
# Run service request tests only
./odoo-bin -c odoo.conf -d test_database -i routy --test-enable \
  --test-tags /routy:TestServiceRequest --stop-after-init
```

### Run Tests with Coverage

```bash
# Install coverage
pip install coverage

# Run with coverage
coverage run --source=addons/routy ./odoo-bin -c odoo.conf -d test_database \
  -i routy --test-enable --stop-after-init

# Generate report
coverage report
coverage html  # Creates htmlcov/index.html
```

## Test Structure

```
tests/
├── __init__.py              # Imports all test modules
├── common.py                # Base test class with helpers
├── test_service_request.py  # Service request tests
├── test_parcel.py          # Parcel tests
├── test_job.py             # Job tests
├── test_hub.py             # Hub tests
├── test_linehaul.py        # Linehaul tests
├── test_route_plan.py      # Route plan tests
├── test_payment_record.py  # Payment record tests
├── test_incident.py        # Incident tests
├── test_wizards.py         # Wizard tests
└── test_mobile_api.py      # API integration tests
```

## Writing Tests

### Test Class Template

```python
# -*- coding: utf-8 -*-

from odoo.tests import tagged
from odoo.exceptions import UserError, ValidationError
from .common import RoutyCommonCase


@tagged('post_install', '-at_install', 'routy')
class TestMyModel(RoutyCommonCase):
    """Test cases for My Model"""

    def test_01_create_record(self):
        """Test creating a record"""
        record = self.env['routy.my_model'].create({
            'name': 'Test Record',
        })
        self.assertTrue(record, "Record should be created")
        self.assertEqual(record.name, 'Test Record')

    def test_02_validation(self):
        """Test field validation"""
        with self.assertRaises(ValidationError):
            self.env['routy.my_model'].create({
                'name': '',  # Invalid empty name
            })
```

### Using Common Test Helpers

```python
class TestExample(RoutyCommonCase):

    def test_with_helpers(self):
        """Test using helper methods"""
        # Create service request
        sr = self._create_service_request()

        # Create parcel
        parcel = self._create_parcel(sr, weight=5.0)

        # Create job
        job = self._create_job(sr, job_type='pickup')

        # Assertions
        self.assertEqual(sr.parcel_count, 1)
        self.assertEqual(job.driver_id, self.driver_user)
```

## Test Categories

### Unit Tests
Test individual model methods:
- Field validation
- Computed fields
- Constraints
- Business logic methods

### Integration Tests
Test interactions between models:
- Workflow transitions
- Related record updates
- Cascade operations

### API Tests
Test HTTP endpoints:
- Authentication
- Authorization
- Response format
- Error handling

## Best Practices

### 1. Test Naming
- Start with `test_`
- Use numbers for ordering: `test_01_`, `test_02_`
- Use descriptive names: `test_cannot_confirm_without_parcels`

### 2. Test Organization
- One test method per scenario
- Use clear assertions
- Test both success and failure cases
- Test edge cases

### 3. Test Data
- Use helper methods for creating data
- Clean up in tearDown if needed
- Use meaningful test data

### 4. Assertions
```python
# Good
self.assertEqual(record.state, 'confirmed')
self.assertTrue(record.active)
self.assertIn('SR', record.name)

# With messages
self.assertEqual(
    record.parcel_count, 2,
    "Should have 2 parcels"
)
```

### 5. Testing Exceptions
```python
# Test UserError
with self.assertRaises(UserError):
    record.action_confirm()

# Test ValidationError
with self.assertRaises(ValidationError):
    record.weight = -5
```

### 6. Testing Workflows
```python
def test_complete_workflow(self):
    """Test complete service request workflow"""
    # Create
    sr = self._create_service_request()
    self.assertEqual(sr.state, 'draft')

    # Add parcel
    parcel = self._create_parcel(sr)

    # Confirm
    sr.action_confirm()
    self.assertEqual(sr.state, 'confirmed')

    # Assign driver
    wizard = self.env['routy.assign.driver.wizard'].create({
        'service_request_id': sr.id,
        'driver_id': self.driver_user.id,
        'scheduled_pickup': '2024-01-15 10:00:00',
    })
    wizard.action_assign()
    self.assertEqual(sr.state, 'assigned')
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: odoo
          POSTGRES_USER: odoo
          POSTGRES_DB: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Run tests
        run: |
          ./odoo-bin -c odoo.conf -d test_db -i routy \
            --test-enable --stop-after-init
```

## Coverage Goals

Target coverage by module:
- Models: >90%
- Controllers: >80%
- Wizards: >85%
- Overall: >80%

## Debugging Tests

### Print Debug Info
```python
def test_with_debug(self):
    record = self._create_service_request()

    # Print for debugging
    print(f"Record: {record}")
    print(f"State: {record.state}")
    print(f"Parcel count: {record.parcel_count}")

    # Use pdb for interactive debugging
    import pdb; pdb.set_trace()
```

### Run Single Test
```bash
# Run one specific test
./odoo-bin -c odoo.conf -d test_db -i routy --test-enable \
  --test-tags /routy:TestServiceRequest.test_01_create_service_request \
  --stop-after-init
```

## Common Issues

### 1. Database Not Cleaned
- Use `TransactionCase` for automatic rollback
- Or manually clean in `tearDown()`

### 2. External Dependencies
- Mock external API calls
- Use test mode for services

### 3. Random Failures
- Avoid time-dependent tests
- Use fixed dates/times
- Sort results when order matters

## Resources

- [Odoo Test Documentation](https://www.odoo.com/documentation/18.0/developer/reference/backend/testing.html)
- [Python unittest](https://docs.python.org/3/library/unittest.html)
- [Coverage.py](https://coverage.readthedocs.io/)

## Questions?

If you have questions about testing, please open an issue or check the documentation.
