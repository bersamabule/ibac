# Phase 2 Specification: Assessment Engine
## IB Assessment Companion MVP

**For:** Claude Code  
**Project Path:** C:\IB_Assessment_App  
**Date:** December 2025  
**Prerequisite:** Phase 1 complete (database + data entry working)

---

## Overview

Phase 2 adds the core Expert System functionality: generating AI-powered assessments of student work using the IB MYP knowledge base.

**What we're building:**
1. Claude API integration
2. Knowledge base loading system
3. Assessment generation with structured output
4. Assessment display and review interface
5. Teacher annotation and finalization workflow

---

## New Dependencies

Add to `requirements.txt`:

```
anthropic==0.39.0
```

---

## Environment Configuration

The `.env` file should contain:

```
ANTHROPIC_API_KEY=your-api-key-here
```

---

## Knowledge Base Loading

### File: `backend/knowledge_base.py`

Create a module that loads the knowledge base markdown files and assembles them into prompts.

```python
"""
Knowledge Base Loader

Loads markdown modules from the knowledge_base directory and assembles
them into context for the assessment engine.
"""

import os
from pathlib import Path

KNOWLEDGE_BASE_PATH = Path(__file__).parent.parent / "knowledge_base"

def load_module(relative_path: str) -> str:
    """Load a single markdown module."""
    full_path = KNOWLEDGE_BASE_PATH / relative_path
    if full_path.exists():
        return full_path.read_text(encoding='utf-8')
    return ""

def load_system_prompt() -> str:
    """Load the core system prompt."""
    return load_module("00_SYSTEM_PROMPT.md")

def load_criterion_modules(criteria: list[str]) -> str:
    """
    Load modules for specified criteria.
    
    Args:
        criteria: List of criterion letters, e.g., ["A", "B"]
    
    Returns:
        Combined content of all relevant modules
    """
    content_parts = []
    
    criterion_map = {
        "A": "01_CRITERION_A_ANALYSING",
        "B": "02_CRITERION_B_ORGANIZING", 
        "C": "03_CRITERION_C_PRODUCING",
        "D": "04_CRITERION_D_LANGUAGE"
    }
    
    for criterion in criteria:
        folder = criterion_map.get(criterion.upper())
        if folder:
            folder_path = KNOWLEDGE_BASE_PATH / folder
            if folder_path.exists():
                for md_file in sorted(folder_path.glob("*.md")):
                    content_parts.append(f"## {md_file.stem}\n\n{md_file.read_text(encoding='utf-8')}")
    
    return "\n\n---\n\n".join(content_parts)

def load_cross_criteria() -> str:
    """Load cross-criteria modules (archetypes, compensation rules, etc.)."""
    content_parts = []
    folder_path = KNOWLEDGE_BASE_PATH / "05_CROSS_CRITERIA"
    
    if folder_path.exists():
        for md_file in sorted(folder_path.glob("*.md")):
            content_parts.append(md_file.read_text(encoding='utf-8'))
    
    return "\n\n---\n\n".join(content_parts)

def load_assessment_protocols() -> str:
    """Load assessment protocol modules."""
    content_parts = []
    folder_path = KNOWLEDGE_BASE_PATH / "06_ASSESSMENT_PROTOCOLS"
    
    if folder_path.exists():
        for md_file in sorted(folder_path.glob("*.md")):
            content_parts.append(md_file.read_text(encoding='utf-8'))
    
    return "\n\n---\n\n".join(content_parts)

def load_diagnostic_tools() -> str:
    """Load diagnostic tool modules."""
    content_parts = []
    folder_path = KNOWLEDGE_BASE_PATH / "07_DIAGNOSTIC_TOOLS"
    
    if folder_path.exists():
        for md_file in sorted(folder_path.glob("*.md")):
            content_parts.append(md_file.read_text(encoding='utf-8'))
    
    return "\n\n---\n\n".join(content_parts)

def assemble_assessment_context(criteria: list[str]) -> str:
    """
    Assemble the full knowledge base context for an assessment.
    
    Args:
        criteria: List of criteria being assessed, e.g., ["A"] or ["A", "B"]
    
    Returns:
        Complete context string to include in the API prompt
    """
    parts = [
        "# IB MYP Assessment Expert System Knowledge Base\n",
        load_system_prompt(),
        "\n\n# Criterion-Specific Frameworks\n",
        load_criterion_modules(criteria),
        "\n\n# Cross-Criteria Frameworks\n",
        load_cross_criteria(),
        "\n\n# Assessment Protocols\n",
        load_assessment_protocols(),
        "\n\n# Diagnostic Tools\n",
        load_diagnostic_tools()
    ]
    
    return "\n".join(parts)
```

