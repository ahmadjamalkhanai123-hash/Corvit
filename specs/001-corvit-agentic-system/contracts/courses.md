
# API Contract: Courses

**Base**: `/api/courses`
**Auth**: Bearer JWT (admin for write; any authenticated for read)

## Standard CRUD

### POST /api/courses
```json
{
  "name": "CCNA",
  "code": "CCNA-01",
  "duration_weeks": 12,
  "fee_amount": 25000.00,
  "description": "Cisco Certified Network Associate",
  "category": "Networking"
}
```
**Response 201**: Course object.

### GET /api/courses
**Query**: `?page=1&limit=20&search=ccna&category=Networking&is_active=true`
**Response 200**: Paginated list.

### GET /api/courses/{id}
**Response 200**: Single course.

### PUT /api/courses/{id}
**Response 200**: Updated course.

### DELETE /api/courses/{id}
**Response 204**: No content.
**Response 409**: `{ "detail": "Cannot delete course with active batches" }`

## Extra Endpoints

### GET /api/courses/{id}/batches
**Response 200**:
```json
{
  "course_id": "uuid",
  "course_name": "CCNA",
  "batches": [
    {
      "id": "uuid",
      "name": "CCNA-Batch-1",
      "teacher_name": "Haleema Sayyar",
      "schedule_days": "Mon,Wed,Fri",
      "schedule_time": "10:00-12:00",
      "start_date": "2026-01-15",
      "enrolled": 18,
      "max_capacity": 30,
      "seats_available": 12,
      "status": "active"
    }
  ]
}
```
