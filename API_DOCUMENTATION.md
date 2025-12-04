# LuminaBI REST API Documentation

## Overview
Complete REST API for LuminaBI with JWT authentication and comprehensive endpoints for all resources.

## Authentication

### Obtain Access Token
```bash
POST /api/token/
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Refresh Token
```bash
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## API Endpoints

### Core Resources

#### Organizations
- `GET /api/organizations/` - List organizations
- `POST /api/organizations/` - Create organization
- `GET /api/organizations/{id}/` - Get organization details
- `PUT /api/organizations/{id}/` - Update organization
- `DELETE /api/organizations/{id}/` - Delete organization
- `POST /api/organizations/{id}/add_member/` - Add member
- `POST /api/organizations/{id}/remove_member/` - Remove member

#### Settings
- `GET /api/settings/` - List settings
- `POST /api/settings/` - Create setting
- `GET /api/settings/{id}/` - Get setting
- `PUT /api/settings/{id}/` - Update setting
- `DELETE /api/settings/{id}/` - Delete setting

#### Audit Logs
- `GET /api/audit-logs/` - List audit logs (read-only)
- `GET /api/audit-logs/{id}/` - Get audit log details

### Analytics Resources

#### Insights
- `GET /api/insights/` - List insights
- `POST /api/insights/` - Create insight
- `GET /api/insights/{id}/` - Get insight details
- `PUT /api/insights/{id}/` - Update insight
- `DELETE /api/insights/{id}/` - Delete insight
- `POST /api/insights/{id}/validate/` - Mark insight as validated
- `POST /api/insights/{id}/invalidate/` - Mark insight as invalid

#### Reports
- `GET /api/reports/` - List reports
- `POST /api/reports/` - Create report
- `GET /api/reports/{id}/` - Get report details
- `PUT /api/reports/{id}/` - Update report
- `DELETE /api/reports/{id}/` - Delete report
- `POST /api/reports/{id}/publish/` - Publish report

#### Trends
- `GET /api/trends/` - List trends (read-only)
- `GET /api/trends/{id}/` - Get trend details

#### Anomalies
- `GET /api/anomalies/` - List anomalies
- `GET /api/anomalies/{id}/` - Get anomaly details
- `PUT /api/anomalies/{id}/` - Update anomaly
- `POST /api/anomalies/{id}/acknowledge/` - Acknowledge anomaly
- `POST /api/anomalies/{id}/resolve/` - Resolve anomaly

#### Alerts
- `GET /api/alerts/` - List alerts
- `GET /api/alerts/{id}/` - Get alert details
- `PUT /api/alerts/{id}/` - Update alert
- `POST /api/alerts/{id}/acknowledge/` - Acknowledge alert
- `POST /api/alerts/{id}/resolve/` - Resolve alert

#### Metrics
- `GET /api/metrics/` - List metrics (read-only)
- `GET /api/metrics/{id}/` - Get metric details

#### Dashboards
- `GET /api/dashboards/` - List dashboards
- `POST /api/dashboards/` - Create dashboard
- `GET /api/dashboards/{id}/` - Get dashboard details
- `PUT /api/dashboards/{id}/` - Update dashboard
- `DELETE /api/dashboards/{id}/` - Delete dashboard
- `POST /api/dashboards/{id}/share/` - Share dashboard with users
- `POST /api/dashboards/{id}/unshare/` - Unshare dashboard

### Data Resources

#### Datasets
- `GET /api/datasets/` - List datasets
- `POST /api/datasets/` - Upload dataset
- `GET /api/datasets/{id}/` - Get dataset details
- `PUT /api/datasets/{id}/` - Update dataset
- `DELETE /api/datasets/{id}/` - Delete dataset

#### Visualizations
- `GET /api/visualizations/` - List visualizations
- `POST /api/visualizations/` - Create visualization
- `GET /api/visualizations/{id}/` - Get visualization details
- `PUT /api/visualizations/{id}/` - Update visualization
- `DELETE /api/visualizations/{id}/` - Delete visualization

#### Dashboard Models
- `GET /api/dashboard-models/` - List dashboard models
- `POST /api/dashboard-models/` - Create dashboard model
- `GET /api/dashboard-models/{id}/` - Get dashboard model details
- `PUT /api/dashboard-models/{id}/` - Update dashboard model
- `DELETE /api/dashboard-models/{id}/` - Delete dashboard model

## Usage Examples

### Get Insights for Current User
```bash
curl -H "Authorization: Bearer <access_token>" \
  https://api.luminabi.com/api/insights/
```

### Create a New Insight
```bash
curl -X POST \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Q4 Revenue Trend",
    "description": "Quarterly revenue analysis",
    "dataset": 1,
    "insight_type": "trend",
    "confidence_level": "high",
    "metrics": {"growth": 15.5}
  }' \
  https://api.luminabi.com/api/insights/
```

### Validate an Insight
```bash
curl -X POST \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "Validated by data quality team"
  }' \
  https://api.luminabi.com/api/insights/1/validate/
```

### Acknowledge an Anomaly
```bash
curl -X POST \
  -H "Authorization: Bearer <access_token>" \
  https://api.luminabi.com/api/anomalies/1/acknowledge/
```

### Share a Dashboard
```bash
curl -X POST \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_ids": [2, 3, 4]
  }' \
  https://api.luminabi.com/api/dashboards/1/share/
```

## Response Format

All responses are in JSON format:

### Success Response (200)
```json
{
  "id": 1,
  "title": "Sample Insight",
  "description": "Description of the insight",
  "created_at": "2024-12-04T10:30:00Z",
  "updated_at": "2024-12-04T10:30:00Z"
}
```

### Error Response
```json
{
  "error": "Error message",
  "detail": "Additional error details"
}
```

### List Response
```json
{
  "count": 10,
  "next": "https://api.luminabi.com/api/insights/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Sample Insight",
      ...
    }
  ]
}
```

## Filtering

Most list endpoints support filtering through query parameters:

```bash
# Filter by status
GET /api/reports/?status=published

# Filter by dataset
GET /api/insights/?dataset=1

# Filter by date range
GET /api/anomalies/?detected_at__gte=2024-12-01&detected_at__lt=2024-12-04

# Search
GET /api/datasets/?search=sales
```

## Pagination

Responses are paginated with 20 items per page by default:

```bash
GET /api/insights/?page=2
GET /api/reports/?page=3&page_size=50
```

## Permissions

- **Authentication Required**: Most endpoints require JWT token
- **Owner Only**: Create/update/delete operations restricted to owner
- **Read-Only**: Some endpoints (trends, metrics) are read-only
- **Public Access**: Public datasets and visualizations viewable without authentication

## Rate Limiting

API rate limits are enforced:
- 100 requests per minute for authenticated users
- 10 requests per minute for anonymous users

## Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `204 No Content`: Request successful, no content to return
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Support

For API support and issues, contact the development team or visit the documentation portal.
