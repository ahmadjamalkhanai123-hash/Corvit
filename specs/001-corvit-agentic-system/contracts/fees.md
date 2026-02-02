# API Contract: Fees

**Base**: `/api/fees`
**Auth**: Bearer JWT (admin for write; any authenticated for read)

## Standard CRUD

### POST /api/fees
```json
{
  "student_id": "uuid",
  "course_id": "uuid",
  "amount": 25000.00,
  "due_date": "2026-03-01"
}
```
**Response 201**: Fee record.

### GET /api/fees
**Query**: `?page=1&limit=20&student_id=uuid&status=overdue&sort_by=due_date`
**Response 200**: Paginated list.

### GET /api/fees/{id}
**Response 200**: Single fee record.

### PUT /api/fees/{id}
**Response 200**: Updated fee.

### DELETE /api/fees/{id}
**Response 204**: No content.

## Extra Endpoints

### POST /api/fees/{id}/pay
Record a payment.
```json
{
  "amount": 10000.00,
  "payment_date": "2026-02-02"
}
```
**Response 200**:
```json
{
  "id": "uuid",
  "amount": 25000.00,
  "paid_amount": 10000.00,
  "remaining": 15000.00,
  "status": "partial",
  "paid_date": "2026-02-02"
}
```
**Response 422**: `{ "detail": "Payment exceeds remaining balance" }`

### GET /api/fees/overdue
**Response 200**:
```json
{
  "items": [
    {
      "id": "uuid",
      "student_name": "Ali Ahmed",
      "course_name": "CCNA",
      "amount": 25000.00,
      "paid_amount": 0,
      "due_date": "2026-01-01",
      "days_overdue": 32,
      "alert_level": "red",
      "status": "overdue"
    }
  ],
  "total_overdue_count": 5,
  "total_overdue_amount": 125000.00
}
```