---

## Assessment Generation

### File: `backend/assessment_engine.py`

```python
"""
Assessment Engine

Generates IB MYP assessments using Claude API and the knowledge base.
"""

import json
import os
from anthropic import Anthropic
from dotenv import load_dotenv
from .knowledge_base import assemble_assessment_context

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

ASSESSMENT_PROMPT_TEMPLATE = """
You are an expert IB MYP Language and Literature assessor. You have been provided with comprehensive training materials in the knowledge base above.

## Your Task

Assess the following student submission according to IB MYP criteria.

### Assignment Information
- **Title:** {assignment_title}
- **Task Type:** {task_type}
- **Prompt Given to Student:** {prompt_text}
- **Criteria Being Assessed:** {criteria_list}

### Student Information
- **Name:** {student_name}
- **Grade Level:** {grade_level}

### Student Submission
```
{submitted_text}
```
Word Count: {word_count}

---

## Required Output Format

You MUST respond with a valid JSON object matching this exact structure. Do not include any text before or after the JSON.

```json
{{
  "overall_summary": "A 2-3 sentence holistic summary of the student's performance across all assessed criteria.",
  
  "identified_strengths": "Key strengths demonstrated in this work (2-4 bullet points as a single string, separated by semicolons).",
  
  "growth_areas": "Priority areas for improvement (2-3 bullet points as a single string, separated by semicolons).",
  
  "archetype_primary": "The primary student archetype that best fits this work (e.g., 'Summarizer', 'Tour Guide', 'Architect', 'Thinker in Translation', 'Polished Hollow', etc.)",
  
  "archetype_notes": "Brief explanation (1-2 sentences) of why this archetype classification was assigned.",
  
  "criterion_scores": [
    {{
      "criterion": "A",
      "level": 4,
      "level_rationale": "Detailed explanation (3-5 sentences) justifying this achievement level with specific reference to the level descriptors and student evidence.",
      "strand_scores": {{
        "strand_i": {{"descriptor": "identify and explain content, context, language, structure, technique, style", "performance": "adequate", "notes": "Specific observations about this strand"}},
        "strand_ii": {{"descriptor": "identify and explain effects of creator's choices", "performance": "limited", "notes": "Specific observations"}},
        "strand_iii": {{"descriptor": "justify opinions using examples and terminology", "performance": "adequate", "notes": "Specific observations"}},
        "strand_iv": {{"descriptor": "evaluate similarities and differences", "performance": "not assessed", "notes": "Not applicable to this task"}}
      }},
      "evidence_quotes": [
        {{"quote": "Exact quote from student work", "analysis": "What this quote demonstrates about their performance"}},
        {{"quote": "Another quote", "analysis": "Analysis of this evidence"}}
      ],
      "diagnostic_notes": "Additional observations using diagnostic frameworks (e.g., Technique-Meaning Bridge status, So What test results, etc.)"
    }}
  ]
}}
```

### Important Guidelines

1. **Be criterion-specific:** Only include criterion_scores entries for the criteria being assessed ({criteria_list}).

2. **Use the knowledge base:** Apply the diagnostic frameworks, archetypes, and level descriptors from your training. Reference specific concepts like "Technique-Meaning Bridge," "Container vs Contents," compensation rules, etc.

3. **Provide evidence:** Every level assignment must be justified with specific quotes from the student's work.

4. **Be calibrated:** Remember that Level 3-4 is typical for this age group, Level 5-6 is strong, and Level 7-8 is exceptional. Do not inflate scores.

5. **Strand scoring:** Use "limited", "adequate", "substantial", or "excellent" for strand performance. Use "not assessed" if a strand doesn't apply to this task.

6. **Be constructive:** Feedback should be honest but developmental—identify the path forward.

Now generate the assessment JSON:
"""

def generate_assessment(
    assignment_title: str,
    task_type: str,
    prompt_text: str,
    criteria_assessed: list[str],
    student_name: str,
    grade_level: int,
    submitted_text: str,
    word_count: int
) -> dict:
    """
    Generate an IB MYP assessment for a student submission.
    
    Returns:
        dict: The parsed assessment data
    
    Raises:
        ValueError: If the API response cannot be parsed as valid JSON
    """
    
    # Assemble the knowledge base context
    knowledge_base = assemble_assessment_context(criteria_assessed)
    
    # Format the criteria list
    criteria_list = ", ".join([f"Criterion {c}" for c in criteria_assessed])
    
    # Build the assessment prompt
    assessment_prompt = ASSESSMENT_PROMPT_TEMPLATE.format(
        assignment_title=assignment_title,
        task_type=task_type,
        prompt_text=prompt_text,
        criteria_list=criteria_list,
        student_name=student_name,
        grade_level=grade_level,
        submitted_text=submitted_text,
        word_count=word_count
    )
    
    # Call Claude API
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": f"{knowledge_base}\n\n---\n\n{assessment_prompt}"
            }
        ]
    )
    
    # Extract the response text
    response_text = message.content[0].text.strip()
    
    # Parse JSON from response
    # Handle case where response might have markdown code blocks
    if response_text.startswith("```"):
        # Extract JSON from code block
        lines = response_text.split("\n")
        json_lines = []
        in_json = False
        for line in lines:
            if line.startswith("```json"):
                in_json = True
                continue
            elif line.startswith("```"):
                in_json = False
                continue
            elif in_json:
                json_lines.append(line)
        response_text = "\n".join(json_lines)
    
    try:
        assessment_data = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse assessment response as JSON: {e}\n\nResponse was:\n{response_text}")
    
    return assessment_data
