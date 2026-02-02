# API Contract: Exams

**Base**: `/api/exams`
**Auth**: Bearer JWT (admin/teacher for write; any authenticated for read)

## Standard CRUD

### POST /api/exams
```json
{
  "batch_id": "uuid",
  "title": "CCNA Midterm",
  "exam_type": "midterm",
  "date": "2026-03-15",
  "total_marks": 100
}
```
**Response 201**: Exam object.

### GET /api/exams
**Query**: `?page=1&limit=20&batch_id=uuid&exam_type=midterm`
**Response 200**: Paginated list.

### GET /api/exams/{id}
**Response 200**: Exam with batch and course details.

### PUT /api/exams/{id}
**Response 200**: Updated exam.

### DELETE /api/exams/{id}
**Response 204**: No content.
**Response 409**: `{ "detail": "Cannot delete exam with recorded results" }`

## Extra Endpoints

### POST /api/exams/{id}/results
Submit results for multiple students.
```json
{
  "results": [
    { "student_id": "uuid-1", "marks_obtained": 85, "grade": "A", "remarks": "Excellent" },
    { "student_id": "uuid-2", "marks_obtained": 62, "grade": "B", "remarks": "" }
  ]
}
```
**Response 200**:
```json
{
  "exam_id": "uuid",
  "submitted": 2,
  "errors": []
}
```

### GET /api/exams/{id}/results
**Response 200**:
```json
{
  "exam_id": "uuid",
  "exam_title": "CCNA Midterm",
  "total_marks": 100,
  "results": [
    {
      "student_id": "uuid",
      "student_name": "Ali Ahmed",
      "marks_obtained": 85,
      "percentage": 85.0,
      "grade": "A",
      "remarks": "Excellent"
    }
  ],
  "stats": {
    "average": 73.5,
    "highest": 95,
    "lowest": 42,
    "pass_rate": 85.0
  }
}
```
