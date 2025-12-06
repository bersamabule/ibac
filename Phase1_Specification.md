# Phase 1 Specification: Database + Data Entry System
## IB Assessment Companion MVP

**For:** Claude Code  
**Project Path:** C:\IB_Assessment_App  
**Date:** December 2025

---

## Project Overview

Build a local web application for tracking IB MYP Language and Literature student assessments. This is Phase 1: Database setup and data entry forms.

**Tech Stack:**
- Backend: Python 3.11+ with FastAPI
- Database: SQLite
- Frontend: HTML/CSS/JavaScript (no framework)
- Local development server

---

## Project Structure to Create

```
C:\IB_Assessment_App\
├── backend\
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database connection and setup
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   └── crud.py              # Database operations
├── frontend\
│   ├── index.html           # Dashboard/home page
│   ├── students.html        # Student management
│   ├── assignments.html     # Assignment management
│   ├── submissions.html     # Submission entry
│   ├── css\
│   │   └── styles.css       # Styling
│   └── js\
│       └── app.js           # Frontend JavaScript
├── database\
│   └── ib_assessment.db     # SQLite database (auto-created)
├── knowledge_base\          # Already populated with markdown files
├── .env                     # Environment variables (API key)
└── requirements.txt         # Python dependencies
```

---

## Database Schema

### Table: students

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | UUID, auto-generated |
| student_code | TEXT | NOT NULL, UNIQUE | School-assigned ID |
| first_name | TEXT | NOT NULL | Given name |
| last_name | TEXT | NOT NULL | Family name |
| preferred_name | TEXT | NULLABLE | Name student prefers |
| class_section | TEXT | NOT NULL | e.g., "7A", "8B" |
| grade_level | INTEGER | NOT NULL | 7 or 8 |
| notes | TEXT | NULLABLE | Teacher notes |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW | Record creation |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW | Last modification |

### Table: assignments

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | UUID, auto-generated |
| title | TEXT | NOT NULL | Assignment title |
| prompt_text | TEXT | NOT NULL | Full prompt given to students |
| task_type | TEXT | NOT NULL | ANALYSIS, COMPARATIVE, CREATIVE, TRANSACTIONAL, INTEGRATED |
| text_type | TEXT | NULLABLE | Genre/form description |
| source_text_info | TEXT | NULLABLE | Description of source texts |
| criteria_assessed | TEXT | NOT NULL | JSON array: ["A"], ["A","B"], etc. |
| word_count_target | INTEGER | NULLABLE | Expected word count |
| date_assigned | DATE | NOT NULL | When assigned |
| date_due | DATE | NULLABLE | Submission deadline |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW | Record creation |

### Table: submissions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | UUID, auto-generated |
| student_id | TEXT | FOREIGN KEY → students.id | Which student |
| assignment_id | TEXT | FOREIGN KEY → assignments.id | Which assignment |
| submitted_text | TEXT | NOT NULL | The actual student work |
| word_count | INTEGER | NOT NULL | Calculated automatically |
| submission_date | TIMESTAMP | NOT NULL | When submitted/entered |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW | Record creation |

**Constraint:** UNIQUE(student_id, assignment_id) — one submission per student per assignment

### Table: assessments

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | UUID, auto-generated |
| submission_id | TEXT | FOREIGN KEY → submissions.id | Which submission |
| version | INTEGER | NOT NULL, DEFAULT 1 | Version number |
| source | TEXT | NOT NULL | AI_GENERATED, AI_REANALYSIS, TEACHER_CREATED |
| status | TEXT | NOT NULL, DEFAULT 'DRAFT' | DRAFT, REVIEWED, FINALIZED |
| overall_summary | TEXT | NULLABLE | Holistic summary |
| identified_strengths | TEXT | NULLABLE | Key strengths |
| growth_areas | TEXT | NULLABLE | Areas for improvement |
| archetype_primary | TEXT | NULLABLE | e.g., "Summarizer", "Tour Guide" |
| archetype_notes | TEXT | NULLABLE | Classification rationale |
| teacher_notes | TEXT | NULLABLE | Teacher annotations |
| knowledge_base_version | TEXT | NOT NULL, DEFAULT '1.0' | KB version used |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW | When generated |
| finalized_at | TIMESTAMP | NULLABLE | When finalized |

### Table: criterion_scores

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | TEXT | PRIMARY KEY | UUID, auto-generated |
| assessment_id | TEXT | FOREIGN KEY → assessments.id | Which assessment |
| criterion | TEXT | NOT NULL | A, B, C, or D |
| level | INTEGER | NOT NULL | 1-8 |
| level_rationale | TEXT | NOT NULL | Explanation for level |
| strand_scores | TEXT | NOT NULL | JSON object with sub-skill breakdown |
| evidence_quotes | TEXT | NOT NULL | JSON array of evidence |
| diagnostic_notes | TEXT | NULLABLE | Additional observations |
| teacher_annotation | TEXT | NULLABLE | Teacher notes on this criterion |

