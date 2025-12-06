"""CRUD operations for IB Assessment App."""

import json
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from . import models, schemas


# ============== Student CRUD ==============

def get_students(
    db: Session,
    class_section: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.Student]:
    """Get all students, optionally filtered by class section."""
    query = db.query(models.Student)
    if class_section:
        query = query.filter(models.Student.class_section == class_section)
    return query.order_by(models.Student.last_name, models.Student.first_name).offset(skip).limit(limit).all()


def get_student(db: Session, student_id: str) -> Optional[models.Student]:
    """Get a single student by ID."""
    return db.query(models.Student).options(
        joinedload(models.Student.submissions)
    ).filter(models.Student.id == student_id).first()


def get_student_by_code(db: Session, student_code: str) -> Optional[models.Student]:
    """Get a student by their student code."""
    return db.query(models.Student).filter(models.Student.student_code == student_code).first()


def create_student(db: Session, student: schemas.StudentCreate) -> models.Student:
    """Create a new student."""
    db_student = models.Student(**student.model_dump())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


def update_student(db: Session, student_id: str, student: schemas.StudentUpdate) -> Optional[models.Student]:
    """Update an existing student."""
    db_student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not db_student:
        return None

    update_data = student.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_student, field, value)

    db_student.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_student)
    return db_student


def delete_student(db: Session, student_id: str) -> bool:
    """Delete a student."""
    db_student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not db_student:
        return False

    db.delete(db_student)
    db.commit()
    return True


# ============== Assignment CRUD ==============

def get_assignments(db: Session, skip: int = 0, limit: int = 100) -> List[models.Assignment]:
    """Get all assignments."""
    return db.query(models.Assignment).order_by(models.Assignment.date_assigned.desc()).offset(skip).limit(limit).all()


def get_assignment(db: Session, assignment_id: str) -> Optional[models.Assignment]:
    """Get a single assignment by ID."""
    return db.query(models.Assignment).options(
        joinedload(models.Assignment.submissions)
    ).filter(models.Assignment.id == assignment_id).first()


def create_assignment(db: Session, assignment: schemas.AssignmentCreate) -> models.Assignment:
    """Create a new assignment."""
    assignment_data = assignment.model_dump()
    # Convert criteria list to JSON string for storage
    assignment_data["criteria_assessed"] = json.dumps(assignment_data["criteria_assessed"])

    db_assignment = models.Assignment(**assignment_data)
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return db_assignment


def update_assignment(db: Session, assignment_id: str, assignment: schemas.AssignmentUpdate) -> Optional[models.Assignment]:
    """Update an existing assignment."""
    db_assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not db_assignment:
        return None

    update_data = assignment.model_dump(exclude_unset=True)

    # Convert criteria list to JSON string if present
    if "criteria_assessed" in update_data and update_data["criteria_assessed"] is not None:
        update_data["criteria_assessed"] = json.dumps(update_data["criteria_assessed"])

    for field, value in update_data.items():
        setattr(db_assignment, field, value)

    db.commit()
    db.refresh(db_assignment)
    return db_assignment


def delete_assignment(db: Session, assignment_id: str) -> bool:
    """Delete an assignment."""
    db_assignment = db.query(models.Assignment).filter(models.Assignment.id == assignment_id).first()
    if not db_assignment:
        return False

    db.delete(db_assignment)
    db.commit()
    return True


# ============== Submission CRUD ==============

def count_words(text: str) -> int:
    """Count words in a text string."""
    return len(text.split())


def get_submissions(
    db: Session,
    student_id: Optional[str] = None,
    assignment_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.Submission]:
    """Get all submissions, optionally filtered by student or assignment."""
    query = db.query(models.Submission).options(
        joinedload(models.Submission.student),
        joinedload(models.Submission.assignment)
    )

    if student_id:
        query = query.filter(models.Submission.student_id == student_id)
    if assignment_id:
        query = query.filter(models.Submission.assignment_id == assignment_id)

    return query.order_by(models.Submission.submission_date.desc()).offset(skip).limit(limit).all()


