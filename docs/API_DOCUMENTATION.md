# Routy Mobile API Documentation

## Overview

The Routy Mobile API provides RESTful endpoints for driver mobile applications to interact with the delivery management system. All endpoints require user authentication and driver role verification.

**Base URL:** `/api/v1/routy`

**Authentication:** User session authentication (`auth='user'`)

**Content Type:** `application/json`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Jobs Management](#jobs-management)
3. [GPS Tracking](#gps-tracking)
4. [Parcel Operations](#parcel-operations)
5. [Error Handling](#error-handling)
6. [Response Formats](#response-formats)

---

## Authentication

All API endpoints require:
- Valid Odoo user session
- User must belong to the "Driver" security group (`routy.group_driver`)

### Authentication Check Process

```python
# The API automatically verifies:
1. User is authenticated (not public)
2. User has driver role
3. User has permission to access the resource
```

### Error Responses

**401 Unauthorized**
```json
{
  "error": "Authentication required"
}
```

**403 Forbidden**
```json
{
  "error": "User is not a driver"
}
```

---

## Jobs Management

### 1. Get My Jobs

Retrieve all jobs assigned to the authenticated driver.

**Endpoint:** `GET /api/v1/routy/jobs/my`

**Parameters:**
- `state` (optional): Filter by job state
  - Values: `assigned`, `accepted`, `in_progress`, `completed`, `failed`, `cancelled`

**Request Example:**
```bash
curl -X GET "https://your-domain.com/api/v1/routy/jobs/my?state=assigned" \
  -H "Cookie: session_id=YOUR_SESSION_ID"
```

**Success Response (200):**
```json
{
  "success": true,
  "count": 5,
  "jobs": [
    {
      "id": 15,
      "name": "JOB00015",
      "job_type": "pickup",
      "state": "assigned",
      "service_request_id": 10,
      "service_request_name": "SR00010",
      "customer_name": "Ahmed Electronics",
      "location_address": "123 Main St, Cairo",
      "location_lat": 30.0444,
      "location_lng": 31.2357,
      "contact_name": "Ahmed Ali",
      "contact_phone": "+201234567890",
      "scheduled_time": "2024-01-15T10:00:00",
      "parcel_count": 3,
      "notes": "Fragile items - handle with care"
    }
  ]
}
```

---

### 2. Accept Job

Accept an assigned job.

**Endpoint:** `POST /api/v1/routy/jobs/<job_id>/accept`

**Path Parameters:**
- `job_id` (required): The job ID

**Request Example:**
```bash
curl -X POST "https://your-domain.com/api/v1/routy/jobs/15/accept" \
  -H "Cookie: session_id=YOUR_SESSION_ID"
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Job accepted successfully",
  "job_id": 15,
  "state": "accepted"
}
```

**Error Responses:**

**404 Not Found:**
```json
{
  "error": "Job not found"
}
```

**403 Forbidden:**
```json
{
  "error": "Not authorized"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Only assigned jobs can be accepted."
}
```

---

### 3. Start Job

Start an accepted job.

**Endpoint:** `POST /api/v1/routy/jobs/<job_id>/start`

**Path Parameters:**
- `job_id` (required): The job ID

**Request Example:**
```bash
curl -X POST "https://your-domain.com/api/v1/routy/jobs/15/start" \
  -H "Cookie: session_id=YOUR_SESSION_ID"
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Job started successfully",
  "job_id": 15,
  "state": "in_progress",
  "started_at": "2024-01-15T10:30:00"
}
```

---

### 4. Complete Job

Complete a job that is in progress.

**Endpoint:** `POST /api/v1/routy/jobs/<job_id>/complete`

**Path Parameters:**
- `job_id` (required): The job ID

**Request Example:**
```bash
curl -X POST "https://your-domain.com/api/v1/routy/jobs/15/complete" \
  -H "Cookie: session_id=YOUR_SESSION_ID"
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Job completed successfully",
  "job_id": 15,
  "state": "completed"
}
```

**Important Notes:**
- For delivery jobs, all parcels must have Proof of Delivery (signature or photo)
- System automatically updates related service request status

---

## GPS Tracking

### Update GPS Location

Send GPS location updates during job execution.

**Endpoint:** `POST /api/v1/routy/gps/update`

**Type:** `type='json'` (JSON-RPC)

**Request Body:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "job_id": 15,
    "latitude": 30.0444,
    "longitude": 31.2357,
    "accuracy": 10.5,
    "speed": 45.0,
    "heading": 180.0,
    "altitude": 25.0,
    "battery_level": 85,
    "network_type": "4G"
  }
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| job_id | Integer | Yes | Current active job ID |
| latitude | Float | Yes | GPS latitude (-90 to 90) |
| longitude | Float | Yes | GPS longitude (-180 to 180) |
| accuracy | Float | No | Location accuracy in meters |
| speed | Float | No | Speed in km/h |
| heading | Float | No | Direction in degrees (0-360) |
| altitude | Float | No | Altitude in meters |
| battery_level | Integer | No | Battery percentage (0-100) |
| network_type | String | No | Network type (2G/3G/4G/5G/WiFi) |

**Success Response (200):**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "message": "GPS location updated",
    "log_id": 1234
  }
}
```

**Error Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "error": "Missing required field: latitude"
  }
}
```

---

## Parcel Operations

### 1. Deliver Parcel

Mark a parcel as delivered with Proof of Delivery.

**Endpoint:** `POST /api/v1/routy/parcels/<parcel_id>/deliver`

**Type:** `type='json'` (JSON-RPC)

**Path Parameters:**
- `parcel_id` (required): The parcel ID

**Request Body:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "recipient_name": "Mohamed Hassan",
    "notes": "Delivered at reception desk",
    "signature": "iVBORw0KGgoAAAANSUhEUgAAAAUA...",
    "photo": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wB..."
  }
}
```

**Field Descriptions:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| recipient_name | String | Recommended | Name of person who received |
| notes | String | Optional | Delivery notes |
| signature | String | Yes* | Base64 encoded signature image |
| photo | String | Yes* | Base64 encoded delivery photo |

*At least one (signature or photo) is required

**Success Response (200):**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "message": "Parcel delivered successfully",
    "parcel_id": 123,
    "tracking_number": "TRK0000123"
  }
}
```

