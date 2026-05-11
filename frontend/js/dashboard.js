/**
 * Employee Dashboard Logic
 */

let currentAttendanceData = {
    latitude: null,
    longitude: null,
    photo: null,
    address: null,
    isCheckIn: true
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async () => {
    console.log("[Dashboard] DOMContentLoaded - checking auth");
    
    if (!await requireEmployee()) return;
    
    console.log("[Dashboard] Auth check passed, verifying session with backend");
    
    // Critical: Verify backend session is available before loading data
    try {
        const sessionCheck = await AuthAPI.getSession();
        if (!sessionCheck.success) {
            console.error("[Dashboard] Backend session check failed:", sessionCheck);
            showMessage("Session verification failed. Redirecting to login...", "error");
            setTimeout(() => {
                window.location.href = "/";
            }, 1000);
            return;
        }
        console.log("[Dashboard] Backend session verified successfully");
    } catch (error) {
        console.error("[Dashboard] Session verification error:", error);
        showMessage("Session error. Redirecting to login...", "error");
        setTimeout(() => {
            window.location.href = "/";
        }, 1000);
        return;
    }
    
    updateUserDisplay();
    await loadDashboardData();
});

// Load dashboard data
async function loadDashboardData() {
    showLoading(document.querySelector('.container-lg'), true);

    try {
        const user = getCurrentUser();
        document.getElementById('welcomeMsg').textContent = `Welcome, ${user.employeeName || user.username}!`;

        // Get today's attendance
        const attendanceResult = await EmployeeAPI.getAttendanceData(user.userId);
        
        if (attendanceResult.success && attendanceResult.data) {
            const todayAttendance = attendanceResult.data[0];
            
            if (todayAttendance) {
                document.getElementById('todayStatus').textContent = 
                    todayAttendance.check_out_time ? '✓ Completed' : '🔄 In Progress';
                
                if (todayAttendance.check_in_time) {
                    document.getElementById('statusTime').textContent = 
                        `Checked in at ${formatTime(todayAttendance.check_in_time)}`;
                }

                if (todayAttendance.duration_minutes) {
                    document.getElementById('workHours').textContent = 
                        formatDuration(todayAttendance.duration_minutes);
                    document.getElementById('durationTime').textContent = 
                        `${todayAttendance.check_in_time} - ${todayAttendance.check_out_time || 'In progress'}`;
                }
            } else {
                document.getElementById('todayStatus').textContent = 'Not started';
                document.getElementById('statusTime').textContent = 'No check-in yet';
            }
        }

        // Get comp-off balance
        const sessionResult = await AuthAPI.getSession();
        if (sessionResult.success) {
            // In a real app, this would come from API response
            document.getElementById('compoffBalance').textContent = '0';
        }

    } catch (error) {
        console.error('Error loading dashboard:', error);
        showMessage('Failed to load dashboard data', 'error');
    } finally {
        showLoading(document.querySelector('.container-lg'), false);
    }
}

// Open check-in modal
function openCheckIn() {
    currentAttendanceData.isCheckIn = true;
    document.getElementById('modalTitle').textContent = 'Check In';
    document.getElementById('submitAttendanceBtn').textContent = 'Check In';
    document.getElementById('submitAttendanceBtn').className = 'btn btn-success';
    
    resetAttendanceModal();
    new bootstrap.Modal(document.getElementById('attendanceModal')).show();
}

// Open check-out modal
function openCheckOut() {
    currentAttendanceData.isCheckIn = false;
    document.getElementById('modalTitle').textContent = 'Check Out';
    document.getElementById('submitAttendanceBtn').textContent = 'Check Out';
    document.getElementById('submitAttendanceBtn').className = 'btn btn-danger';
    
    resetAttendanceModal();
    new bootstrap.Modal(document.getElementById('attendanceModal')).show();
}

// Capture photo and location
async function capturePhotoAndLocation() {
    const btn = event.target;
    btn.disabled = true;
    btn.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"><span class="visually-hidden">Loading...</span></div>';

    try {
        // Get location
        showMessage('Requesting location...', 'info', 2000);
        const location = await getLocation();
        currentAttendanceData.latitude = location.latitude;
        currentAttendanceData.longitude = location.longitude;

        document.getElementById('locationInfo').innerHTML = `
            <div class="alert alert-success">
                <strong>Location Captured:</strong><br>
                Latitude: ${location.latitude.toFixed(6)}<br>
                Longitude: ${location.longitude.toFixed(6)}<br>
                Accuracy: ±${Math.round(location.accuracy)} meters
            </div>
        `;

        // Capture photo
        showMessage('Requesting camera...', 'info', 2000);
        const photo = await capturePhoto();
        currentAttendanceData.photo = photo;

        document.getElementById('photoPreview').innerHTML = `
            <div class="alert alert-success">
                <strong>Photo Captured:</strong><br>
                <img src="${photo}" style="max-width: 100%; max-height: 200px; border-radius: 8px; margin-top: 10px;">
            </div>
        `;

        showMessage('Ready to submit', 'success', 2000);

    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
        console.error(error);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-camera"></i> Capture Photo & Location';
    }
}

// Submit attendance
async function submitAttendance() {
    if (!currentAttendanceData.photo || !currentAttendanceData.latitude) {
        showMessage('Please capture photo and location first', 'warning');
        return;
    }

    document.getElementById('attendanceForm').style.display = 'none';
    document.getElementById('attendanceLoading').style.display = 'block';

    try {
        let result;

        if (currentAttendanceData.isCheckIn) {
            result = await EmployeeAPI.checkIn(
                currentAttendanceData.latitude,
                currentAttendanceData.longitude,
                currentAttendanceData.photo,
                currentAttendanceData.address || `${currentAttendanceData.latitude}, ${currentAttendanceData.longitude}`
            );
        } else {
            result = await EmployeeAPI.checkOut(
                currentAttendanceData.latitude,
                currentAttendanceData.longitude,
                currentAttendanceData.photo,
                currentAttendanceData.address || `${currentAttendanceData.latitude}, ${currentAttendanceData.longitude}`
            );
        }

        if (result.success) {
            showMessage(currentAttendanceData.isCheckIn ? 'Checked in successfully!' : 'Checked out successfully!', 'success');
            
            setTimeout(() => {
                bootstrap.Modal.getInstance(document.getElementById('attendanceModal')).hide();
                loadDashboardData();
                resetAttendanceModal();
            }, 1500);
        } else {
            showMessage(result.error || 'Attendance failed', 'error');
        }

    } catch (error) {
        showMessage('Error: ' + error.message, 'error');
    } finally {
        document.getElementById('attendanceForm').style.display = 'block';
        document.getElementById('attendanceLoading').style.display = 'none';
    }
}

// Reset attendance modal
function resetAttendanceModal() {
    currentAttendanceData = {
        latitude: null,
        longitude: null,
        photo: null,
        address: null,
        isCheckIn: true
    };
    
    document.getElementById('photoPreview').innerHTML = '';
    document.getElementById('locationInfo').innerHTML = '';
    document.getElementById('attendanceMessageContainer').innerHTML = '';
}

// Open leave request modal
function openLeaveRequest() {
    // Placeholder - would open leave request form
    showMessage('Leave request feature coming soon', 'info');
}
