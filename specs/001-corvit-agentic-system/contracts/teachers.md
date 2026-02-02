# API Contract: Teachers

**Base**: `/api/teachers`
**Auth**: Bearer JWT (admin for write; any authenticated for read)

## Standard CRUD

### POST /api/teachers
```json
{
  "name": "Haleema Sayyar",
  "email": "haleema@corvit.edu.pk",
  "phone": "03001111111",
  "specialization": "Networking",
  "qualification": "CCNP, CCIE"
}
```
**Response 201**: Teacher object.

### GET /api/teachers
**Query**: `?page=1&limit=20&search=haleema&is_active=true`
**Response 200**: Paginated list.

### GET /api/teachers/{id}
**Response 200**: Single teacher.

### PUT /api/teachers/{id}
**Response 200**: Updated teacher.

### DELETE /api/teachers/{id}
**Response 204**: No content.
**Response 409**: `{ "detail": "Cannot delete teacher with active batches" }`

## Extra Endpoints

### GET /api/teachers/{id}/batches
**Response 200**:
```json
{
  "teacher_id": "uuid",
  "batches": [
    {
      "id": "uuid",
      "name": "CCNA-Batch-1",
      "course_name": "CCNA",
      "schedule_days": "Mon,Wed,Fri",
      "schedule_time": "10:00-12:00",
      "student_count": 18,
      "status": "active"
    }
  ]
}
```
