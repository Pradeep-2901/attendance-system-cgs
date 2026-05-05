/**
 * Admin Dashboard Logic
 */

let currentSection = 'dashboard';

// Initialize admin dashboard
document.addEventListener('DOMContentLoaded', async () => {
    if (!await requireAdmin()) return;
    
    updateUserDisplay();
    await loadDashboard();
});

// Show different sections
async function showSection(section) {
    // Hide all sections
    document.querySelectorAll('[id$="Section"]').forEach(el => el.style.display = 'none');
    
    // Show selected section
    document.getElementById(section + 'Section').style.display = 'block';
    
    // Update active nav
    document.querySelectorAll('.sidebar .nav-link').forEach(el => el.classList.remove('active'));
    event.target.closest('.nav-link').classList.add('active');
    
    currentSection = section;
    
    // Load section data
    switch(section) {
        case 'employees':
            await loadEmployees();
            break;
        case 'attendance':
            await loadAttendance();
            break;
        case 'leave':
            await loadLeaveRequests();
            break;
        case 'compoff':
            await loadCompOffRequests();
            break;
        case 'holidays':
            await loadHolidays();
            break;
    }
}

// Load dashboard metrics
async function loadDashboard() {
    try {
        // Mock data for now - in production, fetch from API
        document.getElementById('totalEmployees').textContent = '4';
        document.getElementById('todayAttendance').textContent = '3';
        document.getElementById('pendingRequests').textContent = '0';
        document.getElementById('pendingCompOff').textContent = '0';

        // Load recent attendance
        const result = await AdminAPI.getAttendance();
        if (result.success) {
            const rows = result.data.slice(0, 5).map(row => `
                <tr>
                    <td>${row.employee_name || 'Unknown'}</td>
                    <td>${formatDate(row.date)}</td>
                    <td>${formatTime(row.check_in_time) || '—'}</td>
                    <td>${formatTime(row.check_out_time) || '—'}</td>
                    <td>${row.duration_minutes ? formatDuration(row.duration_minutes) : '—'}</td>
                    <td><span class="status-badge ${row.status || 'pending'}">${row.status || 'Pending'}</span></td>
                </tr>
            `).join('');
            
            document.getElementById('recentAttendanceTable').innerHTML = rows || '<tr><td colspan="6" class="text-center">No attendance records</td></tr>';
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

// Load employees
async function loadEmployees() {
    try {
        const result = await AdminAPI.getEmployees();
        
        if (result.success && result.data) {
            const rows = result.data.map(emp => `
                <tr>
                    <td>${emp.employee_name || emp.username}</td>
                    <td>${emp.username}</td>
                    <td>${emp.email || '—'}</td>
                    <td>${emp.department || 'General'}</td>
                    <td><span class="badge bg-${emp.role === 'admin' ? 'danger' : 'primary'}">${emp.role.toUpperCase()}</span></td>
                    <td>
                        <button class="btn btn-sm btn-warning" onclick="editEmployee(${emp.user_id})">Edit</button>
                        <button class="btn btn-sm btn-danger" onclick="deleteEmployee(${emp.user_id})">Delete</button>
                    </td>
                </tr>
            `).join('');
            
            document.getElementById('employeesTable').innerHTML = rows;
        }
    } catch (error) {
        console.error('Error loading employees:', error);
        showMessage('Failed to load employees', 'error');
    }
}

// Load attendance
async function loadAttendance() {
    try {
        const result = await AdminAPI.getAttendance();
        
        if (result.success && result.data) {
            const rows = result.data.map(row => `
                <tr>
                    <td>${row.employee_name || 'Unknown'}</td>
                    <td>${formatDate(row.date)}</td>
                    <td>${formatTime(row.check_in_time) || '—'}</td>
                    <td>${formatTime(row.check_out_time) || '—'}</td>
                    <td>${row.duration_minutes ? formatDuration(row.duration_minutes) : '—'}</td>
                    <td><span class="status-badge ${row.status || 'pending'}">${row.status || 'Pending'}</span></td>
                </tr>
            `).join('');
            
            document.getElementById('attendanceTable').innerHTML = rows || '<tr><td colspan="6" class="text-center">No attendance records</td></tr>';
        }
    } catch (error) {
        console.error('Error loading attendance:', error);
        showMessage('Failed to load attendance', 'error');
    }
}

// Load leave requests
async function loadLeaveRequests() {
    try {
        const result = await AdminAPI.getLeaveManagement();
        
        if (result.success && result.data) {
            const rows = result.data.map(leave => `
                <tr>
                    <td>${leave.employee_name || 'Unknown'}</td>
                    <td>${leave.leave_type || 'Annual'}</td>
                    <td>${formatDate(leave.start_date)}</td>
                    <td>${formatDate(leave.end_date)}</td>
                    <td><span class="status-badge ${leave.status || 'pending'}">${leave.status || 'Pending'}</span></td>
                    <td>
                        ${leave.status === 'pending' ? `
                            <button class="btn btn-sm btn-success" onclick="approveLeave(${leave.leave_id})">Approve</button>
                            <button class="btn btn-sm btn-danger" onclick="rejectLeave(${leave.leave_id})">Reject</button>
                        ` : '—'}
                    </td>
                </tr>
            `).join('');
            
            document.getElementById('leaveTable').innerHTML = rows || '<tr><td colspan="6" class="text-center">No leave requests</td></tr>';
        }
    } catch (error) {
        console.error('Error loading leave requests:', error);
        showMessage('Failed to load leave requests', 'error');
    }
}

// Load comp-off requests
async function loadCompOffRequests() {
    try {
        const result = await AdminAPI.getCompOffRequests();
        
        if (result.success && result.data) {
            const rows = result.data.map(req => `
                <tr>
                    <td>${req.employee_name || 'Unknown'}</td>
                    <td>${formatDate(req.request_date)}</td>
                    <td>${req.reason || '—'}</td>
                    <td><span class="status-badge ${req.status || 'pending'}">${req.status || 'Pending'}</span></td>
                    <td>
                        ${req.status === 'pending' ? `
                            <button class="btn btn-sm btn-success" onclick="approveCompOff(${req.request_id})">Approve</button>
                            <button class="btn btn-sm btn-danger" onclick="rejectCompOff(${req.request_id})">Reject</button>
                        ` : '—'}
                    </td>
                </tr>
            `).join('');
            
            document.getElementById('compoffTable').innerHTML = rows || '<tr><td colspan="5" class="text-center">No comp-off requests</td></tr>';
        }
    } catch (error) {
        console.error('Error loading comp-off requests:', error);
        showMessage('Failed to load comp-off requests', 'error');
    }
}

// Load holidays
async function loadHolidays() {
    try {
        const result = await AdminAPI.getHolidays();
        
        if (result.success && result.data) {
            const rows = result.data.map(holiday => `
                <tr>
                    <td>${holiday.holiday_name}</td>
                    <td>${formatDate(holiday.holiday_date)}</td>
                    <td>${holiday.description || '—'}</td>
                    <td>
                        <button class="btn btn-sm btn-danger" onclick="deleteHoliday(${holiday.holiday_id})">Delete</button>
                    </td>
                </tr>
            `).join('');
            
            document.getElementById('holidaysTable').innerHTML = rows || '<tr><td colspan="4" class="text-center">No holidays</td></tr>';
        }
    } catch (error) {
        console.error('Error loading holidays:', error);
        showMessage('Failed to load holidays', 'error');
    }
}

// Save employee
async function saveEmployee() {
    const name = document.getElementById('empName').value;
    const username = document.getElementById('empUsername').value;
    const password = document.getElementById('empPassword').value;
    const email = document.getElementById('empEmail').value;

    if (!name || !username || !password) {
        showMessage('Please fill all required fields', 'warning');
        return;
    }

    try {
        const result = await AdminAPI.addEmployee(username, password, name, email, '', 'General', 'employee');
        
        if (result.success) {
            showMessage('Employee added successfully', 'success');
            document.getElementById('employeeForm').reset();
            bootstrap.Modal.getInstance(document.getElementById('employeeModal')).hide();
            await loadEmployees();
        } else {
            showMessage(result.error || 'Failed to add employee', 'error');
        }
    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    }
}

// Edit employee
async function editEmployee(userId) {
    showMessage('Edit feature coming soon', 'info');
}

// Delete employee
async function deleteEmployee(userId) {
    if (!confirm('Are you sure you want to delete this employee?')) return;

    try {
        const result = await AdminAPI.deleteEmployee(userId);
        
        if (result.success) {
            showMessage('Employee deleted successfully', 'success');
            await loadEmployees();
        } else {
            showMessage(result.error || 'Failed to delete employee', 'error');
        }
    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    }
}

// Approve leave
async function approveLeave(leaveId) {
    try {
        const result = await AdminAPI.reviewLeave(leaveId, 'approved', '');
        
        if (result.success) {
            showMessage('Leave approved', 'success');
            await loadLeaveRequests();
        } else {
            showMessage(result.error || 'Failed to approve leave', 'error');
        }
    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    }
}

// Reject leave
async function rejectLeave(leaveId) {
    try {
        const result = await AdminAPI.reviewLeave(leaveId, 'rejected', '');
        
        if (result.success) {
            showMessage('Leave rejected', 'success');
            await loadLeaveRequests();
        } else {
            showMessage(result.error || 'Failed to reject leave', 'error');
        }
    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    }
}

// Approve comp-off
async function approveCompOff(requestId) {
    try {
        const result = await AdminAPI.reviewCompOff(requestId, 'approved', '');
        
        if (result.success) {
            showMessage('Comp-off approved', 'success');
            await loadCompOffRequests();
        } else {
            showMessage(result.error || 'Failed to approve comp-off', 'error');
        }
    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    }
}

// Reject comp-off
async function rejectCompOff(requestId) {
    try {
        const result = await AdminAPI.reviewCompOff(requestId, 'rejected', '');
        
        if (result.success) {
            showMessage('Comp-off rejected', 'success');
            await loadCompOffRequests();
        } else {
            showMessage(result.error || 'Failed to reject comp-off', 'error');
        }
    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    }
}

// Save holiday
async function saveHoliday() {
    const name = document.getElementById('holName').value;
    const date = document.getElementById('holDate').value;
    const description = document.getElementById('holDescription').value;

    if (!name || !date) {
        showMessage('Please fill all required fields', 'warning');
        return;
    }

    try {
        const result = await AdminAPI.addHoliday(name, date, description);
        
        if (result.success) {
            showMessage('Holiday added successfully', 'success');
            document.getElementById('holidayForm').reset();
            bootstrap.Modal.getInstance(document.getElementById('holidayModal')).hide();
            await loadHolidays();
        } else {
            showMessage(result.error || 'Failed to add holiday', 'error');
        }
    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    }
}

// Delete holiday
async function deleteHoliday(holidayId) {
    if (!confirm('Are you sure you want to delete this holiday?')) return;

    try {
        const result = await AdminAPI.deleteHoliday(holidayId);
        
        if (result.success) {
            showMessage('Holiday deleted successfully', 'success');
            await loadHolidays();
        } else {
            showMessage(result.error || 'Failed to delete holiday', 'error');
        }
    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    }
}
