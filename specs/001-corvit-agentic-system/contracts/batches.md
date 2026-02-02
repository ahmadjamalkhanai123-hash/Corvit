# API Contract: Batches

**Base**: `/api/batches`
**Auth**: Bearer JWT (admin for write; any authenticated for read)

## Standard CRUD

### POST /api/batches
```json
{
  "course_id": "uuid",
  "teacher_id": "uuid",
  "name": "CCNA-Batch-1",
  "room": "Lab-1",
  "schedule_days": "Mon,Wed,Fri",
  "schedule_time": "10:00-12:00",
  "start_date": "2026-01-15",
  "end_date": "2026-04-15",
  "max_capacity": 30
}
```
**Response 201**: Batch object with course_name and teacher_name included.

### GET /api/batches
**Query**: `?page=1&limit=20&course_id=uuid&teacher_id=uuid&status=active`
**Response 200**: Paginated list with nested course_name and teacher_name.

### GET /api/batches/{id}
**Response 200**: Batch with full course and teacher details.

### PUT /api/batches/{id}
**Response 200**: Updated batch.

### DELETE /api/batches/{id}
**Response 204**: No content.
**Response 409**: `{ "detail": "Cannot delete batch with active enrollments" }`

## Extra Endpoints

### GET /api/batches/{id}/students
**Response 200**:
```json
{
  "batch_id": "uuid",
  "batch_name": "CCNA-Batch-1",
  "students": [
    {
      "id": "uuid",
      "name": "Ali Ahmed",
      "email": "ali@example.com",
      "enrollment_status": "active",
      "attendance_percentage": 85.0
    }
  ],
  "total_enrolled": 18
}
```

### GET /api/batches/{id}/schedule
**Response 200**:
```json
{
  "batch_id": "uuid",
  "batch_name": "CCNA-Batch-1",
  "course_name": "CCNA",
  "teacher_name": "Haleema Sayyar",
  "room": "Lab-1",
  "schedule_days": "Mon,Wed,Fri",
  "schedule_time": "10:00-12:00",
  "start_date": "2026-01-15",
  "end_date": "2026-04-15"
}
```
