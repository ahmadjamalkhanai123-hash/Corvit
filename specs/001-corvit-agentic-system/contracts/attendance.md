# API Contract: Attendance

**Base**: `/api/attendance`
**Auth**: Bearer JWT (admin/teacher for write; any authenticated for read)

## Standard CRUD

### POST /api/attendance
Mark single attendance.
```json
{
  "student_id": "uuid",
  "batch_id": "uuid",
  "date": "2026-02-02",
  "status": "present"
}
```
**Response 201**: Attendance record.
**Response 409**: `{ "detail": "Attendance already marked for this student on this date" }`

### GET /api/attendance
**Query**: `?page=1&limit=50&batch_id=uuid&student_id=uuid&date=2026-02-02&status=absent`
**Response 200**: Paginated list.

### GET /api/attendance/{id}
**Response 200**: Single record.

### PUT /api/attendance/{id}
**Response 200**: Updated record.

### DELETE /api/attendance/{id}
**Response 204**: No content.

## Extra Endpoints

### POST /api/attendance/mark
Bulk mark attendance for a batch.
```json
{
  "batch_id": "uuid",
  "date": "2026-02-02",
  "records": [
    { "student_id": "uuid-1", "status": "present" },
    { "student_id": "uuid-2", "status": "absent" },
    { "student_id": "uuid-3", "status": "late" }
  ]
}
```
**Response 200**:
```json
{
  "batch_id": "uuid",
  "date": "2026-02-02",
  "marked": 3,
  "errors": []
}
```

### GET /api/attendance/report/{batch_id}
**Query**: `?from_date=2026-01-01&to_date=2026-02-01`
**Response 200**:
```json
{
  "batch_id": "uuid",
  "batch_name": "CCNA-Batch-1",
  "period": { "from": "2026-01-01", "to": "2026-02-01" },
  "summary": {
    "total_classes": 20,
    "average_attendance": 82.5
  },
  "students": [
    {
      "student_id": "uuid",
      "name": "Ali Ahmed",
      "present": 17,
      "absent": 2,
      "late": 1,
      "percentage": 85.0,
      "alert_level": null
    }
  ]
}
```
