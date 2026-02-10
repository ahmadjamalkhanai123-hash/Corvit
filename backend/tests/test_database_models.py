import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.settings import get_settings
from src.database.connection import Base
from src.database.models import (
    AgentMemory,
    Attendance,
    AttendanceStatus,
    Batch,
    BatchStatus,
    Certification,
    Course,
    Enrollment,
    EnrollmentStatus,
    Equipment,
    EquipmentStatus,
    Exam,
    ExamResult,
    ExamType,
    EventLog,
    Fee,
    FeeStatus,
    LabBooking,
    Message,
    MessageStatus,
    MessageType,
    Project,
    ProjectStatus,
    Student,
    StudentStatus,
    Teacher,
    User,
    UserRole,
)

from sqlalchemy import pool

settings = get_settings()


@pytest_asyncio.fixture(loop_scope="function")
async def session():
    engine = create_async_engine(settings.database_url, echo=False, poolclass=pool.NullPool)
    async with engine.begin() as conn:
        s = AsyncSession(bind=conn, expire_on_commit=False)
        yield s
        await s.close()
        await conn.rollback()
    await engine.dispose()


# ── Model creation tests ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_user(session: AsyncSession):
    user = User(username="admin1", email="admin@corvit.pk", hashed_password="hash123", role=UserRole.admin)
    session.add(user)
    await session.flush()
    assert user.id is not None
    assert user.role == UserRole.admin
    assert user.is_active is True
    assert user.created_at is not None


@pytest.mark.asyncio
async def test_create_student(session: AsyncSession):
    student = Student(name="Ali Ahmed", email="ali@test.com", phone="03001234567")
    session.add(student)
    await session.flush()
    assert student.id is not None
    assert student.status == StudentStatus.active
    assert student.enrollment_date == date.today()


@pytest.mark.asyncio
async def test_create_teacher(session: AsyncSession):
    teacher = Teacher(name="Haleema Sayyar", email="haleema@corvit.pk", phone="03009876543", specialization="Networking")
    session.add(teacher)
    await session.flush()
    assert teacher.id is not None
    assert teacher.is_active is True


@pytest.mark.asyncio
async def test_create_course(session: AsyncSession):
    course = Course(name="CCNA Test", code=f"TEST-{uuid.uuid4().hex[:6]}", duration_weeks=12, fee_amount=Decimal("25000.00"), category="Networking")
    session.add(course)
    await session.flush()
    assert course.id is not None
    assert course.is_active is True


@pytest.mark.asyncio
async def test_create_batch_with_relationships(session: AsyncSession):
    teacher = Teacher(name="T1", email=f"t1-{uuid.uuid4().hex[:8]}@test.com", phone="000")
    course = Course(name="C1", code=f"C-{uuid.uuid4().hex[:6]}", duration_weeks=8, fee_amount=Decimal("10000"))
    session.add_all([teacher, course])
    await session.flush()

    batch = Batch(
        course_id=course.id,
        teacher_id=teacher.id,
        name="Batch-1",
        start_date=date(2026, 1, 15),
        status=BatchStatus.active,
    )
    session.add(batch)
    await session.flush()
    assert batch.id is not None
    assert batch.max_capacity == 30


@pytest.mark.asyncio
async def test_enrollment_relationship(session: AsyncSession):
    student = Student(name="S1", email=f"s1-{uuid.uuid4().hex[:8]}@test.com", phone="000")
    teacher = Teacher(name="T2", email=f"t2-{uuid.uuid4().hex[:8]}@test.com", phone="000")
    course = Course(name="C2", code=f"C-{uuid.uuid4().hex[:6]}", duration_weeks=8, fee_amount=Decimal("10000"))
    session.add_all([student, teacher, course])
    await session.flush()

    batch = Batch(course_id=course.id, teacher_id=teacher.id, name="B2", start_date=date(2026, 2, 1))
    session.add(batch)
    await session.flush()

    enrollment = Enrollment(student_id=student.id, batch_id=batch.id)
    session.add(enrollment)
    await session.flush()
    assert enrollment.status == EnrollmentStatus.active


