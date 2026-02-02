# Data Model: Corvit Agentic System — Phase 1

**Branch**: `001-corvit-agentic-system` | **Date**: 2026-02-02
**Source**: spec.md Key Entities + Blueprint Section 5

## Entity Relationship Overview

```
User (auth)
  │
  ├── Student ──┬── Enrollment ──── Batch ──── Course
  │             ├── Attendance        │          │
  │             ├── Fee               │          │
  │             ├── ExamResult ── Exam (via Batch)
  │             ├── Certification
  │             ├── Project
  │             └── LabBooking
  │
  ├── Teacher ──── Batch
  │
  └── Admin (manages all)

Agent System:
  Director Agent ──┬── Message (agent-to-agent)
                   ├── AgentMemory (state)
                   └── EventLog (audit)

Infrastructure:
  Equipment (lab inventory)
```

## Entities (17 Tables)

### 1. User

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK, auto-generated | Unique identifier |
| username | String(50) | UNIQUE, NOT NULL | Login username |
| email | String(255) | UNIQUE, NOT NULL | Email address |
| hashed_password | String(255) | NOT NULL | bcrypt hash |
| role | Enum(admin, teacher, student) | NOT NULL, DEFAULT student | Access role |
| is_active | Boolean | DEFAULT true | Account status |
| created_at | DateTime | auto, UTC | Creation timestamp |
| updated_at | DateTime | auto, UTC | Last update timestamp |

**Validation**: Email format, username 3-50 chars alphanumeric, password min 8 chars (validated pre-hash).

---

### 2. Student

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| name | String(100) | NOT NULL | Full name |
| email | String(255) | UNIQUE, NOT NULL | Contact email |
| phone | String(20) | NOT NULL | Phone number |
| cnic | String(15) | UNIQUE | National ID (XXXXX-XXXXXXX-X) |
| guardian_name | String(100) | | Parent/guardian name |
| guardian_phone | String(20) | | Guardian contact |
| address | Text | | Residential address |
| enrollment_date | Date | DEFAULT today | Date joined institute |
| status | Enum(active, graduated, dropped) | DEFAULT active | Current status |
| user_id | UUID | FK → User.id, NULLABLE | Linked auth account |
| created_at | DateTime | auto, UTC | |
| updated_at | DateTime | auto, UTC | |

**Relationships**: Has many Enrollments, Attendance, Fees, ExamResults, Certifications, Projects, LabBookings.
**State transitions**: active → graduated, active → dropped.

---

### 3. Teacher

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| name | String(100) | NOT NULL | Full name |
| email | String(255) | UNIQUE, NOT NULL | Contact email |
| phone | String(20) | NOT NULL | Phone number |
| specialization | String(100) | | Primary expertise area |
| qualification | String(200) | | Degrees/certifications |
| joining_date | Date | DEFAULT today | Date joined |
| is_active | Boolean | DEFAULT true | Employment status |
| user_id | UUID | FK → User.id, NULLABLE | Linked auth account |
| created_at | DateTime | auto, UTC | |
| updated_at | DateTime | auto, UTC | |

**Relationships**: Has many Batches.

---

### 4. Course

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| name | String(100) | NOT NULL | Course title (e.g., "CCNA") |
| code | String(20) | UNIQUE, NOT NULL | Short code (e.g., "CCNA-01") |
| duration_weeks | Integer | NOT NULL | Course length in weeks |
| fee_amount | Decimal(10,2) | NOT NULL | Course fee in PKR |
| description | Text | | Detailed description |
| category | String(50) | | Category (Networking, AI, Security, Cloud) |
| is_active | Boolean | DEFAULT true | Currently offered |
| created_at | DateTime | auto, UTC | |
| updated_at | DateTime | auto, UTC | |

**Relationships**: Has many Batches.

---