```

---

## New API Endpoints

### Add to `backend/main.py`:

```python
from .assessment_engine import generate_assessment

@app.post("/api/submissions/{submission_id}/assess")
async def create_assessment(submission_id: str, db: Session = Depends(get_db)):
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
    criteria = json.loads(assignment.criteria_assessed)
    
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
    
    # Create assessment record
    assessment = crud.create_assessment(
        db,
        submission_id=submission_id,
        source="AI_GENERATED",
        overall_summary=assessment_data.get("overall_summary"),
        identified_strengths=assessment_data.get("identified_strengths"),
        growth_areas=assessment_data.get("growth_areas"),
        archetype_primary=assessment_data.get("archetype_primary"),
        archetype_notes=assessment_data.get("archetype_notes")
    )
    
    # Create criterion score records
    for score_data in assessment_data.get("criterion_scores", []):
        crud.create_criterion_score(
            db,
            assessment_id=assessment.id,
            criterion=score_data.get("criterion"),
            level=score_data.get("level"),
            level_rationale=score_data.get("level_rationale"),
            strand_scores=json.dumps(score_data.get("strand_scores", {})),
            evidence_quotes=json.dumps(score_data.get("evidence_quotes", [])),
            diagnostic_notes=score_data.get("diagnostic_notes")
        )
    
    return {"assessment_id": assessment.id, "status": "created"}


