"""Pydantic schemas for API request/response validation."""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
import json


# ============== Student Schemas ==============

class StudentBase(BaseModel):
    """Base schema for student data."""
    student_code: str = Field(..., min_length=1, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    preferred_name: Optional[str] = Field(None, max_length=100)
    class_section: str = Field(..., min_length=1, max_length=10)
    grade_level: int = Field(..., ge=7, le=8)
    notes: Optional[str] = None


class StudentCreate(StudentBase):
    """Schema for creating a new student."""
    pass


class StudentUpdate(BaseModel):
    """Schema for updating a student (all fields optional)."""
    student_code: Optional[str] = Field(None, min_length=1, max_length=50)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    preferred_name: Optional[str] = Field(None, max_length=100)
    class_section: Optional[str] = Field(None, min_length=1, max_length=10)
    grade_level: Optional[int] = Field(None, ge=7, le=8)
    notes: Optional[str] = None


class StudentResponse(StudentBase):
    """Schema for student response."""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StudentWithSubmissions(StudentResponse):
    """Schema for student with their submissions."""
    submissions: List["SubmissionResponse"] = []


# ============== Assignment Schemas ==============

class AssignmentBase(BaseModel):
    """Base schema for assignment data."""
    title: str = Field(..., min_length=1, max_length=200)
    prompt_text: str = Field(..., min_length=1)
    task_type: str = Field(..., pattern="^(ANALYSIS|COMPARATIVE|CREATIVE|TRANSACTIONAL|INTEGRATED)$")
    text_type: Optional[str] = Field(None, max_length=100)
    source_text_info: Optional[str] = None
    criteria_assessed: List[str] = Field(..., min_length=1)
    word_count_target: Optional[int] = Field(None, ge=1)
    date_assigned: date
    date_due: Optional[date] = None

    @field_validator("criteria_assessed")
    @classmethod
    def validate_criteria(cls, v):
        """Validate criteria are A, B, C, or D."""
        valid_criteria = {"A", "B", "C", "D"}
        for criterion in v:
            if criterion not in valid_criteria:
                raise ValueError(f"Invalid criterion: {criterion}. Must be A, B, C, or D.")
        return v


class AssignmentCreate(AssignmentBase):
    """Schema for creating a new assignment."""
    pass


class AssignmentUpdate(BaseModel):
    """Schema for updating an assignment (all fields optional)."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    prompt_text: Optional[str] = Field(None, min_length=1)
    task_type: Optional[str] = Field(None, pattern="^(ANALYSIS|COMPARATIVE|CREATIVE|TRANSACTIONAL|INTEGRATED)$")
    text_type: Optional[str] = Field(None, max_length=100)
    source_text_info: Optional[str] = None
    criteria_assessed: Optional[List[str]] = None
    word_count_target: Optional[int] = Field(None, ge=1)
    date_assigned: Optional[date] = None
    date_due: Optional[date] = None

    @field_validator("criteria_assessed")
    @classmethod
    def validate_criteria(cls, v):
        """Validate criteria are A, B, C, or D."""
        if v is None:
            return v
        valid_criteria = {"A", "B", "C", "D"}
        for criterion in v:
            if criterion not in valid_criteria:
                raise ValueError(f"Invalid criterion: {criterion}. Must be A, B, C, or D.")
        return v


class AssignmentResponse(BaseModel):
    """Schema for assignment response."""
    id: str
    title: str
    prompt_text: str
    task_type: str
    text_type: Optional[str]
    source_text_info: Optional[str]
    criteria_assessed: List[str]
    word_count_target: Optional[int]
    date_assigned: date
    date_due: Optional[date]
    created_at: datetime

    class Config:
        from_attributes = True

    @field_validator("criteria_assessed", mode="before")
    @classmethod
    def parse_criteria(cls, v):
        """Parse JSON string to list if needed."""
        if isinstance(v, str):
            return json.loads(v)
        return v


class AssignmentWithSubmissions(AssignmentResponse):
    """Schema for assignment with its submissions."""
    submissions: List["SubmissionResponse"] = []


# ============== Submission Schemas ==============

class SubmissionBase(BaseModel):
    """Base schema for submission data."""
    student_id: str
    assignment_id: str
    submitted_text: str = Field(..., min_length=1)


class SubmissionCreate(SubmissionBase):
    """Schema for creating a new submission."""
    pass


class SubmissionResponse(BaseModel):
    """Schema for submission response."""
    id: str
    student_id: str
    assignment_id: str
    submitted_text: str
    word_count: int
    submission_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class SubmissionWithDetails(SubmissionResponse):
    """Schema for submission with student and assignment details."""
    student: Optional[StudentResponse] = None
    assignment: Optional[AssignmentResponse] = None
    assessments: List["AssessmentResponse"] = []


# ============== Assessment Schemas ==============

class CriterionScoreBase(BaseModel):
    """Base schema for criterion score data."""
    criterion: str = Field(..., pattern="^[ABCD]$")
    level: int = Field(..., ge=1, le=8)
    level_rationale: str
    strand_scores: dict
    evidence_quotes: List[dict]  # Changed to list of dicts with quote and analysis
    diagnostic_notes: Optional[str] = None
    teacher_annotation: Optional[str] = None
    # New v2 fields
    comparison_analysis: Optional[dict] = None  # {vs_level_1_2, vs_level_3_4, ...}
    closest_reference: Optional[str] = None  # e.g., "A-05"


class CriterionScoreResponse(CriterionScoreBase):
    """Schema for criterion score response."""
    id: str
    assessment_id: str

    class Config:
        from_attributes = True

    @field_validator("strand_scores", mode="before")
    @classmethod
    def parse_strand_scores(cls, v):
        """Parse JSON string to dict if needed."""
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("evidence_quotes", mode="before")
    @classmethod
    def parse_evidence_quotes(cls, v):
        """Parse JSON string to list if needed."""
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("comparison_analysis", mode="before")
    @classmethod
    def parse_comparison_analysis(cls, v):
        """Parse JSON string to dict if needed."""
        if isinstance(v, str):
            return json.loads(v)
        if v is None:
            return None
        return v


class AssessmentBase(BaseModel):
    """Base schema for assessment data."""
    submission_id: str
    version: int = 1
    source: str = Field(..., pattern="^(AI_GENERATED|AI_REANALYSIS|TEACHER_CREATED)$")
    status: str = Field(default="DRAFT", pattern="^(DRAFT|REVIEWED|FINALIZED)$")
    overall_summary: Optional[str] = None
    identified_strengths: Optional[str] = None
    growth_areas: Optional[str] = None
    archetype_primary: Optional[str] = None
    archetype_notes: Optional[str] = None
    teacher_notes: Optional[str] = None
    knowledge_base_version: str = "2.0"
    # New v2 fields
    profile_detection: Optional[dict] = None  # {detected_profile, confidence, reasoning}
    instructional_priority: Optional[str] = None


class AssessmentUpdate(BaseModel):
    """Schema for updating an assessment."""
    status: Optional[str] = Field(None, pattern="^(DRAFT|REVIEWED|FINALIZED)$")
    teacher_notes: Optional[str] = None
    overall_summary: Optional[str] = None
    identified_strengths: Optional[str] = None
    growth_areas: Optional[str] = None


class AssessmentResponse(BaseModel):
    """Schema for assessment response."""
    id: str
    submission_id: str
    version: int
    source: str
    status: str
    overall_summary: Optional[str]
    identified_strengths: Optional[str]
    growth_areas: Optional[str]
    archetype_primary: Optional[str]
    archetype_notes: Optional[str]
    teacher_notes: Optional[str]
    knowledge_base_version: str
    created_at: datetime
    finalized_at: Optional[datetime]
    # New v2 fields
    profile_detection: Optional[dict] = None
    instructional_priority: Optional[str] = None

    class Config:
        from_attributes = True

    @field_validator("profile_detection", mode="before")
    @classmethod
    def parse_profile_detection(cls, v):
        """Parse JSON string to dict if needed."""
        if isinstance(v, str):
            return json.loads(v)
        if v is None:
            return None
        return v


class AssessmentWithScores(AssessmentResponse):
    """Schema for assessment with criterion scores."""
    criterion_scores: List[CriterionScoreResponse] = []


# ============== Stats Schema ==============

class DashboardStats(BaseModel):
    """Schema for dashboard statistics."""
    total_students: int
    total_assignments: int
    total_submissions: int
    recent_submissions: List[SubmissionWithDetails]


# Update forward references
StudentWithSubmissions.model_rebuild()
AssignmentWithSubmissions.model_rebuild()
SubmissionWithDetails.model_rebuild()
