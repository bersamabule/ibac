"""SQLAlchemy models for IB Assessment App."""

import uuid
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Text, Integer, Date, DateTime,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship

from .database import Base


def generate_uuid():
    """Generate a new UUID string."""
    return str(uuid.uuid4())


class Student(Base):
    """Student model - represents a student in the system."""

    __tablename__ = "students"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_code = Column(String(50), nullable=False, unique=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    preferred_name = Column(String(100), nullable=True)
    class_section = Column(String(10), nullable=False, index=True)
    grade_level = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    submissions = relationship("Submission", back_populates="student", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Student {self.student_code}: {self.first_name} {self.last_name}>"


class Assignment(Base):
    """Assignment model - represents an assessment assignment."""

    __tablename__ = "assignments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(200), nullable=False)
    prompt_text = Column(Text, nullable=False)
    task_type = Column(String(50), nullable=False)  # ANALYSIS, COMPARATIVE, CREATIVE, TRANSACTIONAL, INTEGRATED
    text_type = Column(String(100), nullable=True)
    source_text_info = Column(Text, nullable=True)
    criteria_assessed = Column(Text, nullable=False)  # JSON array: ["A"], ["A","B"], etc.
    word_count_target = Column(Integer, nullable=True)
    date_assigned = Column(Date, nullable=False)
    date_due = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    submissions = relationship("Submission", back_populates="assignment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Assignment {self.title}>"


class Submission(Base):
    """Submission model - represents a student's submitted work."""

    __tablename__ = "submissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    student_id = Column(String(36), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    assignment_id = Column(String(36), ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False)
    submitted_text = Column(Text, nullable=False)
    word_count = Column(Integer, nullable=False)
    submission_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Unique constraint: one submission per student per assignment
    __table_args__ = (
        UniqueConstraint("student_id", "assignment_id", name="uq_student_assignment"),
    )

    # Relationships
    student = relationship("Student", back_populates="submissions")
    assignment = relationship("Assignment", back_populates="submissions")
    assessments = relationship("Assessment", back_populates="submission", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Submission {self.id[:8]}... by student {self.student_id[:8]}...>"


class Assessment(Base):
    """Assessment model - represents an AI or teacher assessment of a submission."""

    __tablename__ = "assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    source = Column(String(20), nullable=False)  # AI_GENERATED, AI_REANALYSIS, TEACHER_CREATED
    status = Column(String(20), nullable=False, default="DRAFT")  # DRAFT, REVIEWED, FINALIZED
    overall_summary = Column(Text, nullable=True)
    identified_strengths = Column(Text, nullable=True)
    growth_areas = Column(Text, nullable=True)
    archetype_primary = Column(String(100), nullable=True)  # Increased length for profile names
    archetype_notes = Column(Text, nullable=True)
    teacher_notes = Column(Text, nullable=True)
    knowledge_base_version = Column(String(20), nullable=False, default="2.0")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    finalized_at = Column(DateTime, nullable=True)

    # New v2 fields for forced-comparison architecture
    profile_detection = Column(Text, nullable=True)  # JSON: {detected_profile, confidence, reasoning}
    instructional_priority = Column(Text, nullable=True)  # Single most important next step

    # Relationships
    submission = relationship("Submission", back_populates="assessments")
    criterion_scores = relationship("CriterionScore", back_populates="assessment", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Assessment {self.id[:8]}... v{self.version} ({self.status})>"


class CriterionScore(Base):
    """CriterionScore model - represents scores for a specific criterion."""

    __tablename__ = "criterion_scores"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    assessment_id = Column(String(36), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    criterion = Column(String(1), nullable=False)  # A, B, C, or D
    level = Column(Integer, nullable=False)  # 1-8
    level_rationale = Column(Text, nullable=False)
    strand_scores = Column(Text, nullable=False)  # JSON object
    evidence_quotes = Column(Text, nullable=False)  # JSON array
    diagnostic_notes = Column(Text, nullable=True)
    teacher_annotation = Column(Text, nullable=True)

    # New v2 fields for forced-comparison architecture
    comparison_analysis = Column(Text, nullable=True)  # JSON: {vs_level_1_2, vs_level_3_4, vs_level_5_6, vs_level_7_8}
    closest_reference = Column(String(20), nullable=True)  # e.g., "A-05"

    # Relationships
    assessment = relationship("Assessment", back_populates="criterion_scores")

    def __repr__(self):
        return f"<CriterionScore {self.criterion}: Level {self.level}>"
