import enum
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.connection import Base


# ── Enums ──────────────────────────────────────────────────────────────


class UserRole(str, enum.Enum):
    admin = "admin"
    teacher = "teacher"
    student = "student"


class StudentStatus(str, enum.Enum):
    active = "active"
    graduated = "graduated"
    dropped = "dropped"


class BatchStatus(str, enum.Enum):
    upcoming = "upcoming"
    active = "active"
    completed = "completed"


class EnrollmentStatus(str, enum.Enum):
    active = "active"
    completed = "completed"
    dropped = "dropped"


class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"
    late = "late"
    excused = "excused"


class FeeStatus(str, enum.Enum):
    pending = "pending"
    partial = "partial"
    paid = "paid"
    overdue = "overdue"


class ExamType(str, enum.Enum):
    quiz = "quiz"
    midterm = "midterm"
    final = "final"
    practical = "practical"


class LabBookingStatus(str, enum.Enum):
    booked = "booked"
    completed = "completed"
    cancelled = "cancelled"


class EquipmentStatus(str, enum.Enum):
    available = "available"
    limited = "limited"
    unavailable = "unavailable"


class ProjectStatus(str, enum.Enum):
    proposed = "proposed"
    in_progress = "in_progress"
    submitted = "submitted"
    graded = "graded"


class MessageType(str, enum.Enum):
    query = "query"
    response = "response"
    notification = "notification"
    escalation = "escalation"


class MessageStatus(str, enum.Enum):
    sent = "sent"
    delivered = "delivered"
    processed = "processed"


# ── Helper ─────────────────────────────────────────────────────────────


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


# ── Models ─────────────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.student)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    student: Mapped["Student | None"] = relationship(back_populates="user")
    teacher: Mapped["Teacher | None"] = relationship(back_populates="user")


class Student(Base):
    __tablename__ = "students"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    cnic: Mapped[str | None] = mapped_column(String(15), unique=True)
    guardian_name: Mapped[str | None] = mapped_column(String(100))
    guardian_phone: Mapped[str | None] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(Text)
    enrollment_date: Mapped[date] = mapped_column(Date, default=date.today)
    status: Mapped[StudentStatus] = mapped_column(Enum(StudentStatus), default=StudentStatus.active)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user: Mapped["User | None"] = relationship(back_populates="student")
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="student")
    attendance_records: Mapped[list["Attendance"]] = relationship(back_populates="student")
    fees: Mapped[list["Fee"]] = relationship(back_populates="student")
    exam_results: Mapped[list["ExamResult"]] = relationship(back_populates="student")
    certifications: Mapped[list["Certification"]] = relationship(back_populates="student")
    projects: Mapped[list["Project"]] = relationship(back_populates="student")
    lab_bookings: Mapped[list["LabBooking"]] = relationship(back_populates="student")


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    specialization: Mapped[str | None] = mapped_column(String(100))
    qualification: Mapped[str | None] = mapped_column(String(200))
    joining_date: Mapped[date] = mapped_column(Date, default=date.today)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user: Mapped["User | None"] = relationship(back_populates="teacher")
    batches: Mapped[list["Batch"]] = relationship(back_populates="teacher")


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    duration_weeks: Mapped[int] = mapped_column(Integer, nullable=False)
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(String(50))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    batches: Mapped[list["Batch"]] = relationship(back_populates="course")
    fees: Mapped[list["Fee"]] = relationship(back_populates="course")


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("teachers.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    room: Mapped[str | None] = mapped_column(String(50))
    schedule_days: Mapped[str | None] = mapped_column(String(50))
    schedule_time: Mapped[str | None] = mapped_column(String(20))
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    max_capacity: Mapped[int] = mapped_column(Integer, default=30)
    status: Mapped[BatchStatus] = mapped_column(Enum(BatchStatus), default=BatchStatus.upcoming)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    course: Mapped["Course"] = relationship(back_populates="batches")
    teacher: Mapped["Teacher"] = relationship(back_populates="batches")
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="batch")
    attendance_records: Mapped[list["Attendance"]] = relationship(back_populates="batch")
    exams: Mapped[list["Exam"]] = relationship(back_populates="batch")
    projects: Mapped[list["Project"]] = relationship(back_populates="batch")
    lab_bookings: Mapped[list["LabBooking"]] = relationship(back_populates="batch")

    __table_args__ = (
        Index("idx_batch_course", "course_id"),
        Index("idx_batch_teacher", "teacher_id"),
    )


