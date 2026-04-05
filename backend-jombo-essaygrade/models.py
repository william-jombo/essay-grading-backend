# from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum, ForeignKey, TIMESTAMP
# from sqlalchemy.orm import relationship
# from sqlalchemy.sql import func
# from database import Base


# class User(Base):
#     __tablename__ = "users"

#     id                  = Column(Integer, primary_key=True, index=True)
#     name                = Column(String(100), nullable=False)
#     email               = Column(String(150), unique=True, nullable=False)
#     password            = Column(String(255), nullable=False)
#     role                = Column(Enum("teacher", "student"), nullable=False)
#     registration_number = Column(String(50), nullable=True)
#     phone               = Column(String(20), nullable=True)
#     is_active           = Column(Boolean, default=True)
#     created_at          = Column(TIMESTAMP, server_default=func.now())
#     updated_at          = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

#     assignments = relationship("Assignment", back_populates="teacher")
#     submissions = relationship("Submission", back_populates="student")
#     sessions    = relationship("UserSession", back_populates="user")


# class UserSession(Base):
#     __tablename__ = "user_sessions"

#     id            = Column(Integer, primary_key=True, index=True)
#     user_id       = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
#     session_token = Column(String(255), unique=True, nullable=False)
#     csrf_token    = Column(String(255), nullable=False)
#     ip_address    = Column(String(45), nullable=False)
#     expires_at    = Column(TIMESTAMP, nullable=False)
#     created_at    = Column(TIMESTAMP, server_default=func.now())

#     user = relationship("User", back_populates="sessions")


# class Assignment(Base):
#     __tablename__ = "assignments"

#     id                 = Column(Integer, primary_key=True, index=True)
#     teacher_id         = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
#     title              = Column(String(255), nullable=False)
#     description        = Column(Text, nullable=True)
#     instructions       = Column(Text, nullable=False)
#     reference_material = Column(Text, nullable=True)
#     max_score          = Column(Integer, default=100)
#     due_date           = Column(DateTime, nullable=False)
#     rubric             = Column(Text, nullable=True)  # JSON string
#     is_active          = Column(Boolean, default=True)
#     created_at         = Column(TIMESTAMP, server_default=func.now())
#     updated_at         = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

#     teacher     = relationship("User", back_populates="assignments")
#     submissions = relationship("Submission", back_populates="assignment")
#     attachments = relationship("AssignmentAttachment", back_populates="assignment")


# class AssignmentAttachment(Base):
#     __tablename__ = "assignment_attachments"

#     id            = Column(Integer, primary_key=True, index=True)
#     assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
#     file_name     = Column(String(255), nullable=False)
#     file_path     = Column(String(500), nullable=False)
#     file_type     = Column(String(100), nullable=True)
#     file_size     = Column(Integer, nullable=True)
#     uploaded_at   = Column(TIMESTAMP, server_default=func.now())

#     assignment = relationship("Assignment", back_populates="attachments")


# class Submission(Base):
#     __tablename__ = "submissions"

#     id                 = Column(Integer, primary_key=True, index=True)
#     assignment_id      = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
#     student_id         = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
#     essay_text         = Column(Text, nullable=False)
#     submit_mode        = Column(Enum("write", "upload"), default="write")
#     file_name          = Column(String(255), nullable=True)
#     file_path          = Column(String(500), nullable=True)
#     ai_score           = Column(Integer, nullable=True)
#     ai_feedback        = Column(Text, nullable=True)
#     ai_detection_score = Column(Integer, nullable=True)
#     ai_graded_at       = Column(TIMESTAMP, nullable=True)
#     final_score        = Column(Integer, nullable=True)
#     teacher_feedback   = Column(Text, nullable=True)
#     graded_at          = Column(TIMESTAMP, nullable=True)
#     status             = Column(Enum("pending", "submitted", "ai_graded", "graded"), default="pending")
#     submitted_at       = Column(TIMESTAMP, server_default=func.now())
#     updated_at         = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

#     assignment   = relationship("Assignment", back_populates="submissions")
#     student      = relationship("User", back_populates="submissions")
#     ai_detection = relationship("AIDetectionLog", back_populates="submission", uselist=False)


# class AIDetectionLog(Base):
#     __tablename__ = "ai_detection_logs"

#     id              = Column(Integer, primary_key=True, index=True)
#     submission_id   = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
#     detection_score = Column(Integer, nullable=False)
#     flagged         = Column(Boolean, default=False)
#     indicators      = Column(Text, nullable=True)  # JSON array
#     model_version   = Column(String(50), nullable=True)
#     detected_at     = Column(TIMESTAMP, server_default=func.now())

#     submission = relationship("Submission", back_populates="ai_detection")


from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum, ForeignKey, TIMESTAMP, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id                  = Column(Integer, primary_key=True, index=True)
    name                = Column(String(100), nullable=False)
    email               = Column(String(150), unique=True, nullable=False)
    password            = Column(String(255), nullable=False)
    role                = Column(Enum("teacher", "student"), nullable=False)
    registration_number = Column(String(50), nullable=True)
    phone               = Column(String(20), nullable=True)
    is_active           = Column(Boolean, default=True)
    created_at          = Column(TIMESTAMP, server_default=func.now())
    updated_at          = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Teacher side — classes this teacher is assigned to (via junction table)
    teacher_classes = relationship("TeacherClass", back_populates="teacher", cascade="all, delete-orphan")

    # Student side — classes this student is enrolled in (via junction table)
    enrollments = relationship("ClassEnrollment", back_populates="student", cascade="all, delete-orphan")

    assignments = relationship("Assignment", back_populates="teacher")
    submissions = relationship("Submission", back_populates="student")
    sessions    = relationship("UserSession", back_populates="user")


