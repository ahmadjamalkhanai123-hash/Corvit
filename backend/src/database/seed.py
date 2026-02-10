import uuid
from datetime import date, timedelta
from decimal import Decimal
import random

import bcrypt as _bcrypt
from sqlalchemy.ext.asyncio import AsyncSession


def _hash_pw(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()

from src.database.models import (
    Attendance,
    AttendanceStatus,
    Batch,
    BatchStatus,
    Course,
    Enrollment,
    EnrollmentStatus,
    Equipment,
    EquipmentStatus,
    Exam,
    ExamResult,
    ExamType,
    Fee,
    FeeStatus,
    Student,
    StudentStatus,
    Teacher,
    User,
    UserRole,
)


async def seed_database(session: AsyncSession) -> dict:
    """Populate database with sample data per Blueprint Section 12."""

    stats: dict[str, int] = {}

    # ── Admin user ─────────────────────────────────────────────────────
    admin_user = User(
        username="admin",
        email="admin@corvitsystems.com",
        hashed_password=_hash_pw("admin123"),
        role=UserRole.admin,
    )
    session.add(admin_user)
    await session.flush()
    stats["users"] = 1

    # ── 5 Courses ──────────────────────────────────────────────────────
    courses_data = [
        ("CCNA", "CCNA-01", 12, Decimal("25000.00"), "Cisco Certified Network Associate — routing, switching, network fundamentals", "Networking"),
        ("Ethical Hacking", "CEH-01", 10, Decimal("30000.00"), "Certified Ethical Hacker — penetration testing, vulnerability assessment", "Security"),
        ("AI & Machine Learning", "AI-01", 16, Decimal("35000.00"), "Python-based AI/ML — scikit-learn, TensorFlow, NLP basics", "AI"),
        ("Cloud Computing", "AWS-01", 12, Decimal("28000.00"), "AWS Solutions Architect — EC2, S3, VPC, IAM, Lambda", "Cloud"),
        ("Web Development", "WEB-01", 14, Decimal("20000.00"), "Full-stack web development — HTML, CSS, JS, React, Node.js", "Development"),
    ]
    courses = []
    for name, code, weeks, fee, desc, cat in courses_data:
        c = Course(name=name, code=code, duration_weeks=weeks, fee_amount=fee, description=desc, category=cat)
        courses.append(c)
    session.add_all(courses)
    await session.flush()
    stats["courses"] = len(courses)

    # ── 4 Teachers ─────────────────────────────────────────────────────
    teachers_data = [
        ("Haleema Sayyar", "haleema@corvitsystems.com", "03001111111", "Networking", "CCNA, CCNP"),
        ("Muhammad Arslan", "arslan@corvitsystems.com", "03002222222", "Cybersecurity", "CEH, OSCP"),
        ("Sara Khan", "sara@corvitsystems.com", "03003333333", "AI/ML", "MS Computer Science"),
        ("Usman Ali", "usman@corvitsystems.com", "03004444444", "Cloud", "AWS SAA, Azure AZ-104"),
    ]
    teachers = []
    teacher_users = []
    for name, email, phone, spec, qual in teachers_data:
        u = User(username=email.split("@")[0], email=email, hashed_password=_hash_pw("teacher123"), role=UserRole.teacher)
        teacher_users.append(u)
    session.add_all(teacher_users)
    await session.flush()

    for i, (name, email, phone, spec, qual) in enumerate(teachers_data):
        t = Teacher(name=name, email=f"teacher-{email}", phone=phone, specialization=spec, qualification=qual, user_id=teacher_users[i].id)
        teachers.append(t)
    session.add_all(teachers)
    await session.flush()
    stats["teachers"] = len(teachers)
    stats["users"] += len(teacher_users)

    # ── 5 Batches ──────────────────────────────────────────────────────
    today = date.today()
    batches_data = [
        (courses[0], teachers[0], "CCNA-Batch-1", "Lab-1", "Mon,Wed,Fri", "10:00-12:00", today - timedelta(days=30)),
        (courses[1], teachers[1], "CEH-Batch-1", "Lab-2", "Tue,Thu", "14:00-16:00", today - timedelta(days=20)),
        (courses[2], teachers[2], "AI-Batch-1", "Lab-3", "Mon,Wed,Fri", "14:00-16:00", today - timedelta(days=15)),
        (courses[3], teachers[3], "AWS-Batch-1", "Lab-1", "Tue,Thu,Sat", "10:00-12:00", today - timedelta(days=25)),
        (courses[4], teachers[0], "WEB-Batch-1", "Lab-2", "Mon,Wed", "16:00-18:00", today - timedelta(days=10)),
    ]
    batches = []
    for course, teacher, name, room, days, time, start in batches_data:
        b = Batch(
            course_id=course.id,
            teacher_id=teacher.id,
            name=name,
            room=room,
            schedule_days=days,
            schedule_time=time,
            start_date=start,
            end_date=start + timedelta(weeks=course.duration_weeks),
            status=BatchStatus.active,
        )
        batches.append(b)
    session.add_all(batches)
    await session.flush()
    stats["batches"] = len(batches)

    # ── 20 Students ────────────────────────────────────────────────────
    student_names = [
        "Ali Ahmed", "Fatima Noor", "Hassan Raza", "Ayesha Bibi", "Bilal Khan",
        "Zainab Shah", "Umar Farooq", "Mahnoor Iqbal", "Tariq Mehmood", "Sana Malik",
        "Junaid Afridi", "Hira Gul", "Waqas Ahmad", "Nadia Parveen", "Faisal Yousaf",
        "Amina Khatoon", "Rizwan Ali", "Rabia Sultana", "Kamran Shah", "Mehwish Jan",
    ]
    students = []
    for i, name in enumerate(student_names):
        slug = name.lower().replace(" ", ".")
        s = Student(
            name=name,
            email=f"{slug}@student.corvit.pk",
            phone=f"030{i:08d}",
            cnic=f"17301-{1000000+i}-{i % 10}",
            guardian_name=f"Guardian of {name}",
            guardian_phone=f"030{i+50:08d}",
            address="Peshawar",
            status=StudentStatus.active,
        )
        students.append(s)
    session.add_all(students)
    await session.flush()
    stats["students"] = len(students)

    # ── Enrollments (4 students per batch) ─────────────────────────────
    enrollments = []
    for bi, batch in enumerate(batches):
        for si in range(4):
            student = students[bi * 4 + si]
            e = Enrollment(student_id=student.id, batch_id=batch.id, status=EnrollmentStatus.active)
            enrollments.append(e)
    session.add_all(enrollments)
    await session.flush()
    stats["enrollments"] = len(enrollments)

    # ── 30 days attendance per enrollment ──────────────────────────────
    random.seed(42)
    attendance_records = []
    for enrollment in enrollments:
        for day_offset in range(30):
            d = today - timedelta(days=30) + timedelta(days=day_offset)
            if d.weekday() >= 5:
                continue
            roll = random.random()
            if roll < 0.80:
                status = AttendanceStatus.present
            elif roll < 0.90:
                status = AttendanceStatus.late
            elif roll < 0.95:
                status = AttendanceStatus.excused
            else:
                status = AttendanceStatus.absent
            att = Attendance(
                student_id=enrollment.student_id,
                batch_id=enrollment.batch_id,
                date=d,
                status=status,
            )
            attendance_records.append(att)
    session.add_all(attendance_records)
    await session.flush()
    stats["attendance"] = len(attendance_records)

    # ── Fee records ────────────────────────────────────────────────────
    fee_records = []
    for enrollment in enrollments:
        batch = next(b for b in batches if b.id == enrollment.batch_id)
        course = next(c for c in courses if c.id == batch.course_id)
        paid_pct = random.choice([0, 0.5, 1.0])
        paid = course.fee_amount * Decimal(str(paid_pct))
        if paid_pct == 1.0:
            fee_status = FeeStatus.paid
        elif paid_pct > 0:
            fee_status = FeeStatus.partial
        else:
            fee_status = FeeStatus.pending
        f = Fee(
            student_id=enrollment.student_id,
            course_id=course.id,
            amount=course.fee_amount,
            due_date=batch.start_date + timedelta(days=30),
            paid_amount=paid,
            paid_date=today - timedelta(days=5) if paid > 0 else None,
            status=fee_status,
        )
        fee_records.append(f)
    session.add_all(fee_records)
    await session.flush()
    stats["fees"] = len(fee_records)

    # ── Exams + results ────────────────────────────────────────────────
    exam_records = []
    result_records = []
    for batch in batches:
        exam = Exam(
            batch_id=batch.id,
            title=f"{batch.name} Quiz 1",
            exam_type=ExamType.quiz,
            date=today - timedelta(days=5),
            total_marks=50,
        )
        exam_records.append(exam)
    session.add_all(exam_records)
    await session.flush()

    for exam in exam_records:
        batch_enrollments = [e for e in enrollments if e.batch_id == exam.batch_id]
        for enrollment in batch_enrollments:
            marks = Decimal(str(random.randint(25, 50)))
            pct = float(marks) / 50
            grade = "A" if pct >= 0.9 else "B" if pct >= 0.8 else "C" if pct >= 0.7 else "D" if pct >= 0.6 else "F"
            r = ExamResult(exam_id=exam.id, student_id=enrollment.student_id, marks_obtained=marks, grade=grade)
            result_records.append(r)
    session.add_all(result_records)
    await session.flush()
    stats["exams"] = len(exam_records)
    stats["exam_results"] = len(result_records)

    # ── Lab equipment ──────────────────────────────────────────────────
    equipment_data = [
        ("Cisco Router 2901", "Lab-1", 10, 8),
        ("Cisco Switch 2960", "Lab-1", 15, 14),
        ("Kali Linux Workstation", "Lab-2", 20, 18),
        ("GPU Server (RTX 3090)", "Lab-3", 4, 4),
        ("AWS Training Laptop", "Lab-1", 12, 10),
    ]
    equipment_records = []
    for name, lab, qty, working in equipment_data:
        eq = Equipment(name=name, lab=lab, quantity=qty, working_count=working, status=EquipmentStatus.available)
        equipment_records.append(eq)
    session.add_all(equipment_records)
    await session.flush()
    stats["equipment"] = len(equipment_records)

    await session.commit()
    return stats
