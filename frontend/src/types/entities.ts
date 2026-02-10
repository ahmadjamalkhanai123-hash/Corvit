export type UserRole = "admin" | "teacher" | "student"
export type StudentStatus = "active" | "graduated" | "dropped"
export type BatchStatus = "upcoming" | "active" | "completed"
export type EnrollmentStatus = "active" | "completed" | "dropped"
export type AttendanceStatus = "present" | "absent" | "late" | "excused"
export type FeeStatus = "pending" | "partial" | "paid" | "overdue"
export type ExamType = "quiz" | "midterm" | "final" | "practical"

export interface User {
  id: string
  username: string
  email: string
  role: UserRole
  is_active: boolean
  created_at: string
}

export interface Student {
  id: string
  name: string
  email: string
  phone: string
  cnic?: string | null
  guardian_name?: string | null
  guardian_phone?: string | null
  address?: string | null
  enrollment_date: string
  status: StudentStatus
  user_id?: string | null
  created_at: string
  updated_at: string
}

export interface Teacher {
  id: string
  name: string
  email: string
  phone: string
  specialization?: string | null
  qualification?: string | null
  joining_date: string
  is_active: boolean
  user_id?: string | null
  created_at: string
  updated_at: string
}

export interface Course {
  id: string
  name: string
  code: string
  duration_weeks: number
  fee_amount: number
  description?: string | null
  category?: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Batch {
  id: string
  course_id: string
  teacher_id: string
  name: string
  room?: string | null
  schedule_days?: string | null
  schedule_time?: string | null
  start_date: string
  end_date?: string | null
  max_capacity: number
  status: BatchStatus
  created_at: string
  updated_at: string
  course_name?: string
  teacher_name?: string
  enrolled_count?: number
}

export interface Enrollment {
  id: string
  student_id: string
  batch_id: string
  enrollment_date: string
  status: EnrollmentStatus
  created_at: string
  updated_at: string
  student_name?: string
  batch_name?: string
  course_name?: string
}

export interface Attendance {
  id: string
  student_id: string
  batch_id: string
  date: string
  status: AttendanceStatus
  marked_by?: string | null
  created_at: string
}

export interface Fee {
  id: string
  student_id: string
  course_id: string
  amount: number
  due_date: string
  paid_amount: number
  paid_date?: string | null
  status: FeeStatus
  created_at: string
  updated_at: string
  student_name?: string
  course_name?: string
}

export interface Exam {
  id: string
  batch_id: string
  title: string
  exam_type: ExamType
  date: string
  total_marks: number
  created_at: string
  updated_at: string
  batch_name?: string
}

export interface ExamResult {
  id: string
  exam_id: string
  student_id: string
  marks_obtained: number
  grade?: string | null
  remarks?: string | null
  created_at: string
  student_name?: string
}

export interface EventLog {
  id: string
  event_type: string
  actor: string
  target?: string | null
  timestamp?: string | null
}