class UserSession(Base):
    __tablename__ = "user_sessions"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False)
    csrf_token    = Column(String(255), nullable=False)
    ip_address    = Column(String(45), nullable=False)
    expires_at    = Column(TIMESTAMP, nullable=False)
    created_at    = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="sessions")


class Class(Base):
    __tablename__ = "classes"

    id          = Column(Integer, primary_key=True, index=True)
    # NOTE: teacher_id removed — teachers are linked via TeacherClass junction table
    name        = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    subject     = Column(String(100), nullable=True)
    section     = Column(String(50), nullable=True)
    is_active   = Column(Boolean, default=True, nullable=False)
    created_at  = Column(TIMESTAMP, server_default=func.now())
    updated_at  = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Teachers assigned to this class (via junction table)
    teacher_classes = relationship("TeacherClass", back_populates="cls", cascade="all, delete-orphan")

    # Assignments and enrolled students
    assignments = relationship("Assignment",     back_populates="cls", cascade="all, delete-orphan")
    enrollments = relationship("ClassEnrollment", back_populates="cls", cascade="all, delete-orphan")


class TeacherClass(Base):
    """Junction table — assigns teachers to classes (many-to-many)."""
    __tablename__ = "teacher_classes"

    __table_args__ = (
        UniqueConstraint("teacher_id", "class_id", name="uq_teacher_class"),
    )

    id          = Column(Integer, primary_key=True, index=True)
    teacher_id  = Column(Integer, ForeignKey("users.id",    ondelete="CASCADE"), nullable=False)
    class_id    = Column(Integer, ForeignKey("classes.id",  ondelete="CASCADE"), nullable=False)
    assigned_at = Column(TIMESTAMP, server_default=func.now())

    teacher = relationship("User",  back_populates="teacher_classes")
    cls     = relationship("Class", back_populates="teacher_classes")


class ClassEnrollment(Base):
    """Junction table — links students to classes (many-to-many)."""
    __tablename__ = "class_enrollments"

    __table_args__ = (
        UniqueConstraint("class_id", "student_id", name="uq_enrollment"),
    )

    id          = Column(Integer, primary_key=True, index=True)
    class_id    = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    student_id  = Column(Integer, ForeignKey("users.id",   ondelete="CASCADE"), nullable=False)
    enrolled_at = Column(TIMESTAMP, server_default=func.now())

    cls     = relationship("Class", back_populates="enrollments")
    student = relationship("User",  back_populates="enrollments")


class Assignment(Base):
    __tablename__ = "assignments"

    id                 = Column(Integer, primary_key=True, index=True)
    teacher_id         = Column(Integer, ForeignKey("users.id",   ondelete="CASCADE"),  nullable=False)
    class_id           = Column(Integer, ForeignKey("classes.id", ondelete="SET NULL"), nullable=True)
    title              = Column(String(255), nullable=False)
    description        = Column(Text, nullable=True)
    instructions       = Column(Text, nullable=False)
    reference_material = Column(Text, nullable=True)
    max_score          = Column(Integer, default=100)
    due_date           = Column(DateTime, nullable=False)
    rubric             = Column(Text, nullable=True)  # JSON string
    is_active          = Column(Boolean, default=True)
    created_at         = Column(TIMESTAMP, server_default=func.now())
    updated_at         = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    teacher     = relationship("User",                 back_populates="assignments")
    cls         = relationship("Class",                back_populates="assignments")
    submissions = relationship("Submission",           back_populates="assignment")
    attachments = relationship("AssignmentAttachment", back_populates="assignment")


class AssignmentAttachment(Base):
    __tablename__ = "assignment_attachments"

    id            = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    file_name     = Column(String(255), nullable=False)
    file_path     = Column(String(500), nullable=False)
    file_type     = Column(String(100), nullable=True)
    file_size     = Column(Integer, nullable=True)
    uploaded_at   = Column(TIMESTAMP, server_default=func.now())

    assignment = relationship("Assignment", back_populates="attachments")


class Submission(Base):
    __tablename__ = "submissions"

    id                 = Column(Integer, primary_key=True, index=True)
    assignment_id      = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    student_id         = Column(Integer, ForeignKey("users.id",       ondelete="CASCADE"), nullable=False)
    essay_text         = Column(Text, nullable=False)
    submit_mode        = Column(Enum("write", "upload"), default="write")
    file_name          = Column(String(255), nullable=True)
    file_path          = Column(String(500), nullable=True)
    ai_score           = Column(Integer, nullable=True)
    ai_feedback        = Column(Text, nullable=True)
    ai_detection_score = Column(Integer, nullable=True)
    ai_graded_at       = Column(TIMESTAMP, nullable=True)
    final_score        = Column(Integer, nullable=True)
    teacher_feedback   = Column(Text, nullable=True)
    graded_at          = Column(TIMESTAMP, nullable=True)
    status             = Column(Enum("pending", "submitted", "ai_graded", "graded"), default="pending")
    submitted_at       = Column(TIMESTAMP, server_default=func.now())
    updated_at         = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    assignment   = relationship("Assignment",    back_populates="submissions")
    student      = relationship("User",          back_populates="submissions")
    ai_detection = relationship("AIDetectionLog", back_populates="submission", uselist=False)


class AIDetectionLog(Base):
    __tablename__ = "ai_detection_logs"

    id              = Column(Integer, primary_key=True, index=True)
    submission_id   = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    detection_score = Column(Integer, nullable=False)
    flagged         = Column(Boolean, default=False)
    indicators      = Column(Text, nullable=True)   # JSON array
    model_version   = Column(String(50), nullable=True)
    detected_at     = Column(TIMESTAMP, server_default=func.now())

    submission = relationship("Submission", back_populates="ai_detection")