@app.get("/api/assessments/{assessment_id}")
async def get_assessment(assessment_id: str, db: Session = Depends(get_db)):
    """
    Get a full assessment with all criterion scores.
    """
    assessment = crud.get_assessment_with_scores(db, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment


@app.put("/api/assessments/{assessment_id}")
async def update_assessment(
    assessment_id: str,
    update_data: dict,
    db: Session = Depends(get_db)
):
    """
    Update assessment (teacher notes, status changes).
    """
    assessment = crud.update_assessment(db, assessment_id, update_data)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment


@app.put("/api/assessments/{assessment_id}/finalize")
async def finalize_assessment(assessment_id: str, db: Session = Depends(get_db)):
    """
    Mark an assessment as finalized.
    """
    assessment = crud.finalize_assessment(db, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return {"status": "finalized", "finalized_at": assessment.finalized_at}


@app.put("/api/criterion-scores/{score_id}")
async def update_criterion_score(
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
    return score
```

---

## CRUD Operations to Add

### Add to `backend/crud.py`:

```python
def create_assessment(
    db: Session,
    submission_id: str,
    source: str,
    overall_summary: str = None,
    identified_strengths: str = None,
    growth_areas: str = None,
    archetype_primary: str = None,
    archetype_notes: str = None
) -> models.Assessment:
    """Create a new assessment."""
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
        knowledge_base_version="1.0"
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
    diagnostic_notes: str = None
) -> models.CriterionScore:
    """Create a criterion score record."""
    score = models.CriterionScore(
        id=str(uuid.uuid4()),
        assessment_id=assessment_id,
        criterion=criterion,
        level=level,
        level_rationale=level_rationale,
        strand_scores=strand_scores,
        evidence_quotes=evidence_quotes,
        diagnostic_notes=diagnostic_notes
    )
    db.add(score)
    db.commit()
    db.refresh(score)
    return score


def get_assessment_with_scores(db: Session, assessment_id: str):
    """Get assessment with all criterion scores."""
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


def update_assessment(db: Session, assessment_id: str, update_data: dict):
    """Update assessment fields."""
    assessment = db.query(models.Assessment).filter(
        models.Assessment.id == assessment_id
    ).first()
    
    if not assessment:
        return None
    
    for key, value in update_data.items():
        if hasattr(assessment, key):
            setattr(assessment, key, value)
    
    assessment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(assessment)
    return assessment


def finalize_assessment(db: Session, assessment_id: str):
    """Mark assessment as finalized."""
    assessment = db.query(models.Assessment).filter(
        models.Assessment.id == assessment_id
    ).first()
    
    if not assessment:
        return None
    
    assessment.status = "FINALIZED"
    assessment.finalized_at = datetime.utcnow()
    db.commit()
    db.refresh(assessment)
    return assessment


def update_criterion_score(db: Session, score_id: str, update_data: dict):
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
```

---

## Frontend: Assessment View

### New File: `frontend/assessment.html`

Create a new page to display and interact with assessments:

**Key Features:**
1. **Header Section:**
   - Student name, assignment title
   - Assessment status badge (DRAFT / REVIEWED / FINALIZED)
   - Finalize button (disabled if already finalized)

2. **Summary Panel:**
   - Overall summary
   - Identified strengths (displayed as bullet list)
   - Growth areas (displayed as bullet list)
   - Archetype classification with notes

3. **Criterion Scores Section:**
   For each assessed criterion, display:
   - Criterion letter and name (e.g., "Criterion A: Analysing")
   - Achievement level (large, prominent number 1-8)
   - Level rationale (expandable/collapsible)
   - Strand-by-strand breakdown (table)
   - Evidence quotes (with analysis)
   - Diagnostic notes
   - Teacher annotation field (editable textarea)
   - Save annotation button

4. **Original Submission Panel:**
   - Collapsible section showing the original student text
   - Word count

5. **Actions:**
   - "Back to Submissions" link
   - "Finalize Assessment" button
   - Status changes to REVIEWED when teacher adds annotations
   - Status changes to FINALIZED when teacher clicks Finalize

### Styling for Achievement Levels

Use color coding for quick visual recognition:

```css
.level-badge {
  display: inline-block;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  text-align: center;
  line-height: 48px;
  font-size: 24px;
  font-weight: bold;
  color: white;
}

.level-1-2 { background-color: #DC3545; } /* Red - needs support */
.level-3-4 { background-color: #FFC107; color: #333; } /* Yellow - developing */
.level-5-6 { background-color: #28A745; } /* Green - proficient */
.level-7-8 { background-color: #2B579A; } /* Blue - exceptional */
```

---

## Modify Submissions Page

Update `frontend/submissions.html` to:

1. **Add "Assess" button** to each submission row (only if no assessment exists yet)
2. **Add "View Assessment" button** if assessment already exists
3. **Show assessment status** badge in the table

When "Assess" is clicked:
1. Show loading spinner
2. Call `POST /api/submissions/{id}/assess`
3. On success, redirect to `/assessment.html?id={assessment_id}`

---

## Phase 2 Success Criteria

When Phase 2 is complete, the user should be able to:

1. ✅ Click "Assess" on any submission
2. ✅ See a loading state while assessment generates (10-30 seconds)
3. ✅ View the complete assessment with all criterion scores
4. ✅ See evidence quotes from the student's work
5. ✅ Add teacher annotations to any criterion
6. ✅ Finalize an assessment
7. ✅ View the original submission alongside the assessment

---

## Testing the Assessment Engine

After building, test with your existing submission (Emma Wilson's poetry analysis):

1. Go to Submissions page
2. Click "Assess" on Emma's submission
3. Wait for assessment generation
4. Review the generated assessment
5. Try adding a teacher annotation
6. Finalize the assessment

**Expected behavior:**
- Assessment should reference IB terminology and frameworks
- Criterion A should be assessed (since it's a poetry analysis)
- Level should likely be in the 3-5 range for typical middle school work
- Evidence quotes should be actual excerpts from the submission

---

## Troubleshooting

**"API key not found" error:**
- Check that `.env` file exists in project root
- Check that `ANTHROPIC_API_KEY` is set correctly
- Restart the server after adding/changing `.env`

**"Assessment generation failed" error:**
- Check the server console for detailed error message
- Common issues: JSON parsing failure, API rate limit
- Try regenerating the assessment

**Assessment seems wrong or off:**
- Review the knowledge base files—are they in the right location?
- Check that criteria_assessed is properly set on the assignment
- The model may need prompt refinement for edge cases