@pytest.mark.asyncio
async def test_enrollment_unique_constraint(session: AsyncSession):
    student = Student(name="S2", email=f"s2-{uuid.uuid4().hex[:8]}@test.com", phone="000")
    teacher = Teacher(name="T3", email=f"t3-{uuid.uuid4().hex[:8]}@test.com", phone="000")
    course = Course(name="C3", code=f"C-{uuid.uuid4().hex[:6]}", duration_weeks=8, fee_amount=Decimal("10000"))
    session.add_all([student, teacher, course])
    await session.flush()

    batch = Batch(course_id=course.id, teacher_id=teacher.id, name="B3", start_date=date(2026, 2, 1))
    session.add(batch)
    await session.flush()

    e1 = Enrollment(student_id=student.id, batch_id=batch.id)
    session.add(e1)
    await session.flush()

    e2 = Enrollment(student_id=student.id, batch_id=batch.id)
    session.add(e2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_student_email_unique(session: AsyncSession):
    unique_email = f"dup-{uuid.uuid4().hex[:8]}@test.com"
    s1 = Student(name="A", email=unique_email, phone="000")
    session.add(s1)
    await session.flush()

    s2 = Student(name="B", email=unique_email, phone="111")
    session.add(s2)
    with pytest.raises(IntegrityError):
        await session.flush()


@pytest.mark.asyncio
async def test_create_attendance(session: AsyncSession):
    student = Student(name="S3", email=f"s3-{uuid.uuid4().hex[:8]}@test.com", phone="000")
    teacher = Teacher(name="T4", email=f"t4-{uuid.uuid4().hex[:8]}@test.com", phone="000")
    course = Course(name="C4", code=f"C-{uuid.uuid4().hex[:6]}", duration_weeks=8, fee_amount=Decimal("10000"))
    session.add_all([student, teacher, course])
    await session.flush()
    batch = Batch(course_id=course.id, teacher_id=teacher.id, name="B4", start_date=date(2026, 2, 1))
    session.add(batch)
    await session.flush()

    att = Attendance(student_id=student.id, batch_id=batch.id, date=date(2026, 2, 3), status=AttendanceStatus.present)
    session.add(att)
    await session.flush()
    assert att.id is not None


@pytest.mark.asyncio
async def test_create_fee(session: AsyncSession):
    student = Student(name="S4", email=f"s4-{uuid.uuid4().hex[:8]}@test.com", phone="000")
    course = Course(name="C5", code=f"C-{uuid.uuid4().hex[:6]}", duration_weeks=8, fee_amount=Decimal("20000"))
    session.add_all([student, course])
    await session.flush()

    fee = Fee(student_id=student.id, course_id=course.id, amount=Decimal("20000"), due_date=date(2026, 3, 1))
    session.add(fee)
    await session.flush()
    assert fee.status == FeeStatus.pending
    assert fee.paid_amount == Decimal("0")


@pytest.mark.asyncio
async def test_create_exam_and_result(session: AsyncSession):
    teacher = Teacher(name="T5", email=f"t5-{uuid.uuid4().hex[:8]}@test.com", phone="000")
    course = Course(name="C6", code=f"C-{uuid.uuid4().hex[:6]}", duration_weeks=8, fee_amount=Decimal("10000"))
    session.add_all([teacher, course])
    await session.flush()
    batch = Batch(course_id=course.id, teacher_id=teacher.id, name="B5", start_date=date(2026, 2, 1))
    session.add(batch)
    await session.flush()

    exam = Exam(batch_id=batch.id, title="Midterm", exam_type=ExamType.midterm, date=date(2026, 3, 15), total_marks=100)
    session.add(exam)
    await session.flush()

    student = Student(name="S5", email=f"s5-{uuid.uuid4().hex[:8]}@test.com", phone="000")
    session.add(student)
    await session.flush()

    result = ExamResult(exam_id=exam.id, student_id=student.id, marks_obtained=Decimal("85.50"), grade="A")
    session.add(result)
    await session.flush()
    assert result.id is not None


@pytest.mark.asyncio
async def test_create_agent_models(session: AsyncSession):
    msg = Message(sender_agent="director", receiver_agent="attendance_agent", content="Check alerts", message_type=MessageType.query)
    session.add(msg)
    await session.flush()
    assert msg.status == MessageStatus.sent

    mem = AgentMemory(agent_id="director", key="last_check", value="2026-02-03T00:00:00Z")
    session.add(mem)
    await session.flush()
    assert mem.id is not None

    log = EventLog(event_type="attendance_alert", actor="rule_engine", target="student:123", details={"level": "red"})
    session.add(log)
    await session.flush()
    assert log.id is not None


@pytest.mark.asyncio
async def test_create_equipment(session: AsyncSession):
    eq = Equipment(name="Cisco Router 2901", lab="Lab-1", quantity=10, working_count=8, status=EquipmentStatus.available)
    session.add(eq)
    await session.flush()
    assert eq.id is not None


@pytest.mark.asyncio
async def test_create_certification(session: AsyncSession):
    student = Student(name="S6", email=f"s6-{uuid.uuid4().hex[:8]}@test.com", phone="000")
    session.add(student)
    await session.flush()
    cert = Certification(student_id=student.id, name="CCNA", vendor="Cisco", issue_date=date(2026, 1, 1))
    session.add(cert)
    await session.flush()
    assert cert.id is not None


@pytest.mark.asyncio
async def test_create_lab_booking(session: AsyncSession):
    student = Student(name="S7", email=f"s7-{uuid.uuid4().hex[:8]}@test.com", phone="000")
    session.add(student)
    await session.flush()
    booking = LabBooking(student_id=student.id, lab="Lab-2", date=date(2026, 2, 5), time_slot="10:00-12:00")
    session.add(booking)
    await session.flush()
    assert booking.id is not None


@pytest.mark.asyncio
async def test_create_project(session: AsyncSession):
    student = Student(name="S8", email=f"s8-{uuid.uuid4().hex[:8]}@test.com", phone="000")
    teacher = Teacher(name="T6", email=f"t6-{uuid.uuid4().hex[:8]}@test.com", phone="000")
    course = Course(name="C7", code=f"C-{uuid.uuid4().hex[:6]}", duration_weeks=8, fee_amount=Decimal("10000"))
    session.add_all([student, teacher, course])
    await session.flush()
    batch = Batch(course_id=course.id, teacher_id=teacher.id, name="B6", start_date=date(2026, 2, 1))
    session.add(batch)
    await session.flush()
    project = Project(student_id=student.id, batch_id=batch.id, title="Network Monitoring Tool")
    session.add(project)
    await session.flush()
    assert project.status == ProjectStatus.proposed


@pytest.mark.asyncio
async def test_timestamps_auto_set(session: AsyncSession):
    user = User(username=f"ts-{uuid.uuid4().hex[:8]}", email=f"ts-{uuid.uuid4().hex[:8]}@test.com", hashed_password="hash")
    session.add(user)
    await session.flush()
    assert user.created_at is not None
    assert user.updated_at is not None
    assert isinstance(user.created_at, datetime)
