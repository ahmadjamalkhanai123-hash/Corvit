# API Contract: Enrollments

**Base**: `/api/enrollments`
**Auth**: Bearer JWT (admin for write; any authenticated for read)

## Standard CRUD

### POST /api/enrollments
```json
{
  "student_id": "uuid",
  "batch_id": "uuid"
}
```
**Response 201**: Enrollment object with student_name, batch_name, course_name.
**Response 409**: `{ "detail": "Student already enrolled in this batch" }`
**Response 422**: `{ "detail": "Batch is at maximum capacity" }`

### GET /api/enrollments
**Query**: `?page=1&limit=20&student_id=uuid&batch_id=uuid&status=active`
**Response 200**: Paginated list with nested names.

### GET /api/enrollments/{id}
**Response 200**: Single enrollment.

### PUT /api/enrollments/{id}
Update enrollment status.
```json
{ "status": "dropped" }
```
**Response 200**: Updated enrollment.

### DELETE /api/enrollments/{id}
**Response 204**: No content.

## Extra Endpoints

### POST /api/enrollments/enroll
Convenience endpoint — enroll by student name + course/batch.
```json
{
  "student_id": "uuid",
  "batch_id": "uuid"
}
```
Same as POST /api/enrollments but with additional validation and event logging.