class Enrollment(Base):
    __tablename__ = "enrollments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    batch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("batches.id"), nullable=False)
    enrollment_date: Mapped[date] = mapped_column(Date, default=date.today)
    status: Mapped[EnrollmentStatus] = mapped_column(Enum(EnrollmentStatus), default=EnrollmentStatus.active)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    student: Mapped["Student"] = relationship(back_populates="enrollments")
    batch: Mapped["Batch"] = relationship(back_populates="enrollments")

    __table_args__ = (
        UniqueConstraint("student_id", "batch_id", name="uq_enrollment_student_batch"),
        Index("idx_enrollment_student", "student_id"),
        Index("idx_enrollment_batch", "batch_id"),
    )


class Attendance(Base):
    __tablename__ = "attendance"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    batch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("batches.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[AttendanceStatus] = mapped_column(Enum(AttendanceStatus), nullable=False)
    marked_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    student: Mapped["Student"] = relationship(back_populates="attendance_records")
    batch: Mapped["Batch"] = relationship(back_populates="attendance_records")

    __table_args__ = (
        UniqueConstraint("student_id", "batch_id", "date", name="uq_attendance_student_batch_date"),
        Index("idx_attendance_student_batch", "student_id", "batch_id", "date"),
    )


class Fee(Base):
    __tablename__ = "fees"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    course_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("courses.id"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    paid_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[FeeStatus] = mapped_column(Enum(FeeStatus), default=FeeStatus.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    student: Mapped["Student"] = relationship(back_populates="fees")
    course: Mapped["Course"] = relationship(back_populates="fees")

    __table_args__ = (
        Index("idx_fee_status", "status"),
        Index("idx_fee_due_date", "due_date"),
    )


class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    batch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("batches.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    exam_type: Mapped[ExamType] = mapped_column(Enum(ExamType), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    total_marks: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    batch: Mapped["Batch"] = relationship(back_populates="exams")
    results: Mapped[list["ExamResult"]] = relationship(back_populates="exam")


class ExamResult(Base):
    __tablename__ = "exam_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    exam_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("exams.id"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    marks_obtained: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    grade: Mapped[str | None] = mapped_column(String(5))
    remarks: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    exam: Mapped["Exam"] = relationship(back_populates="results")
    student: Mapped["Student"] = relationship(back_populates="exam_results")

    __table_args__ = (
        UniqueConstraint("exam_id", "student_id", name="uq_result_exam_student"),
        Index("idx_result_exam", "exam_id"),
    )


class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    vendor: Mapped[str | None] = mapped_column(String(100))
    issue_date: Mapped[date | None] = mapped_column(Date)
    expiry_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    student: Mapped["Student"] = relationship(back_populates="certifications")


class LabBooking(Base):
    __tablename__ = "lab_bookings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    student_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id"))
    batch_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("batches.id"))
    lab: Mapped[str] = mapped_column(String(50), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    time_slot: Mapped[str] = mapped_column(String(20), nullable=False)
    equipment_list: Mapped[str | None] = mapped_column(Text)
    status: Mapped[LabBookingStatus] = mapped_column(Enum(LabBookingStatus), default=LabBookingStatus.booked)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    student: Mapped["Student | None"] = relationship(back_populates="lab_bookings")
    batch: Mapped["Batch | None"] = relationship(back_populates="lab_bookings")


class Equipment(Base):
    __tablename__ = "equipment"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    lab: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    working_count: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[EquipmentStatus] = mapped_column(Enum(EquipmentStatus), default=EquipmentStatus.available)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    batch_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("batches.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus), default=ProjectStatus.proposed)
    grade: Mapped[str | None] = mapped_column(String(5))
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    student: Mapped["Student"] = relationship(back_populates="projects")
    batch: Mapped["Batch"] = relationship(back_populates="projects")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    sender_agent: Mapped[str] = mapped_column(String(50), nullable=False)
    receiver_agent: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    message_type: Mapped[MessageType] = mapped_column(Enum(MessageType), nullable=False)
    status: Mapped[MessageStatus] = mapped_column(Enum(MessageStatus), default=MessageStatus.sent)
    extra_data: Mapped[dict | None] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AgentMemory(Base):
    __tablename__ = "agent_memory"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    agent_id: Mapped[str] = mapped_column(String(50), nullable=False)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        UniqueConstraint("agent_id", "key", "context", name="uq_agent_memory_key"),
    )


class EventLog(Base):
    __tablename__ = "event_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    actor: Mapped[str] = mapped_column(String(100), nullable=False)
    target: Mapped[str | None] = mapped_column(String(100))
    details: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("idx_event_created", "created_at"),
        Index("idx_event_type", "event_type"),
    )