---

## API Endpoints to Create

### Students
- `GET /api/students` — List all students (with optional filter by class_section)
- `GET /api/students/{id}` — Get single student with their submissions
- `POST /api/students` — Create new student
- `PUT /api/students/{id}` — Update student
- `DELETE /api/students/{id}` — Delete student

### Assignments
- `GET /api/assignments` — List all assignments
- `GET /api/assignments/{id}` — Get single assignment with submissions
- `POST /api/assignments` — Create new assignment
- `PUT /api/assignments/{id}` — Update assignment
- `DELETE /api/assignments/{id}` — Delete assignment

### Submissions
- `GET /api/submissions` — List submissions (filter by student_id or assignment_id)
- `GET /api/submissions/{id}` — Get submission with assessments
- `POST /api/submissions` — Create new submission (auto-calculate word_count)
- `DELETE /api/submissions/{id}` — Delete submission

### Assessments (stub for Phase 2)
- `GET /api/assessments/{id}` — Get assessment with criterion scores
- `PUT /api/assessments/{id}` — Update assessment (teacher_notes, status)

---

## Frontend Pages

### 1. Dashboard (index.html)

Simple home page with:
- Navigation links to Students, Assignments, Submissions
- Quick stats: total students, total assignments, total submissions
- Recent activity (last 5 submissions)

### 2. Students Page (students.html)

**Features:**
- Table listing all students (sortable by name, class)
- Filter dropdown by class_section
- "Add Student" button → opens form
- Edit/Delete buttons per row

**Add/Edit Student Form:**
- student_code (required)
- first_name (required)
- last_name (required)
- preferred_name (optional)
- class_section (dropdown: 7A, 7B, 8A, 8B — make configurable)
- grade_level (dropdown: 7, 8)
- notes (textarea, optional)

### 3. Assignments Page (assignments.html)

**Features:**
- Table listing all assignments (sortable by date, title)
- "Add Assignment" button → opens form
- Edit/Delete buttons per row
- Show criteria_assessed as badges (A, B, C, D)

**Add/Edit Assignment Form:**
- title (required)
- prompt_text (textarea, required)
- task_type (dropdown: Analysis, Comparative, Creative, Transactional, Integrated)
- text_type (optional)
- source_text_info (textarea, optional)
- criteria_assessed (checkboxes: A, B, C, D — at least one required)
- word_count_target (number, optional)
- date_assigned (date picker, required)
- date_due (date picker, optional)

### 4. Submissions Page (submissions.html)

**Features:**
- Filter by student (dropdown)
- Filter by assignment (dropdown)
- Table showing submissions with student name, assignment title, word count, date, status
- "New Submission" button → opens form
- Click row to view submission details

**New Submission Form:**
- student_id (searchable dropdown, required)
- assignment_id (dropdown, required)
- submitted_text (large textarea, required)
- Word count displayed live as user types/pastes

---

## Styling Guidelines

Keep it simple, clean, functional:

- Use system fonts (no external font loading)
- Primary color: #2B579A (professional blue)
- Background: #F5F5F5
- Cards/panels: white with subtle shadow
- Tables: striped rows for readability
- Forms: clear labels, adequate spacing
- Responsive: works on laptop screen (no mobile optimization needed for MVP)

---

## Requirements.txt

```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
pydantic==2.5.2
python-dotenv==1.0.0
python-multipart==0.0.6
aiofiles==23.2.1
```

---

## Running the Application

After building, the app should start with:

```bash
cd C:\IB_Assessment_App\backend
uvicorn main:app --reload --port 8000
```

Then open browser to: http://localhost:8000

The frontend HTML files should be served by FastAPI as static files.

---

## Phase 1 Success Criteria

When Phase 1 is complete, the user should be able to:

1. ✅ Start the application with a single command
2. ✅ View a dashboard with navigation
3. ✅ Add, edit, delete, and list students
4. ✅ Add, edit, delete, and list assignments
5. ✅ Create submissions by selecting student + assignment and pasting text
6. ✅ See word count calculated automatically
7. ✅ View list of all submissions with filters
8. ✅ Data persists in SQLite database between sessions

---

## Notes for Implementation

1. Use UUIDs (uuid4) for all primary keys
2. Store JSON fields as TEXT in SQLite (serialize/deserialize in Python)
3. Include proper error handling with user-friendly messages
4. Auto-create database file and tables on first run if they don't exist
5. Add some sample data seeding option for testing
6. Keep console logging for debugging during development
