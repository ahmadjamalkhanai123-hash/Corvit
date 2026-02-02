# API Contract: Students

**Base**: `/api/students`
**Auth**: Bearer JWT (admin only for write; any authenticated for read)

## Standard CRUD

### POST /api/students
Create a student.

**Request**:
```json
{
  "name": "Ali Ahmed",
  "email": "ali@example.com",
  "phone": "03001234567",
  "cnic": "17301-1234567-1",
  "guardian_name": "Ahmed Khan",
  "guardian_phone": "03009876543",
  "address": "Peshawar"
}
```
**Response 201**: Student object with `id`, `enrollment_date`, `status`, `created_at`.
**Response 409**: `{ "detail": "Email already exists" }`

### GET /api/students
List students (paginated).

**Query Params**: `?page=1&limit=20&search=ali&status=active&sort_by=name&sort_order=asc`
**Response 200**:
```json
{
  "items": [ { ...student } ],
  "total": 20,
  "page": 1,
  "limit": 20,
  "pages": 1
}
```

### GET /api/students/{id}
**Response 200**: Single student object.
**Response 404**: `{ "detail": "Student not found" }`

### PUT /api/students/{id}
**Request**: Partial student fields.
**Response 200**: Updated student object.

### DELETE /api/students/{id}
**Response 204**: No content.
**Response 409**: `{ "detail": "Cannot delete student with active enrollments" }`

## Extra Endpoints

### GET /api/students/{id}/attendance
**Query**: `?batch_id=uuid&from_date=2026-01-01&to_date=2026-02-01`
**Response 200**:
```json
{
  "student_id": "uuid",
  "total_classes": 30,
  "present": 24,
  "absent": 4,
  "late": 2,
  "percentage": 80.0,
  "alert_level": "yellow",
  "records": [ { "date": "2026-01-15", "status": "present" } ]
}
```

### GET /api/students/{id}/fees
**Response 200**:
```json
{
  "student_id": "uuid",
  "fees": [
    {
      "id": "uuid",
      "course_name": "CCNA",
      "amount": 25000,
      "paid_amount": 15000,
      "due_date": "2026-02-15",
      "status": "partial",
      "alert_level": null
    }
  ],
  "total_due": 10000,
  "total_paid": 15000
}
```
