/**
 * IB Assessment App - Frontend JavaScript
 */

const API_BASE = '/api';

// ============== Utility Functions ==============

/**
 * Make an API request
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    console.log('API Request:', url);
    const config = {
        headers: {
            'Content-Type': 'application/json',
        },
        ...options,
    };

    if (config.body && typeof config.body === 'object') {
        config.body = JSON.stringify(config.body);
    }

    try {
        const response = await fetch(url, config);
        console.log('API Response status:', response.status);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'An error occurred');
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

/**
 * Format datetime for display
 */
function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Count words in text
 */
function countWords(text) {
    if (!text || !text.trim()) return 0;
    return text.trim().split(/\s+/).length;
}

/**
 * Show loading state
 */
function showLoading(container) {
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <span>Loading...</span>
        </div>
    `;
}

/**
 * Show error message
 */
function showError(container, message) {
    container.innerHTML = `
        <div class="alert alert-error">
            ${escapeHtml(message)}
        </div>
    `;
}

/**
 * Show success message
 */
function showAlert(message, type = 'success') {
    const alertsContainer = document.getElementById('alerts');
    if (!alertsContainer) return;

    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    alertsContainer.appendChild(alert);

    setTimeout(() => {
        alert.remove();
    }, 5000);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Create criteria badges
 */
function createCriteriaBadges(criteria) {
    if (!criteria) return '';
    const criteriaArray = typeof criteria === 'string' ? JSON.parse(criteria) : criteria;
    return criteriaArray.map(c =>
        `<span class="badge badge-${c.toLowerCase()}">${c}</span>`
    ).join('');
}

// ============== Modal Functions ==============

/**
 * Open a modal
 */
function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

/**
 * Close a modal
 */
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

/**
 * Close modal when clicking overlay
 */
function setupModalClose() {
    document.querySelectorAll('.modal-overlay').forEach(overlay => {
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                overlay.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    });
}

// ============== Dashboard Functions ==============

async function loadDashboard() {
    const statsContainer = document.getElementById('dashboard-stats');
    const activityContainer = document.getElementById('recent-activity');

    if (!statsContainer) return;

    try {
        showLoading(statsContainer);
        const data = await apiRequest('/dashboard');

        // Render stats
        statsContainer.innerHTML = `
            <div class="stat-card">
                <div class="stat-value">${data.total_students}</div>
                <div class="stat-label">Students</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${data.total_assignments}</div>
                <div class="stat-label">Assignments</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${data.total_submissions}</div>
                <div class="stat-label">Submissions</div>
            </div>
        `;

        // Render recent activity
        if (activityContainer) {
            if (data.recent_submissions.length === 0) {
                activityContainer.innerHTML = `
                    <div class="empty-state">
                        <p>No recent submissions</p>
                    </div>
                `;
            } else {
                activityContainer.innerHTML = `
                    <ul class="activity-list">
                        ${data.recent_submissions.map(sub => `
                            <li class="activity-item">
                                <div class="activity-info">
                                    <div class="activity-title">
                                        ${escapeHtml(sub.student?.first_name || '')} ${escapeHtml(sub.student?.last_name || '')}
                                    </div>
                                    <div class="activity-meta">
                                        ${escapeHtml(sub.assignment?.title || 'Unknown Assignment')}
                                        &bull; ${sub.word_count} words
                                    </div>
                                </div>
                                <div class="activity-date text-muted">
                                    ${formatDateTime(sub.submission_date)}
                                </div>
                            </li>
                        `).join('')}
                    </ul>
                `;
            }
        }
    } catch (error) {
        showError(statsContainer, 'Failed to load dashboard data');
    }
}

// ============== Student Functions ==============

let allStudents = [];

async function loadStudents(classSection = '') {
    const container = document.getElementById('students-table-body');
    if (!container) return;

    try {
        // Show loading in the tbody itself (not parent, which would destroy the table structure)
        container.innerHTML = `
            <tr>
                <td colspan="6" class="loading">
                    <div class="spinner"></div>
                    <span>Loading...</span>
                </td>
            </tr>
        `;
        const endpoint = classSection ? `/students?class_section=${classSection}` : '/students';
        allStudents = await apiRequest(endpoint);

        renderStudentsTable(allStudents);
    } catch (error) {
        container.innerHTML = `
            <tr>
                <td colspan="6" class="alert alert-error">
                    Failed to load students: ${escapeHtml(error.message)}
                </td>
            </tr>
        `;
    }
}

function renderStudentsTable(students) {
    const container = document.getElementById('students-table-body');
    if (!container) return;

    if (students.length === 0) {
        container.innerHTML = `
            <tr>
                <td colspan="6" class="empty-state">
                    No students found. Click "Add Student" to create one.
                </td>
            </tr>
        `;
        return;
    }

    container.innerHTML = students.map(student => `
        <tr>
            <td>${escapeHtml(student.student_code)}</td>
            <td>${escapeHtml(student.first_name)} ${escapeHtml(student.last_name)}</td>
            <td>${escapeHtml(student.preferred_name || '-')}</td>
            <td>${escapeHtml(student.class_section)}</td>
            <td>${student.grade_level}</td>
            <td>
                <div class="btn-group">
                    <button class="btn btn-sm btn-secondary" onclick="editStudent('${student.id}')">Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteStudent('${student.id}')">Delete</button>
                </div>
            </td>
        </tr>
    `).join('');
}

function openStudentForm(studentId = null) {
    const form = document.getElementById('student-form');
    const title = document.getElementById('student-modal-title');

    form.reset();
    document.getElementById('student-id').value = '';

    if (studentId) {
        title.textContent = 'Edit Student';
        const student = allStudents.find(s => s.id === studentId);
        if (student) {
            document.getElementById('student-id').value = student.id;
            document.getElementById('student-code').value = student.student_code;
            document.getElementById('first-name').value = student.first_name;
            document.getElementById('last-name').value = student.last_name;
            document.getElementById('preferred-name').value = student.preferred_name || '';
            document.getElementById('class-section').value = student.class_section;
            document.getElementById('grade-level').value = student.grade_level;
            document.getElementById('student-notes').value = student.notes || '';
        }
    } else {
        title.textContent = 'Add Student';
    }

    openModal('student-modal');
}

function editStudent(studentId) {
    openStudentForm(studentId);
}

async function saveStudent(event) {
    event.preventDefault();

    const studentId = document.getElementById('student-id').value;
    const data = {
        student_code: document.getElementById('student-code').value,
        first_name: document.getElementById('first-name').value,
        last_name: document.getElementById('last-name').value,
        preferred_name: document.getElementById('preferred-name').value || null,
        class_section: document.getElementById('class-section').value,
        grade_level: parseInt(document.getElementById('grade-level').value),
        notes: document.getElementById('student-notes').value || null,
    };

    try {
        if (studentId) {
            await apiRequest(`/students/${studentId}`, { method: 'PUT', body: data });
            showAlert('Student updated successfully');
        } else {
            await apiRequest('/students', { method: 'POST', body: data });
            showAlert('Student created successfully');
        }

        closeModal('student-modal');
        loadStudents();
    } catch (error) {
        showAlert(error.message, 'error');
    }
}

async function deleteStudent(studentId) {
    if (!confirm('Are you sure you want to delete this student? This will also delete all their submissions.')) {
        return;
    }

    try {
        await apiRequest(`/students/${studentId}`, { method: 'DELETE' });
        showAlert('Student deleted successfully');
        loadStudents();
    } catch (error) {
        showAlert(error.message, 'error');
    }
}

// ============== Student Import Functions ==============

function openImportModal() {
    // Reset the modal state
    const fileInput = document.getElementById('csv-file');
    const resultDiv = document.getElementById('import-result');
    const importBtn = document.getElementById('import-btn');

    if (fileInput) fileInput.value = '';
    if (resultDiv) {
        resultDiv.style.display = 'none';
        resultDiv.innerHTML = '';
    }
    if (importBtn) {
        importBtn.disabled = false;
        importBtn.textContent = 'Import';
    }

    openModal('import-modal');
}

async function importStudents() {
    const fileInput = document.getElementById('csv-file');
    const resultDiv = document.getElementById('import-result');
    const importBtn = document.getElementById('import-btn');

    if (!fileInput.files || fileInput.files.length === 0) {
        showAlert('Please select a CSV file', 'error');
        return;
    }

    const file = fileInput.files[0];

    // Disable button and show loading state
    importBtn.disabled = true;
    importBtn.textContent = 'Importing...';
    resultDiv.style.display = 'none';

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/students/import', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Import failed');
        }

        // Show result
        resultDiv.style.display = 'block';
        resultDiv.style.backgroundColor = '#d4edda';
        resultDiv.style.color = '#155724';

        let resultHtml = `<strong>Import Complete!</strong><br>`;
        resultHtml += `Imported: ${data.imported} student(s)<br>`;
        resultHtml += `Skipped (duplicates): ${data.skipped}`;

        if (data.total_errors > 0) {
            resultHtml += `<br><br><strong style="color: #856404;">Errors (${data.total_errors}):</strong><br>`;
            resultHtml += data.errors.map(e => `<small>${escapeHtml(e)}</small>`).join('<br>');
            if (data.total_errors > 10) {
                resultHtml += `<br><small>...and ${data.total_errors - 10} more</small>`;
            }
            resultDiv.style.backgroundColor = '#fff3cd';
            resultDiv.style.color = '#856404';
        }

        resultDiv.innerHTML = resultHtml;

        // Reload students table
        loadStudents();

        // Update button
        importBtn.textContent = 'Done';

    } catch (error) {
        resultDiv.style.display = 'block';
        resultDiv.style.backgroundColor = '#f8d7da';
        resultDiv.style.color = '#721c24';
        resultDiv.innerHTML = `<strong>Import Failed</strong><br>${escapeHtml(error.message)}`;

        importBtn.disabled = false;
        importBtn.textContent = 'Retry';
    }
}

// ============== Assignment Functions ==============

let allAssignments = [];

async function loadAssignments() {
    const container = document.getElementById('assignments-table-body');
    if (!container) return;

    try {
        // Show loading in the tbody itself (not parent, which would destroy the table structure)
        container.innerHTML = `
            <tr>
                <td colspan="6" class="loading">
                    <div class="spinner"></div>
                    <span>Loading...</span>
                </td>
            </tr>
        `;
        allAssignments = await apiRequest('/assignments');

        renderAssignmentsTable(allAssignments);
    } catch (error) {
        container.innerHTML = `
            <tr>
                <td colspan="6" class="alert alert-error">
                    Failed to load assignments: ${escapeHtml(error.message)}
                </td>
            </tr>
        `;
    }
}

function renderAssignmentsTable(assignments) {
    const container = document.getElementById('assignments-table-body');
    if (!container) return;

    if (assignments.length === 0) {
        container.innerHTML = `
            <tr>
                <td colspan="6" class="empty-state">
                    No assignments found. Click "Add Assignment" to create one.
                </td>
            </tr>
        `;
        return;
    }

    container.innerHTML = assignments.map(assignment => `
        <tr>
            <td>${escapeHtml(assignment.title)}</td>
            <td>${escapeHtml(assignment.task_type)}</td>
            <td>
                <div class="badge-group">
                    ${createCriteriaBadges(assignment.criteria_assessed)}
                </div>
            </td>
            <td>${formatDate(assignment.date_assigned)}</td>
            <td>${formatDate(assignment.date_due)}</td>
            <td>
                <div class="btn-group">
                    <button class="btn btn-sm btn-secondary" onclick="editAssignment('${assignment.id}')">Edit</button>
                    <button class="btn btn-sm btn-danger" onclick="deleteAssignment('${assignment.id}')">Delete</button>
                </div>
            </td>
        </tr>
    `).join('');
}

function openAssignmentForm(assignmentId = null) {
    const form = document.getElementById('assignment-form');
    const title = document.getElementById('assignment-modal-title');

    form.reset();
    document.getElementById('assignment-id').value = '';

    // Uncheck all criteria checkboxes
    document.querySelectorAll('input[name="criteria"]').forEach(cb => cb.checked = false);

    if (assignmentId) {
        title.textContent = 'Edit Assignment';
        const assignment = allAssignments.find(a => a.id === assignmentId);
        if (assignment) {
            document.getElementById('assignment-id').value = assignment.id;
            document.getElementById('assignment-title').value = assignment.title;
            document.getElementById('prompt-text').value = assignment.prompt_text;
            document.getElementById('task-type').value = assignment.task_type;
            document.getElementById('text-type').value = assignment.text_type || '';
            document.getElementById('source-text-info').value = assignment.source_text_info || '';
            document.getElementById('word-count-target').value = assignment.word_count_target || '';
            document.getElementById('date-assigned').value = assignment.date_assigned;
            document.getElementById('date-due').value = assignment.date_due || '';

            // Check criteria checkboxes
            const criteria = typeof assignment.criteria_assessed === 'string'
                ? JSON.parse(assignment.criteria_assessed)
                : assignment.criteria_assessed;
            criteria.forEach(c => {
                const checkbox = document.querySelector(`input[name="criteria"][value="${c}"]`);
                if (checkbox) checkbox.checked = true;
            });
        }
    } else {
        title.textContent = 'Add Assignment';
        // Set default date to today
        document.getElementById('date-assigned').value = new Date().toISOString().split('T')[0];
    }

    openModal('assignment-modal');
}

function editAssignment(assignmentId) {
    openAssignmentForm(assignmentId);
}

async function saveAssignment(event) {
    event.preventDefault();

    const assignmentId = document.getElementById('assignment-id').value;

    // Get checked criteria
    const criteriaChecked = [];
    document.querySelectorAll('input[name="criteria"]:checked').forEach(cb => {
        criteriaChecked.push(cb.value);
    });

    if (criteriaChecked.length === 0) {
        showAlert('Please select at least one criterion', 'error');
        return;
    }

    const data = {
        title: document.getElementById('assignment-title').value,
        prompt_text: document.getElementById('prompt-text').value,
        task_type: document.getElementById('task-type').value,
        text_type: document.getElementById('text-type').value || null,
        source_text_info: document.getElementById('source-text-info').value || null,
        criteria_assessed: criteriaChecked,
        word_count_target: document.getElementById('word-count-target').value
            ? parseInt(document.getElementById('word-count-target').value)
            : null,
        date_assigned: document.getElementById('date-assigned').value,
        date_due: document.getElementById('date-due').value || null,
    };

    try {
        if (assignmentId) {
            await apiRequest(`/assignments/${assignmentId}`, { method: 'PUT', body: data });
            showAlert('Assignment updated successfully');
        } else {
            await apiRequest('/assignments', { method: 'POST', body: data });
            showAlert('Assignment created successfully');
        }

        closeModal('assignment-modal');
        loadAssignments();
    } catch (error) {
        showAlert(error.message, 'error');
    }
}

async function deleteAssignment(assignmentId) {
    if (!confirm('Are you sure you want to delete this assignment? This will also delete all related submissions.')) {
        return;
    }

    try {
        await apiRequest(`/assignments/${assignmentId}`, { method: 'DELETE' });
        showAlert('Assignment deleted successfully');
        loadAssignments();
    } catch (error) {
        showAlert(error.message, 'error');
    }
}

// ============== Submission Functions ==============

let allSubmissions = [];
let submissionStudents = [];
let submissionAssignments = [];

async function loadSubmissions(studentId = '', assignmentId = '') {
    const container = document.getElementById('submissions-table-body');
    if (!container) return;

    try {
        // Show loading in the tbody itself
        container.innerHTML = `
            <tr>
                <td colspan="6" class="loading">
                    <div class="spinner"></div>
                    <span>Loading...</span>
                </td>
            </tr>
        `;

        // Build query string
        const params = new URLSearchParams();
        if (studentId) params.append('student_id', studentId);
        if (assignmentId) params.append('assignment_id', assignmentId);

        const query = params.toString() ? `?${params.toString()}` : '';
        allSubmissions = await apiRequest(`/submissions${query}`);

        renderSubmissionsTable(allSubmissions);
    } catch (error) {
        container.innerHTML = `
            <tr>
                <td colspan="6" class="alert alert-error">
                    Failed to load submissions: ${escapeHtml(error.message)}
                </td>
            </tr>
        `;
    }
}

function renderSubmissionsTable(submissions) {
    const container = document.getElementById('submissions-table-body');
    if (!container) return;

    if (submissions.length === 0) {
        container.innerHTML = `
            <tr>
                <td colspan="6" class="empty-state">
                    No submissions found. Click "New Submission" to create one.
                </td>
            </tr>
        `;
        return;
    }

    container.innerHTML = submissions.map(sub => {
        const hasAssessment = sub.assessments && sub.assessments.length > 0;
        const assessmentId = hasAssessment ? sub.assessments[0].id : null;
        const assessmentStatus = hasAssessment ? sub.assessments[0].status : null;

        // Determine status badge
        let statusBadge = '<span class="badge">Pending</span>';
        if (hasAssessment) {
            if (assessmentStatus === 'FINALIZED') {
                statusBadge = '<span class="badge" style="background-color: #28a745; color: white;">Finalized</span>';
            } else if (assessmentStatus === 'REVIEWED') {
                statusBadge = '<span class="badge" style="background-color: #17a2b8; color: white;">Reviewed</span>';
            } else {
                statusBadge = '<span class="badge badge-primary">Draft</span>';
            }
        }

        // Determine action button
        let actionButton = '';
        if (hasAssessment) {
            actionButton = `<button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); viewAssessment('${assessmentId}')">View Assessment</button>`;
        } else {
            actionButton = `<button class="btn btn-sm btn-success" onclick="event.stopPropagation(); generateAssessment('${sub.id}')">Assess</button>`;
        }

        return `
            <tr onclick="viewSubmission('${sub.id}')" style="cursor: pointer;">
                <td>${escapeHtml(sub.student?.first_name || '')} ${escapeHtml(sub.student?.last_name || '')}</td>
                <td>${escapeHtml(sub.assignment?.title || '-')}</td>
                <td>${sub.word_count}</td>
                <td>${formatDateTime(sub.submission_date)}</td>
                <td>${statusBadge}</td>
                <td>
                    <div class="btn-group">
                        ${actionButton}
                        <button class="btn btn-sm btn-danger" onclick="event.stopPropagation(); deleteSubmission('${sub.id}')">Delete</button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

async function loadSubmissionFilters() {
    try {
        // Load students and assignments for filters
        const [students, assignments] = await Promise.all([
            apiRequest('/students'),
            apiRequest('/assignments')
        ]);

        submissionStudents = students;
        submissionAssignments = assignments;

        // Populate student filter
        const studentFilter = document.getElementById('filter-student');
        if (studentFilter) {
            studentFilter.innerHTML = '<option value="">All Students</option>' +
                students.map(s => `<option value="${s.id}">${escapeHtml(s.first_name)} ${escapeHtml(s.last_name)}</option>`).join('');
        }

        // Populate assignment filter
        const assignmentFilter = document.getElementById('filter-assignment');
        if (assignmentFilter) {
            assignmentFilter.innerHTML = '<option value="">All Assignments</option>' +
                assignments.map(a => `<option value="${a.id}">${escapeHtml(a.title)}</option>`).join('');
        }

        // Populate form dropdowns
        const studentSelect = document.getElementById('submission-student');
        if (studentSelect) {
            studentSelect.innerHTML = '<option value="">Select a student...</option>' +
                students.map(s => `<option value="${s.id}">${escapeHtml(s.first_name)} ${escapeHtml(s.last_name)} (${s.student_code})</option>`).join('');
        }

        const assignmentSelect = document.getElementById('submission-assignment');
        if (assignmentSelect) {
            assignmentSelect.innerHTML = '<option value="">Select an assignment...</option>' +
                assignments.map(a => `<option value="${a.id}">${escapeHtml(a.title)}</option>`).join('');
        }
    } catch (error) {
        console.error('Failed to load filters:', error);
    }
}

function applySubmissionFilters() {
    const studentId = document.getElementById('filter-student')?.value || '';
    const assignmentId = document.getElementById('filter-assignment')?.value || '';
    loadSubmissions(studentId, assignmentId);
}

function openSubmissionForm() {
    const form = document.getElementById('submission-form');
    form.reset();
    updateWordCount();
    openModal('submission-modal');
}

function updateWordCount() {
    const textarea = document.getElementById('submitted-text');
    const wordCountDisplay = document.getElementById('word-count-display');

    if (textarea && wordCountDisplay) {
        const count = countWords(textarea.value);
        wordCountDisplay.textContent = `${count} words`;

        // Check against target if assignment is selected
        const assignmentId = document.getElementById('submission-assignment')?.value;
        if (assignmentId) {
            const assignment = submissionAssignments.find(a => a.id === assignmentId);
            if (assignment && assignment.word_count_target) {
                const target = assignment.word_count_target;
                const diff = count - target;
                if (Math.abs(diff) > target * 0.1) {
                    wordCountDisplay.classList.add(diff > 0 ? 'over' : 'warning');
                    wordCountDisplay.classList.remove(diff > 0 ? 'warning' : 'over');
                } else {
                    wordCountDisplay.classList.remove('warning', 'over');
                }
            }
        }
    }
}

async function saveSubmission(event) {
    event.preventDefault();

    const data = {
        student_id: document.getElementById('submission-student').value,
        assignment_id: document.getElementById('submission-assignment').value,
        submitted_text: document.getElementById('submitted-text').value,
    };

    try {
        await apiRequest('/submissions', { method: 'POST', body: data });
        showAlert('Submission created successfully');
        closeModal('submission-modal');
        loadSubmissions();
    } catch (error) {
        showAlert(error.message, 'error');
    }
}

async function viewSubmission(submissionId) {
    try {
        const submission = await apiRequest(`/submissions/${submissionId}`);

        document.getElementById('view-student-name').textContent =
            `${submission.student?.first_name || ''} ${submission.student?.last_name || ''}`;
        document.getElementById('view-assignment-title').textContent =
            submission.assignment?.title || '-';
        document.getElementById('view-word-count').textContent = submission.word_count;
        document.getElementById('view-submission-date').textContent =
            formatDateTime(submission.submission_date);
        document.getElementById('view-submitted-text').textContent = submission.submitted_text;

        openModal('view-submission-modal');
    } catch (error) {
        showAlert('Failed to load submission details', 'error');
    }
}

async function deleteSubmission(submissionId) {
    if (!confirm('Are you sure you want to delete this submission?')) {
        return;
    }

    try {
        await apiRequest(`/submissions/${submissionId}`, { method: 'DELETE' });
        showAlert('Submission deleted successfully');
        loadSubmissions();
    } catch (error) {
        showAlert(error.message, 'error');
    }
}

// ============== Assessment Functions ==============

/**
 * Navigate to view an existing assessment
 */
function viewAssessment(assessmentId) {
    window.location.href = `/assessment.html?id=${assessmentId}`;
}

/**
 * Generate a new assessment for a submission
 */
async function generateAssessment(submissionId) {
    // Show loading overlay
    showLoadingOverlay('Generating assessment... This may take 10-30 seconds.');

    try {
        const result = await apiRequest(`/submissions/${submissionId}/assess`, {
            method: 'POST'
        });

        hideLoadingOverlay();

        if (result.assessment_id) {
            showAlert('Assessment generated successfully!');
            // Navigate to the new assessment
            window.location.href = `/assessment.html?id=${result.assessment_id}`;
        } else {
            showAlert('Assessment created but no ID returned', 'error');
            loadSubmissions();
        }
    } catch (error) {
        hideLoadingOverlay();
        showAlert('Failed to generate assessment: ' + error.message, 'error');
    }
}

/**
 * Show loading overlay for long operations
 */
function showLoadingOverlay(message) {
    // Remove any existing overlay
    hideLoadingOverlay();

    const overlay = document.createElement('div');
    overlay.id = 'loading-overlay';
    overlay.className = 'loading-overlay';
    overlay.innerHTML = `
        <div class="spinner"></div>
        <p>${escapeHtml(message)}</p>
    `;
    document.body.appendChild(overlay);
}

/**
 * Hide loading overlay
 */
function hideLoadingOverlay() {
    const existing = document.getElementById('loading-overlay');
    if (existing) {
        existing.remove();
    }
}

// ============== Initialization ==============

document.addEventListener('DOMContentLoaded', () => {
    // Setup modal close handlers
    setupModalClose();

    // Determine which page we're on and initialize accordingly
    const path = window.location.pathname;

    if (path === '/' || path === '/index.html') {
        loadDashboard();
    } else if (path === '/students.html') {
        loadStudents();

        // Setup class filter
        const classFilter = document.getElementById('filter-class');
        if (classFilter) {
            classFilter.addEventListener('change', (e) => {
                loadStudents(e.target.value);
            });
        }
    } else if (path === '/assignments.html') {
        loadAssignments();
    } else if (path === '/submissions.html') {
        console.log('Submissions page detected, loading data...');
        loadSubmissionFilters()
            .then(() => {
                console.log('Filters loaded, now loading submissions...');
                return loadSubmissions();
            })
            .then(() => {
                console.log('Submissions loaded successfully');
            })
            .catch(err => {
                console.error('Error in submission loading chain:', err);
            });

        // Setup filter handlers
        const filterStudent = document.getElementById('filter-student');
        const filterAssignment = document.getElementById('filter-assignment');

        if (filterStudent) {
            filterStudent.addEventListener('change', applySubmissionFilters);
        }
        if (filterAssignment) {
            filterAssignment.addEventListener('change', applySubmissionFilters);
        }

        // Setup word count update
        const submittedText = document.getElementById('submitted-text');
        if (submittedText) {
            submittedText.addEventListener('input', updateWordCount);
        }

        // Update word count when assignment changes
        const assignmentSelect = document.getElementById('submission-assignment');
        if (assignmentSelect) {
            assignmentSelect.addEventListener('change', updateWordCount);
        }
    }
});
