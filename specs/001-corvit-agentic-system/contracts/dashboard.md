# API Contract: Dashboard

**Base**: `/api/dashboard`
**Auth**: Bearer JWT (any role; data scoped by role)

## GET /api/dashboard/stats

**Description**: Aggregated KPI data for dashboard cards and charts.

**Response 200**:
```json
{
  "kpis": {
    "total_students": 20,
    "active_courses": 5,
    "active_batches": 5,
    "total_revenue": 500000.00,
    "overdue_fees_count": 3,
    "overdue_fees_amount": 75000.00,
    "average_attendance": 82.5
  },
  "attendance_trend": [
    { "date": "2026-01-01", "percentage": 85.0 },
    { "date": "2026-01-02", "percentage": 82.0 },
    { "date": "2026-01-03", "percentage": 88.0 }
  ],
  "enrollment_by_course": [
    { "course": "CCNA", "count": 8 },
    { "course": "CCNP", "count": 4 },
    { "course": "AI", "count": 5 },
    { "course": "Cyber Security", "count": 2 },
    { "course": "Cloud Computing", "count": 1 }
  ],
  "recent_activity": [
    {
      "id": "uuid",
      "event_type": "enrollment",
      "actor": "admin",
      "target": "Ali Ahmed → CCNA-Batch-1",
      "timestamp": "2026-02-02T09:30:00Z"
    }
  ],
  "timestamp": "2026-02-02T10:00:00Z"
}
```
