"""FastAPI main application for IB Assessment App."""

import os
import io
import csv
import json
from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, Query, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .database import get_db, init_db
from . import crud, schemas
from .assessment_engine import generate_assessment


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    print("Starting IB Assessment App...")
    init_db()
    yield
    print("Shutting down IB Assessment App...")


# Create FastAPI app
app = FastAPI(
    title="IB Assessment Companion",
    description="Local application for tracking IB MYP Language and Literature student assessments",
    version="1.0.0",
    lifespan=lifespan
)

# Get frontend directory path
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

# Mount static files (CSS and JS)
app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")


# ============== HTML Page Routes ==============

@app.get("/", response_class=FileResponse)
async def serve_index():
    """Serve the dashboard/home page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/students.html", response_class=FileResponse)
async def serve_students():
    """Serve the students page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "students.html"))


@app.get("/assignments.html", response_class=FileResponse)
async def serve_assignments():
    """Serve the assignments page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "assignments.html"))


@app.get("/submissions.html", response_class=FileResponse)
async def serve_submissions():
    """Serve the submissions page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "submissions.html"))


@app.get("/assessment.html", response_class=FileResponse)
async def serve_assessment():
    """Serve the assessment view page."""
    return FileResponse(os.path.join(FRONTEND_DIR, "assessment.html"))


# ============== Dashboard API ==============

@app.get("/api/dashboard", response_model=schemas.DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics."""
    return crud.get_dashboard_stats(db)


# ============== Student API ==============

@app.get("/api/students", response_model=List[schemas.StudentResponse])
def list_students(
    class_section: Optional[str] = Query(None, description="Filter by class section"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """List all students, optionally filtered by class section."""
    return crud.get_students(db, class_section=class_section, skip=skip, limit=limit)


@app.get("/api/students/{student_id}", response_model=schemas.StudentWithSubmissions)
def get_student(student_id: str, db: Session = Depends(get_db)):
    """Get a single student with their submissions."""
    student = crud.get_student(db, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student


@app.post("/api/students", response_model=schemas.StudentResponse, status_code=201)
def create_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    """Create a new student."""
    # Check for duplicate student code
    existing = crud.get_student_by_code(db, student.student_code)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Student with code '{student.student_code}' already exists"
        )
    return crud.create_student(db, student)


@app.put("/api/students/{student_id}", response_model=schemas.StudentResponse)
def update_student(
    student_id: str,
    student: schemas.StudentUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing student."""
    # Check if student code is being changed to an existing one
    if student.student_code:
        existing = crud.get_student_by_code(db, student.student_code)
        if existing and existing.id != student_id:
            raise HTTPException(
                status_code=400,
                detail=f"Student with code '{student.student_code}' already exists"
            )

    updated = crud.update_student(db, student_id, student)
    if not updated:
        raise HTTPException(status_code=404, detail="Student not found")
    return updated


@app.delete("/api/students/{student_id}")
def delete_student(student_id: str, db: Session = Depends(get_db)):
    """Delete a student."""
    if not crud.delete_student(db, student_id):
        raise HTTPException(status_code=404, detail="Student not found")
    return {"message": "Student deleted successfully"}


@app.post("/api/students/import")
async def import_students_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Import students from a CSV file.
    Expected columns: student_code, first_name, last_name, class_section, grade_level
    Skips duplicates based on student_code.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    content = await file.read()
    try:
        text = content.decode('utf-8')
    except UnicodeDecodeError:
        text = content.decode('latin-1')

    reader = csv.DictReader(io.StringIO(text))

    # Validate required columns
    required_columns = {'student_code', 'first_name', 'last_name', 'class_section', 'grade_level'}
    if reader.fieldnames is None:
        raise HTTPException(status_code=400, detail="CSV file is empty or invalid")

    # Normalize column names (strip whitespace and lowercase)
    column_map = {col.strip().lower().replace(' ', '_'): col for col in reader.fieldnames}
    missing = required_columns - set(column_map.keys())
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required columns: {', '.join(missing)}"
        )

    imported = 0
    skipped = 0
    errors = []

    for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header row
        try:
            # Get values using the column map
            student_code = row[column_map['student_code']].strip()
            first_name = row[column_map['first_name']].strip()
            last_name = row[column_map['last_name']].strip()
            class_section = row[column_map['class_section']].strip()
            grade_level_str = row[column_map['grade_level']].strip()

            # Validate required fields
            if not all([student_code, first_name, last_name, class_section, grade_level_str]):
                errors.append(f"Row {row_num}: Missing required field(s)")
                continue

            # Parse grade level
            try:
                grade_level = int(grade_level_str)
            except ValueError:
                errors.append(f"Row {row_num}: Invalid grade_level '{grade_level_str}'")
                continue

            # Check for duplicate
            existing = crud.get_student_by_code(db, student_code)
            if existing:
                skipped += 1
                continue

            # Create student
            student_data = schemas.StudentCreate(
                student_code=student_code,
                first_name=first_name,
                last_name=last_name,
                class_section=class_section,
                grade_level=grade_level
            )
            crud.create_student(db, student_data)
            imported += 1

        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")

    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors[:10] if errors else [],  # Return first 10 errors
        "total_errors": len(errors)
    }