def get_submission(db: Session, submission_id: str) -> Optional[models.Submission]:
    """Get a single submission by ID with all related data."""
    return db.query(models.Submission).options(
        joinedload(models.Submission.student),
        joinedload(models.Submission.assignment),
        joinedload(models.Submission.assessments)
    ).filter(models.Submission.id == submission_id).first()


def get_submission_by_student_assignment(
    db: Session,
    student_id: str,
    assignment_id: str
) -> Optional[models.Submission]:
    """Check if a submission already exists for this student/assignment combination."""
    return db.query(models.Submission).filter(
        models.Submission.student_id == student_id,
        models.Submission.assignment_id == assignment_id
    ).first()


def create_submission(db: Session, submission: schemas.SubmissionCreate) -> models.Submission:
    """Create a new submission with auto-calculated word count."""
    submission_data = submission.model_dump()
    submission_data["word_count"] = count_words(submission_data["submitted_text"])

    db_submission = models.Submission(**submission_data)
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission


def delete_submission(db: Session, submission_id: str) -> bool:
    """Delete a submission."""
    db_submission = db.query(models.Submission).filter(models.Submission.id == submission_id).first()
    if not db_submission:
        return False

    db.delete(db_submission)
    db.commit()
    return True


# ============== Assessment CRUD ==============

def get_assessment(db: Session, assessment_id: str) -> Optional[models.Assessment]:
    """Get a single assessment by ID with criterion scores."""
    return db.query(models.Assessment).options(
        joinedload(models.Assessment.criterion_scores)
    ).filter(models.Assessment.id == assessment_id).first()