**Error Responses:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "error": "Parcel not found"
  }
}
```

```json
{
  "jsonrpc": "2.0",
  "result": {
    "error": "Not authorized"
  }
}
```

---

### 2. Get Parcel Details

Retrieve detailed information about a specific parcel.

**Endpoint:** `GET /api/v1/routy/parcels/<parcel_id>`

**Path Parameters:**
- `parcel_id` (required): The parcel ID

**Request Example:**
```bash
curl -X GET "https://your-domain.com/api/v1/routy/parcels/123" \
  -H "Cookie: session_id=YOUR_SESSION_ID"
```

**Success Response (200):**
```json
{
  "success": true,
  "parcel": {
    "id": 123,
    "name": "TRK0000123",
    "description": "Electronics - Laptop",
    "weight": 2.5,
    "declared_value": 5000.0,
    "state": "out_for_delivery",
    "service_request": "SR00010",
    "customer": "Ahmed Electronics"
  }
}
```

**Error Response (404):**
```json
{
  "error": "Parcel not found"
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | User not authorized |
| 404 | Not Found | Resource not found |
| 500 | Internal Server Error | Server error occurred |

### Error Response Format

All errors follow this format:
```json
{
  "error": "Error description here"
}
```

For JSON-RPC endpoints:
```json
{
  "jsonrpc": "2.0",
  "result": {
    "error": "Error description here"
  }
}
```

---

## Response Formats

### Standard HTTP Response

```json
{
  "success": true,
  "data": {},
  "message": "Optional message"
}
```

### JSON-RPC Response

```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "data": {}
  }
}
```

---

## Best Practices

### 1. GPS Updates
- Send GPS updates every 30-60 seconds during active jobs
- Include battery level to help manage driver resources
- Always send accurate location data

### 2. Job Management
- Accept jobs before starting them
- Complete pickup jobs before starting delivery jobs
- Provide failure reasons if job cannot be completed

### 3. Proof of Delivery
- Always collect signature or photo
- Add recipient name for better tracking
- Include notes for special circumstances

### 4. Error Handling
- Always check response status
- Handle network errors gracefully
- Retry failed requests with exponential backoff

### 5. Security
- Never share session tokens
- Use HTTPS in production
- Logout when session ends

---

## Mobile App Integration Example

### JavaScript/React Native Example

```javascript
class RoutyAPI {
  constructor(baseURL, sessionId) {
    this.baseURL = baseURL;
    this.sessionId = sessionId;
  }

  async getMyJobs(state = null) {
    const url = state
      ? `${this.baseURL}/api/v1/routy/jobs/my?state=${state}`
      : `${this.baseURL}/api/v1/routy/jobs/my`;

    const response = await fetch(url, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Cookie': `session_id=${this.sessionId}`
      }
    });

    return await response.json();
  }

  async updateGPS(jobId, location) {
    const response = await fetch(`${this.baseURL}/api/v1/routy/gps/update`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'Cookie': `session_id=${this.sessionId}`
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'call',
        params: {
          job_id: jobId,
          latitude: location.latitude,
          longitude: location.longitude,
          accuracy: location.accuracy,
          speed: location.speed,
          battery_level: location.batteryLevel,
          network_type: location.networkType
        }
      })
    });

    return await response.json();
  }

  async deliverParcel(parcelId, pod) {
    const response = await fetch(
      `${this.baseURL}/api/v1/routy/parcels/${parcelId}/deliver`,
      {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'Cookie': `session_id=${this.sessionId}`
        },
        body: JSON.stringify({
          jsonrpc: '2.0',
          method: 'call',
          params: {
            recipient_name: pod.recipientName,
            notes: pod.notes,
            signature: pod.signatureBase64,
            photo: pod.photoBase64
          }
        })
      }
    );

    return await response.json();
  }
}

// Usage
const api = new RoutyAPI('https://your-domain.com', 'your_session_id');

// Get assigned jobs
const jobs = await api.getMyJobs('assigned');

// Update GPS location
await api.updateGPS(15, {
  latitude: 30.0444,
  longitude: 31.2357,
  accuracy: 10,
  speed: 45,
  batteryLevel: 85,
  networkType: '4G'
});

// Deliver parcel
await api.deliverParcel(123, {
  recipientName: 'Mohamed Hassan',
  notes: 'Delivered successfully',
  signatureBase64: '...',
  photoBase64: '...'
});
```

---

## Rate Limiting

Currently, there are no rate limits implemented. However, please follow these guidelines:

- GPS updates: Maximum 1 request per 30 seconds
- Job status updates: As needed
- Parcel queries: Maximum 10 requests per minute

---

## Changelog

### Version 1.0.0 (Current)
- Initial API release
- Job management endpoints
- GPS tracking
- Parcel delivery operations

---

## Support

For API issues or questions:
- Check the error message in the response
- Review the Odoo logs for detailed error information
- Contact system administrator

---

## License

This API documentation is part of the Routy module, licensed under LGPL-3.