# ============== Assignment API ==============

@app.get("/api/assignments", response_model=List[schemas.AssignmentResponse])
def list_assignments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """List all assignments."""
    return crud.get_assignments(db, skip=skip, limit=limit)


@app.get("/api/assignments/{assignment_id}", response_model=schemas.AssignmentWithSubmissions)
def get_assignment(assignment_id: str, db: Session = Depends(get_db)):
    """Get a single assignment with its submissions."""
    assignment = crud.get_assignment(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@app.post("/api/assignments", response_model=schemas.AssignmentResponse, status_code=201)
def create_assignment(assignment: schemas.AssignmentCreate, db: Session = Depends(get_db)):
    """Create a new assignment."""
    return crud.create_assignment(db, assignment)


@app.put("/api/assignments/{assignment_id}", response_model=schemas.AssignmentResponse)
def update_assignment(
    assignment_id: str,
    assignment: schemas.AssignmentUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing assignment."""
    updated = crud.update_assignment(db, assignment_id, assignment)
    if not updated:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return updated


@app.delete("/api/assignments/{assignment_id}")
def delete_assignment(assignment_id: str, db: Session = Depends(get_db)):
    """Delete an assignment."""
    if not crud.delete_assignment(db, assignment_id):
        raise HTTPException(status_code=404, detail="Assignment not found")
    return {"message": "Assignment deleted successfully"}


# ============== Submission API ==============

@app.get("/api/submissions", response_model=List[schemas.SubmissionWithDetails])
def list_submissions(
    student_id: Optional[str] = Query(None, description="Filter by student ID"),
    assignment_id: Optional[str] = Query(None, description="Filter by assignment ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """List submissions, optionally filtered by student or assignment."""
    return crud.get_submissions(
        db,
        student_id=student_id,
        assignment_id=assignment_id,
        skip=skip,
        limit=limit
    )


@app.get("/api/submissions/{submission_id}", response_model=schemas.SubmissionWithDetails)
def get_submission(submission_id: str, db: Session = Depends(get_db)):
    """Get a single submission with all details."""
    submission = crud.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission


@app.post("/api/submissions", response_model=schemas.SubmissionResponse, status_code=201)
def create_submission(submission: schemas.SubmissionCreate, db: Session = Depends(get_db)):
    """Create a new submission."""
    # Check if student exists
    student = crud.get_student(db, submission.student_id)
    if not student:
        raise HTTPException(status_code=400, detail="Student not found")

    # Check if assignment exists
    assignment = crud.get_assignment(db, submission.assignment_id)
    if not assignment:
        raise HTTPException(status_code=400, detail="Assignment not found")

    # Check for duplicate submission
    existing = crud.get_submission_by_student_assignment(
        db, submission.student_id, submission.assignment_id
    )
    if existing:
        raise HTTPException(
            status_code=400,
            detail="A submission already exists for this student and assignment"
        )

    return crud.create_submission(db, submission)


@app.delete("/api/submissions/{submission_id}")
def delete_submission(submission_id: str, db: Session = Depends(get_db)):
    """Delete a submission."""
    if not crud.delete_submission(db, submission_id):
        raise HTTPException(status_code=404, detail="Submission not found")
    return {"message": "Submission deleted successfully"}


# ============== Assessment API ==============

@app.post("/api/submissions/{submission_id}/assess")
async def create_assessment_for_submission(submission_id: str, db: Session = Depends(get_db)):
    """
    Generate an AI assessment for a submission.
    """
    # Get the submission with related data
    submission = crud.get_submission(db, submission_id)
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Get student and assignment
    student = crud.get_student(db, submission.student_id)
    assignment = crud.get_assignment(db, submission.assignment_id)

    # Parse criteria from assignment
    criteria = json.loads(assignment.criteria_assessed) if isinstance(assignment.criteria_assessed, str) else assignment.criteria_assessed

    # Generate assessment
    try:
        assessment_data = generate_assessment(
            assignment_title=assignment.title,
            task_type=assignment.task_type,
            prompt_text=assignment.prompt_text,
            criteria_assessed=criteria,
            student_name=f"{student.first_name} {student.last_name}",
            grade_level=student.grade_level,
            submitted_text=submission.submitted_text,
            word_count=submission.word_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assessment generation failed: {str(e)}")

    # Serialize profile_detection to JSON string if present
    profile_detection_json = None
    if assessment_data.get("profile_detection"):
        profile_detection_json = json.dumps(assessment_data.get("profile_detection"))

    # Create assessment record
    assessment = crud.create_assessment(
        db,
        submission_id=submission_id,
        source="AI_GENERATED",
        overall_summary=assessment_data.get("overall_summary"),
        identified_strengths=assessment_data.get("identified_strengths"),
        growth_areas=assessment_data.get("growth_areas"),
        archetype_primary=assessment_data.get("archetype_primary"),
        archetype_notes=assessment_data.get("archetype_notes"),
        knowledge_base_version=assessment_data.get("knowledge_base_version", "2.0"),
        profile_detection=profile_detection_json,
        instructional_priority=assessment_data.get("instructional_priority")
    )

    # Create criterion score records
    for score_data in assessment_data.get("criterion_scores", []):
        # Serialize comparison_analysis to JSON string if present
        comparison_analysis_json = None
        if score_data.get("comparison_analysis"):
            comparison_analysis_json = json.dumps(score_data.get("comparison_analysis"))

        crud.create_criterion_score(
            db,
            assessment_id=assessment.id,
            criterion=score_data.get("criterion"),
            level=score_data.get("level"),
            level_rationale=score_data.get("level_rationale"),
            strand_scores=json.dumps(score_data.get("strand_scores", {})),
            evidence_quotes=json.dumps(score_data.get("evidence_quotes", [])),
            diagnostic_notes=score_data.get("diagnostic_notes"),
            comparison_analysis=comparison_analysis_json,
            closest_reference=score_data.get("closest_reference")
        )

    return {"assessment_id": assessment.id, "status": "created"}


@app.get("/api/assessments/{assessment_id}")
def get_assessment_full(assessment_id: str, db: Session = Depends(get_db)):
    """
    Get a full assessment with all criterion scores and related data.
    """
    result = crud.get_assessment_with_scores(db, assessment_id)
    if not result:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Format the response
    assessment = result["assessment"]
    scores = result["criterion_scores"]
    submission = result["submission"]
    student = result["student"]
    assignment = result["assignment"]

    # Parse criteria from assignment
    criteria_assessed = []
    if assignment:
        criteria_assessed = json.loads(assignment.criteria_assessed) if isinstance(assignment.criteria_assessed, str) else assignment.criteria_assessed

    # Format criterion scores
    formatted_scores = []
    for score in scores:
        formatted_score = {
            "id": score.id,
            "criterion": score.criterion,
            "level": score.level,
            "level_rationale": score.level_rationale,
            "strand_scores": json.loads(score.strand_scores) if isinstance(score.strand_scores, str) else score.strand_scores,
            "evidence_quotes": json.loads(score.evidence_quotes) if isinstance(score.evidence_quotes, str) else score.evidence_quotes,
            "diagnostic_notes": score.diagnostic_notes,
            "teacher_annotation": score.teacher_annotation,
            # New v2 fields
            "comparison_analysis": json.loads(score.comparison_analysis) if score.comparison_analysis and isinstance(score.comparison_analysis, str) else score.comparison_analysis,
            "closest_reference": score.closest_reference
        }
        formatted_scores.append(formatted_score)

    # Parse profile_detection from JSON string
    profile_detection = None
    if assessment.profile_detection:
        profile_detection = json.loads(assessment.profile_detection) if isinstance(assessment.profile_detection, str) else assessment.profile_detection

    return {
        "id": assessment.id,
        "submission_id": assessment.submission_id,
        "version": assessment.version,
        "source": assessment.source,
        "status": assessment.status,
        "overall_summary": assessment.overall_summary,
        "identified_strengths": assessment.identified_strengths,
        "growth_areas": assessment.growth_areas,
        "archetype_primary": assessment.archetype_primary,
        "archetype_notes": assessment.archetype_notes,
        "teacher_notes": assessment.teacher_notes,
        "knowledge_base_version": assessment.knowledge_base_version,
        "created_at": assessment.created_at.isoformat() if assessment.created_at else None,
        "finalized_at": assessment.finalized_at.isoformat() if assessment.finalized_at else None,
        # New v2 fields
        "profile_detection": profile_detection,
        "instructional_priority": assessment.instructional_priority,
        "criterion_scores": formatted_scores,
        "submission": {
            "id": submission.id,
            "submitted_text": submission.submitted_text,
            "word_count": submission.word_count,
            "submission_date": submission.submission_date.isoformat() if submission.submission_date else None
        } if submission else None,
        "student": {
            "id": student.id,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "preferred_name": student.preferred_name,
            "grade_level": student.grade_level
        } if student else None,
        "assignment": {
            "id": assignment.id,
            "title": assignment.title,
            "task_type": assignment.task_type,
            "prompt_text": assignment.prompt_text,
            "criteria_assessed": criteria_assessed
        } if assignment else None
    }


@app.put("/api/assessments/{assessment_id}")
def update_assessment(
    assessment_id: str,
    update_data: dict,
    db: Session = Depends(get_db)
):
    """
    Update assessment (teacher notes, status changes).
    """
    assessment = crud.update_assessment_dict(db, assessment_id, update_data)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return {"status": "updated", "id": assessment.id}


@app.put("/api/assessments/{assessment_id}/finalize")
def finalize_assessment(assessment_id: str, db: Session = Depends(get_db)):
    """
    Mark an assessment as finalized.
    """
    assessment = crud.finalize_assessment(db, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return {"status": "finalized", "finalized_at": assessment.finalized_at.isoformat() if assessment.finalized_at else None}


@app.put("/api/criterion-scores/{score_id}")
def update_criterion_score(
    score_id: str,
    update_data: dict,
    db: Session = Depends(get_db)
):
    """
    Update a criterion score (teacher annotation).
    """
    score = crud.update_criterion_score(db, score_id, update_data)
    if not score:
        raise HTTPException(status_code=404, detail="Criterion score not found")
    return {"status": "updated", "id": score.id}


# ============== Utility Endpoints ==============

@app.post("/api/seed")
def seed_database(db: Session = Depends(get_db)):
    """Seed the database with sample data for testing."""
    result = crud.seed_sample_data(db)
    return result


@app.get("/api/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


# ============== Debug Endpoints ==============

@app.get("/debug/calibration")
def debug_calibration():
    """
    Debug endpoint to diagnose calibration file loading issues.
    Reports paths, file existence, and sample content.
    """
    from pathlib import Path
    from .knowledge_base import KNOWLEDGE_BASE_PATH, CALIBRATION_PATH

    result = {
        "paths": {
            "knowledge_base_path": str(KNOWLEDGE_BASE_PATH),
            "knowledge_base_resolved": str(KNOWLEDGE_BASE_PATH.resolve()) if KNOWLEDGE_BASE_PATH else None,
            "knowledge_base_exists": KNOWLEDGE_BASE_PATH.exists() if KNOWLEDGE_BASE_PATH else False,
            "calibration_path": str(CALIBRATION_PATH),
            "calibration_resolved": str(CALIBRATION_PATH.resolve()) if CALIBRATION_PATH else None,
            "calibration_exists": CALIBRATION_PATH.exists() if CALIBRATION_PATH else False,
        },
        "calibration_modules": {
            "dir_path": None,
            "dir_exists": False,
            "files": [],
            "file_count": 0,
        },
        "cross_criteria_profiles": {
            "file_path": None,
            "file_exists": False,
            "content_length": 0,
        },
        "sample_content": {
            "file": None,
            "first_200_chars": None,
        },
        "cwd": os.getcwd(),
        "__file__": __file__,
    }

    # Check calibration_modules directory
    calibration_modules_dir = CALIBRATION_PATH / "calibration_modules"
    result["calibration_modules"]["dir_path"] = str(calibration_modules_dir)
    result["calibration_modules"]["dir_exists"] = calibration_modules_dir.exists()

    if calibration_modules_dir.exists():
        files = list(calibration_modules_dir.iterdir())
        result["calibration_modules"]["files"] = [f.name for f in files]
        result["calibration_modules"]["file_count"] = len(files)

        # Try to read first calibration file
        md_files = [f for f in files if f.suffix == '.md']
        if md_files:
            try:
                sample_file = md_files[0]
                content = sample_file.read_text(encoding='utf-8')
                result["sample_content"]["file"] = sample_file.name
                result["sample_content"]["first_200_chars"] = content[:200]
            except Exception as e:
                result["sample_content"]["error"] = str(e)

    # Check cross_criteria_profiles.json
    profiles_path = CALIBRATION_PATH / "cross_criteria_profiles.json"
    result["cross_criteria_profiles"]["file_path"] = str(profiles_path)
    result["cross_criteria_profiles"]["file_exists"] = profiles_path.exists()

    if profiles_path.exists():
        try:
            content = profiles_path.read_text(encoding='utf-8')
            result["cross_criteria_profiles"]["content_length"] = len(content)
        except Exception as e:
            result["cross_criteria_profiles"]["error"] = str(e)

    # Test actual loading functions
    try:
        from .knowledge_base import load_calibration_anchors, format_cross_criteria_profiles_for_prompt

        anchors = load_calibration_anchors(["A", "B"])
        result["load_calibration_anchors_result"] = {
            "length": len(anchors),
            "first_200_chars": anchors[:200] if anchors else None,
            "is_empty": len(anchors) == 0,
        }

        profiles = format_cross_criteria_profiles_for_prompt()
        result["format_cross_criteria_profiles_result"] = {
            "length": len(profiles),
            "first_200_chars": profiles[:200] if profiles else None,
            "is_empty": len(profiles) == 0,
        }
    except Exception as e:
        result["loading_functions_error"] = str(e)

    return result


@app.get("/debug/database")
def debug_database(db: Session = Depends(get_db)):
    """
    Debug endpoint to diagnose database persistence issues.
    Reports database file info, table counts, and volume mount status.
    """
    from .database import DATABASE_DIR, DATABASE_PATH, IS_RAILWAY

    result = {
        "environment": {
            "IS_RAILWAY": IS_RAILWAY,
            "DATABASE_DIR": DATABASE_DIR,
            "DATABASE_PATH": DATABASE_PATH,
            "cwd": os.getcwd(),
        },
        "file_system": {
            "database_dir_exists": os.path.exists(DATABASE_DIR),
            "database_file_exists": os.path.exists(DATABASE_PATH),
            "database_file_size": None,
            "directory_contents": [],
            "directory_writable": False,
        },
        "database_contents": {
            "students_count": 0,
            "assignments_count": 0,
            "submissions_count": 0,
            "assessments_count": 0,
        },
        "volume_mount_test": {
            "test_file_created": False,
            "test_file_read_back": False,
            "error": None,
        }
    }

    # Check file system
    if os.path.exists(DATABASE_PATH):
        result["file_system"]["database_file_size"] = os.path.getsize(DATABASE_PATH)

    if os.path.exists(DATABASE_DIR):
        try:
            result["file_system"]["directory_contents"] = os.listdir(DATABASE_DIR)
        except Exception as e:
            result["file_system"]["directory_contents_error"] = str(e)

        # Test if directory is writable
        try:
            test_file = os.path.join(DATABASE_DIR, ".write_test")
            with open(test_file, 'w') as f:
                f.write("test")
            result["file_system"]["directory_writable"] = True
            os.remove(test_file)
        except Exception as e:
            result["file_system"]["directory_writable"] = False
            result["file_system"]["write_error"] = str(e)

    # Count records in database
    try:
        from . import models
        result["database_contents"]["students_count"] = db.query(models.Student).count()
        result["database_contents"]["assignments_count"] = db.query(models.Assignment).count()
        result["database_contents"]["submissions_count"] = db.query(models.Submission).count()
        result["database_contents"]["assessments_count"] = db.query(models.Assessment).count()
    except Exception as e:
        result["database_contents"]["error"] = str(e)

    # Test volume persistence with a marker file
    if IS_RAILWAY:
        marker_file = os.path.join(DATABASE_DIR, ".persistence_marker")
        try:
            if os.path.exists(marker_file):
                with open(marker_file, 'r') as f:
                    content = f.read()
                result["volume_mount_test"]["marker_exists"] = True
                result["volume_mount_test"]["marker_content"] = content
            else:
                # Create marker for next deployment
                from datetime import datetime
                with open(marker_file, 'w') as f:
                    f.write(f"Created at: {datetime.utcnow().isoformat()}")
                result["volume_mount_test"]["marker_created"] = True
                result["volume_mount_test"]["message"] = "Marker file created. Check after next deployment to verify persistence."
        except Exception as e:
            result["volume_mount_test"]["error"] = str(e)

    return result