def create_assessment(
    db: Session,
    submission_id: str,
    source: str,
    overall_summary: str = None,
    identified_strengths: str = None,
    growth_areas: str = None,
    archetype_primary: str = None,
    archetype_notes: str = None,
    knowledge_base_version: str = "2.0",
    profile_detection: str = None,
    instructional_priority: str = None
) -> models.Assessment:
    """Create a new assessment."""
    import uuid
    assessment = models.Assessment(
        id=str(uuid.uuid4()),
        submission_id=submission_id,
        version=1,
        source=source,
        status="DRAFT",
        overall_summary=overall_summary,
        identified_strengths=identified_strengths,
        growth_areas=growth_areas,
        archetype_primary=archetype_primary,
        archetype_notes=archetype_notes,
        knowledge_base_version=knowledge_base_version,
        profile_detection=profile_detection,
        instructional_priority=instructional_priority
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def create_criterion_score(
    db: Session,
    assessment_id: str,
    criterion: str,
    level: int,
    level_rationale: str,
    strand_scores: str,
    evidence_quotes: str,
    diagnostic_notes: str = None,
    comparison_analysis: str = None,
    closest_reference: str = None
) -> models.CriterionScore:
    """Create a criterion score record."""
    import uuid
    score = models.CriterionScore(
        id=str(uuid.uuid4()),
        assessment_id=assessment_id,
        criterion=criterion,
        level=level,
        level_rationale=level_rationale,
        strand_scores=strand_scores,
        evidence_quotes=evidence_quotes,
        diagnostic_notes=diagnostic_notes,
        comparison_analysis=comparison_analysis,
        closest_reference=closest_reference
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    return score


def get_assessment_with_scores(db: Session, assessment_id: str) -> Optional[dict]:
    """Get assessment with all criterion scores and related data."""
    assessment = db.query(models.Assessment).filter(
        models.Assessment.id == assessment_id
    ).first()

    if not assessment:
        return None

    scores = db.query(models.CriterionScore).filter(
        models.CriterionScore.assessment_id == assessment_id
    ).all()

    # Get related submission, student, assignment
    submission = db.query(models.Submission).filter(
        models.Submission.id == assessment.submission_id
    ).first()

    student = db.query(models.Student).filter(
        models.Student.id == submission.student_id
    ).first() if submission else None

    assignment = db.query(models.Assignment).filter(
        models.Assignment.id == submission.assignment_id
    ).first() if submission else None

    return {
        "assessment": assessment,
        "criterion_scores": scores,
        "submission": submission,
        "student": student,
        "assignment": assignment
    }


def update_assessment_dict(db: Session, assessment_id: str, update_data: dict) -> Optional[models.Assessment]:
    """Update assessment fields using a dictionary."""
    db_assessment = db.query(models.Assessment).filter(
        models.Assessment.id == assessment_id
    ).first()

    if not db_assessment:
        return None

    for key, value in update_data.items():
        if hasattr(db_assessment, key):
            setattr(db_assessment, key, value)

    db.commit()
    db.refresh(db_assessment)
    return db_assessment


def finalize_assessment(db: Session, assessment_id: str) -> Optional[models.Assessment]:
    """Mark assessment as finalized."""
    db_assessment = db.query(models.Assessment).filter(
        models.Assessment.id == assessment_id
    ).first()

    if not db_assessment:
        return None

    db_assessment.status = "FINALIZED"
    db_assessment.finalized_at = datetime.utcnow()
    db.commit()
    db.refresh(db_assessment)
    return db_assessment


def update_criterion_score(db: Session, score_id: str, update_data: dict) -> Optional[models.CriterionScore]:
    """Update criterion score (typically teacher_annotation)."""
    score = db.query(models.CriterionScore).filter(
        models.CriterionScore.id == score_id
    ).first()

    if not score:
        return None

    for key, value in update_data.items():
        if hasattr(score, key):
            setattr(score, key, value)

    db.commit()
    db.refresh(score)
    return score


def update_assessment(db: Session, assessment_id: str, assessment: schemas.AssessmentUpdate) -> Optional[models.Assessment]:
    """Update an existing assessment."""
    db_assessment = db.query(models.Assessment).filter(models.Assessment.id == assessment_id).first()
    if not db_assessment:
        return None

    update_data = assessment.model_dump(exclude_unset=True)

    # Handle finalization
    if "status" in update_data and update_data["status"] == "FINALIZED":
        update_data["finalized_at"] = datetime.utcnow()

    for field, value in update_data.items():
        setattr(db_assessment, field, value)

    db.commit()
    db.refresh(db_assessment)
    return db_assessment


# ============== Dashboard Stats ==============

def get_dashboard_stats(db: Session) -> dict:
    """Get statistics for the dashboard."""
    total_students = db.query(func.count(models.Student.id)).scalar()
    total_assignments = db.query(func.count(models.Assignment.id)).scalar()
    total_submissions = db.query(func.count(models.Submission.id)).scalar()

    recent_submissions = db.query(models.Submission).options(
        joinedload(models.Submission.student),
        joinedload(models.Submission.assignment)
    ).order_by(models.Submission.submission_date.desc()).limit(5).all()

    return {
        "total_students": total_students or 0,
        "total_assignments": total_assignments or 0,
        "total_submissions": total_submissions or 0,
        "recent_submissions": recent_submissions
    }


# ============== Sample Data Seeding ==============

def seed_sample_data(db: Session) -> dict:
    """Seed the database with sample data for testing."""
    # Check if data already exists
    if db.query(models.Student).first():
        return {"message": "Database already contains data. Skipping seed."}

    # Create sample students
    students_data = [
        {"student_code": "STU001", "first_name": "Emma", "last_name": "Wilson", "class_section": "7A", "grade_level": 7},
        {"student_code": "STU002", "first_name": "Liam", "last_name": "Chen", "preferred_name": "Leo", "class_section": "7A", "grade_level": 7},
        {"student_code": "STU003", "first_name": "Sophia", "last_name": "Patel", "class_section": "7B", "grade_level": 7},
        {"student_code": "STU004", "first_name": "Noah", "last_name": "Garcia", "class_section": "8A", "grade_level": 8},
        {"student_code": "STU005", "first_name": "Olivia", "last_name": "Kim", "class_section": "8B", "grade_level": 8},
    ]

    created_students = []
    for data in students_data:
        student = models.Student(**data)
        db.add(student)
        created_students.append(student)

    db.commit()

    # Create sample assignments
    from datetime import date
    assignments_data = [
        {
            "title": "Poetry Analysis: 'The Road Not Taken'",
            "prompt_text": "Analyze Robert Frost's poem 'The Road Not Taken'. Consider the use of imagery, symbolism, and how the structure contributes to the poem's meaning.",
            "task_type": "ANALYSIS",
            "text_type": "Literary Analysis Essay",
            "source_text_info": "Robert Frost, 'The Road Not Taken' (1916)",
            "criteria_assessed": json.dumps(["A", "B"]),
            "word_count_target": 500,
            "date_assigned": date(2025, 11, 1),
            "date_due": date(2025, 11, 15)
        },
        {
            "title": "Comparative Essay: Two Short Stories",
            "prompt_text": "Compare and contrast the themes of identity in 'The Metamorphosis' by Franz Kafka and 'The Yellow Wallpaper' by Charlotte Perkins Gilman.",
            "task_type": "COMPARATIVE",
            "text_type": "Comparative Essay",
            "source_text_info": "Kafka's 'The Metamorphosis' and Gilman's 'The Yellow Wallpaper'",
            "criteria_assessed": json.dumps(["A", "B", "C"]),
            "word_count_target": 800,
            "date_assigned": date(2025, 11, 15),
            "date_due": date(2025, 12, 1)
        },
        {
            "title": "Creative Writing: Alternative Ending",
            "prompt_text": "Write an alternative ending for 'The Lottery' by Shirley Jackson. Maintain the author's style and tone while creating a different outcome.",
            "task_type": "CREATIVE",
            "text_type": "Creative Narrative",
            "source_text_info": "Shirley Jackson, 'The Lottery' (1948)",
            "criteria_assessed": json.dumps(["C", "D"]),
            "word_count_target": 600,
            "date_assigned": date(2025, 12, 1),
            "date_due": date(2025, 12, 15)
        }
    ]

    created_assignments = []
    for data in assignments_data:
        assignment = models.Assignment(**data)
        db.add(assignment)
        created_assignments.append(assignment)

    db.commit()

    # Refresh to get IDs
    for student in created_students:
        db.refresh(student)
    for assignment in created_assignments:
        db.refresh(assignment)

    # Create sample submission
    sample_text = """The Road Not Taken by Robert Frost presents a speaker at a crossroads, both literal and metaphorical. The imagery of "two roads diverged in a yellow wood" immediately establishes autumn as the setting, suggesting a time of change and transition.

The poem's central symbol is the fork in the road, representing life's choices. Frost uses visual imagery to describe the paths: one "bent in the undergrowth" while the other appears "just as fair." This similarity is crucial—the speaker admits the paths are "really about the same," challenging the notion that our choices are always clearly differentiated.

The structure reinforces the theme of choice. Four stanzas of five lines each create a measured, contemplative pace. The rhyme scheme (ABAAB) provides stability while the enjambment creates forward momentum, mirroring the journey itself.

Most significantly, Frost employs irony in the final stanza. The speaker imagines telling this story "ages and ages hence" with a "sigh," claiming the choice "made all the difference." Yet we know from the poem that the roads were essentially equal. This suggests that the meaning we attribute to our choices may be constructed retrospectively.

In conclusion, Frost masterfully uses imagery, symbolism, and structure to explore how we narrativize our life choices, finding significance in decisions that may have been arbitrary."""

    submission = models.Submission(
        student_id=created_students[0].id,
        assignment_id=created_assignments[0].id,
        submitted_text=sample_text,
        word_count=count_words(sample_text)
    )
    db.add(submission)
    db.commit()

    return {
        "message": "Sample data created successfully",
        "students_created": len(created_students),
        "assignments_created": len(created_assignments),
        "submissions_created": 1
    }