### 5. Batch

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| course_id | UUID | FK → Course.id, NOT NULL | Parent course |
| teacher_id | UUID | FK → Teacher.id, NOT NULL | Assigned teacher |
| name | String(50) | NOT NULL | Batch identifier (e.g., "CCNA-Batch-1") |
| room | String(50) | | Room/lab assignment |
| schedule_days | String(50) | | Days (e.g., "Mon,Wed,Fri") |
| schedule_time | String(20) | | Time slot (e.g., "10:00-12:00") |
| start_date | Date | NOT NULL | Batch start |
| end_date | Date | | Batch end |
| max_capacity | Integer | DEFAULT 30 | Maximum students |
| status | Enum(upcoming, active, completed) | DEFAULT upcoming | |
| created_at | DateTime | auto, UTC | |
| updated_at | DateTime | auto, UTC | |

**Relationships**: Belongs to Course, belongs to Teacher. Has many Enrollments, Attendance, Exams.
**Validation**: end_date > start_date, max_capacity > 0.
**State transitions**: upcoming → active → completed.

---

### 6. Enrollment

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| student_id | UUID | FK → Student.id, NOT NULL | |
| batch_id | UUID | FK → Batch.id, NOT NULL | |
| enrollment_date | Date | DEFAULT today | |
| status | Enum(active, completed, dropped) | DEFAULT active | |
| created_at | DateTime | auto, UTC | |
| updated_at | DateTime | auto, UTC | |

**Constraints**: UNIQUE(student_id, batch_id) — a student can only enroll once per batch.
**Validation**: Batch must not be at max_capacity when enrolling.
**State transitions**: active → completed, active → dropped.

---

### 7. Attendance

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| student_id | UUID | FK → Student.id, NOT NULL | |
| batch_id | UUID | FK → Batch.id, NOT NULL | |
| date | Date | NOT NULL | Attendance date |
| status | Enum(present, absent, late, excused) | NOT NULL | |
| marked_by | UUID | FK → User.id, NULLABLE | Who marked it |
| created_at | DateTime | auto, UTC | |

**Constraints**: UNIQUE(student_id, batch_id, date) — one record per student per batch per day.
**Rule engine triggers**:
- < 85% → yellow warning
- < 75% → orange warning (student + mentor)
- < 60% → red (escalate to Director Agent)
- 3 consecutive absences → red (parent notification)

---

### 8. Fee

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| student_id | UUID | FK → Student.id, NOT NULL | |
| course_id | UUID | FK → Course.id, NOT NULL | |
| amount | Decimal(10,2) | NOT NULL | Total fee amount |
| due_date | Date | NOT NULL | Payment deadline |
| paid_amount | Decimal(10,2) | DEFAULT 0 | Amount paid so far |
| paid_date | Date | NULLABLE | Date of last payment |
| status | Enum(pending, partial, paid, overdue) | DEFAULT pending | |
| created_at | DateTime | auto, UTC | |
| updated_at | DateTime | auto, UTC | |

**Validation**: paid_amount <= amount, paid_amount >= 0.
**State transitions**: pending → partial → paid; pending → overdue; partial → overdue.
**Rule engine triggers**:
- 7 days overdue → yellow (SMS reminder)
- 15 days overdue → orange (SMS to student + parent)
- 30 days overdue → red (escalate to Director Agent)

---

### 9. Exam

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| batch_id | UUID | FK → Batch.id, NOT NULL | |
| title | String(100) | NOT NULL | Exam name |
| exam_type | Enum(quiz, midterm, final, practical) | NOT NULL | |
| date | Date | NOT NULL | Scheduled date |
| total_marks | Integer | NOT NULL | Maximum marks |
| created_at | DateTime | auto, UTC | |
| updated_at | DateTime | auto, UTC | |

**Validation**: total_marks > 0, date >= today (for creation).

---

### 10. ExamResult

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| exam_id | UUID | FK → Exam.id, NOT NULL | |
| student_id | UUID | FK → Student.id, NOT NULL | |
| marks_obtained | Decimal(5,2) | NOT NULL | Score |
| grade | String(5) | NULLABLE | Letter grade (A, B, C, D, F) |
| remarks | Text | NULLABLE | Teacher comments |
| created_at | DateTime | auto, UTC | |

**Constraints**: UNIQUE(exam_id, student_id). marks_obtained <= Exam.total_marks.

---

### 11. Certification

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| student_id | UUID | FK → Student.id, NOT NULL | |
| name | String(100) | NOT NULL | Cert name (e.g., "CCNA") |
| vendor | String(100) | | Issuing body (e.g., "Cisco") |
| issue_date | Date | | |
| expiry_date | Date | NULLABLE | |
| created_at | DateTime | auto, UTC | |

---

### 12. LabBooking

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| student_id | UUID | FK → Student.id, NULLABLE | Individual booking |
| batch_id | UUID | FK → Batch.id, NULLABLE | Batch booking |
| lab | String(50) | NOT NULL | Lab name/number |
| date | Date | NOT NULL | Booking date |
| time_slot | String(20) | NOT NULL | Time slot |
| equipment_list | Text | NULLABLE | Required equipment |
| status | Enum(booked, completed, cancelled) | DEFAULT booked | |
| created_at | DateTime | auto, UTC | |

**Validation**: Either student_id or batch_id must be set (not both null).

---

### 13. Equipment

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| name | String(100) | NOT NULL | Equipment name |
| lab | String(50) | NOT NULL | Lab location |
| quantity | Integer | DEFAULT 1 | Total count |
| working_count | Integer | DEFAULT 1 | Functional count |
| status | Enum(available, limited, unavailable) | DEFAULT available | |
| created_at | DateTime | auto, UTC | |
| updated_at | DateTime | auto, UTC | |

**Validation**: working_count <= quantity.

---

### 14. Project

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| student_id | UUID | FK → Student.id, NOT NULL | |
| batch_id | UUID | FK → Batch.id, NOT NULL | |
| title | String(200) | NOT NULL | Project title |
| description | Text | NULLABLE | |
| status | Enum(proposed, in_progress, submitted, graded) | DEFAULT proposed | |
| grade | String(5) | NULLABLE | |
| submitted_at | DateTime | NULLABLE | |
| created_at | DateTime | auto, UTC | |
| updated_at | DateTime | auto, UTC | |

**State transitions**: proposed → in_progress → submitted → graded.

---

### 15. Message (Agent-to-Agent)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| sender_agent | String(50) | NOT NULL | Sending agent ID |
| receiver_agent | String(50) | NOT NULL | Target agent ID |
| content | Text | NOT NULL | Message body |
| message_type | Enum(query, response, notification, escalation) | NOT NULL | |
| status | Enum(sent, delivered, processed) | DEFAULT sent | |
| metadata | JSON | NULLABLE | Extra structured data |
| created_at | DateTime | auto, UTC | |

---

### 16. AgentMemory

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| agent_id | String(50) | NOT NULL | Agent identifier |
| key | String(100) | NOT NULL | Memory key |
| value | Text | NOT NULL | Memory value |
| context | String(100) | NULLABLE | Context scope |
| created_at | DateTime | auto, UTC | |
| updated_at | DateTime | auto, UTC | |

**Constraints**: UNIQUE(agent_id, key, context).

---

### 17. EventLog

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| event_type | String(50) | NOT NULL | Event category |
| actor | String(100) | NOT NULL | Who/what triggered it |
| target | String(100) | NULLABLE | Affected entity |
| details | JSON | NULLABLE | Structured event data |
| created_at | DateTime | auto, UTC | Timestamp |

**Index**: created_at DESC for recent activity queries, event_type for filtering.

---

## Indexes

| Table | Index | Columns | Purpose |
|-------|-------|---------|---------|
| Student | idx_student_email | email | Unique lookup |
| Student | idx_student_cnic | cnic | Unique lookup |
| Attendance | idx_attendance_student_batch | student_id, batch_id, date | Daily queries |
| Fee | idx_fee_status | status | Overdue queries |
| Fee | idx_fee_due_date | due_date | Rule engine checks |
| Enrollment | idx_enrollment_student | student_id | Student history |
| Enrollment | idx_enrollment_batch | batch_id | Batch roster |
| EventLog | idx_event_created | created_at DESC | Recent activity |
| EventLog | idx_event_type | event_type | Filtered queries |
| ExamResult | idx_result_exam | exam_id | Results per exam |
| Batch | idx_batch_course | course_id | Course batches |
| Batch | idx_batch_teacher | teacher_id | Teacher schedule |
