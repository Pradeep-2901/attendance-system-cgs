// API Configuration
const API_BASE = "https://attendance-system-cgs.onrender.com";

console.log("[API] Initializing API client with base URL:", API_BASE);

/**
 * Make API calls with proper error handling and retry logic
 */
async function apiCall(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const method = options.method || "GET";
  
  console.log(`[API] ${method} ${url}`);
  
  const defaultOptions = {
    method,
    credentials: "include", // Include cookies for session auth
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json"
    }
  };

  const fetchOptions = { ...defaultOptions, ...options };
  
  // Retry logic for network failures
  const maxRetries = 3;
  let lastError;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      console.log(`[API] Attempt ${attempt}/${maxRetries}`);
      
      const response = await fetch(url, fetchOptions);
      
      console.log(`[API] Response status: ${response.status}`);
      
      // Handle 502/503 (cold start)
      if ((response.status === 502 || response.status === 503) && attempt < maxRetries) {
        console.log(`[API] Got ${response.status}, waiting before retry...`);
        await new Promise(resolve => setTimeout(resolve, 2000));
        continue;
      }
      
      const data = await response.json();
      
      console.log(`[API] Response data:`, data);
      
      if (!response.ok && response.status === 401) {
        console.log("[API] Unauthorized (401) - redirecting to login");
        window.location.href = "/";
        return null;
      }
      
      return { success: response.ok, status: response.status, data };
      
    } catch (error) {
      lastError = error;
      console.error(`[API] Attempt ${attempt} failed:`, error.message);
      
      if (attempt < maxRetries) {
        console.log(`[API] Waiting 2s before retry...`);
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
  }
  
  // All retries failed
  console.error(`[API] All ${maxRetries} attempts failed:`, lastError);
  
  if (lastError.message === "Failed to fetch") {
    return {
      success: false,
      error: "Backend unreachable. Check API URL or backend status.",
      details: lastError.message
    };
  }
  
  return {
    success: false,
    error: lastError.message,
    details: lastError
  };
}

/**
 * User Authentication
 */
async function login(username, password, role) {
  console.log(`[API] Login attempt for user: ${username}, role: ${role}`);
  
  const result = await apiCall("/login", {
    method: "POST",
    body: JSON.stringify({ username, password, role })
  });
  
  if (!result.success) {
    console.error("[API] Login failed:", result.error);
    return { success: false, error: result.error || "Login failed" };
  }
  
  console.log("[API] Checking result.data.success:", result.data.success);
  console.log("[API] result.data keys:", Object.keys(result.data || {}));
  console.log("[API] Full result.data:", JSON.stringify(result.data));
  
  if (result.data.success) {
    console.log("[API] Login successful");
    console.log("[API] About to extract user_id:", result.data.user_id);
    console.log("[API] User data:", result.data);
    // Store user data in localStorage (backend returns at top level of result.data)
    localStorage.setItem("userId", result.data.user_id || username);
    localStorage.setItem("username", result.data.username || username);
    localStorage.setItem("role", result.data.role || role);
    localStorage.setItem("employeeName", result.data.employee_name || "");
    // Return success WITH the user data so handleLogin can access it
    const returnValue = { success: true, data: result.data, message: "Login successful" };
    console.log("[API] login() returning:", JSON.stringify(returnValue));
    return returnValue;
  }
  
  console.error("[API] Login returned false:", result.data);
  return { success: false, error: result.data.message || "Login failed" };
}

/**
 * Logout
 */
async function logout() {
  console.log("[API] Logout");
  localStorage.removeItem("userId");
  localStorage.removeItem("username");
  localStorage.removeItem("role");
  localStorage.removeItem("employeeName");
  window.location.href = "/";
}

/**
 * Check Authentication Status
 */
async function checkAuth() {
  console.log("[API] Checking auth status");
  const result = await apiCall("/dashboard");
  return result.success;
}

/**
 * Admin Routes
 */
async function getEmployees() {
  return apiCall("/api/admin/employees");
}

async function getAttendance() {
  return apiCall("/api/admin/attendance");
}

async function getSettings() {
  return apiCall("/api/admin/settings");
}

async function updateSettings(settingsData) {
  return apiCall("/api/admin/settings", {
    method: "PUT",
    body: JSON.stringify(settingsData)
  });
}

async function getSites() {
  return apiCall("/api/admin/sites");
}

async function createSite(siteData) {
  return apiCall("/api/admin/sites", {
    method: "POST",
    body: JSON.stringify(siteData)
  });
}

async function toggleSite(siteId) {
  return apiCall(`/api/admin/sites/${siteId}/toggle`, {
    method: "POST"
  });
}

async function getGeofenceRequests() {
  return apiCall("/api/admin/geofence-requests");
}

async function reviewGeofenceRequest(requestId, decision) {
  return apiCall(`/api/admin/geofence-requests/${requestId}`, {
    method: "POST",
    body: JSON.stringify({ decision })
  });
}

async function getVisitRequests() {
  return apiCall("/api/admin/visit-requests");
}

async function updateVisitRequest(requestId, action, notes = "") {
  return apiCall(`/api/admin/visit-requests/${requestId}`, {
    method: "POST",
    body: JSON.stringify({ action, admin_notes: notes })
  });
}

async function getRemoteRequests() {
  return apiCall("/api/admin/remote-requests");
}

async function updateRemoteRequest(requestId, action, notes = "") {
  return apiCall(`/api/admin/remote-requests/${requestId}`, {
    method: "POST",
    body: JSON.stringify({ action, review_notes: notes })
  });
}

async function getLeaveRequests() {
  return apiCall("/api/admin/leave-requests");
}

async function reviewLeaveRequest(leaveId, decision) {
  return apiCall(`/api/admin/leave-requests/${leaveId}`, {
    method: "POST",
    body: JSON.stringify({ decision })
  });
}

async function getHolidays(year) {
  return apiCall(`/api/admin/holidays?year=${year || new Date().getFullYear()}`);
}

async function createHoliday(holidayDate, holidayName) {
  return apiCall("/api/admin/holidays", {
    method: "POST",
    body: JSON.stringify({ holiday_date: holidayDate, holiday_name: holidayName })
  });
}

async function deleteHoliday(holidayId) {
  return apiCall(`/api/admin/holidays/${holidayId}`, {
    method: "DELETE"
  });
}

/**
 * Employee Routes
 */
async function getEmployeeVisitRequests() {
  return apiCall("/api/employee/visit-requests");
}

async function submitVisitRequest(siteId, visitDate, purpose) {
  return apiCall("/api/employee/visit-requests", {
    method: "POST",
    body: JSON.stringify({ site_id: siteId, visit_date: visitDate, purpose })
  });
}

async function getEmployeeRemoteRequests() {
  return apiCall("/api/employee/remote-requests");
}

async function submitRemoteRequest(startDate, endDate, address, lat, lon, reason) {
  return apiCall("/api/employee/remote-requests", {
    method: "POST",
    body: JSON.stringify({
      start_date: startDate,
      end_date: endDate,
      address,
      lat,
      lon,
      reason
    })
  });
}

/**
 * Attendance Routes
 */
async function checkIn(latitude, longitude, photoData = null) {
  return apiCall("/checkin", {
    method: "POST",
    body: JSON.stringify({
      latitude,
      longitude,
      photo_data: photoData
    })
  });
}

async function checkOut(latitude, longitude) {
  return apiCall("/checkout", {
    method: "POST",
    body: JSON.stringify({ latitude, longitude })
  });
}

/**
 * Additional Employee API Routes
 */
async function getAttendanceData(userId) {
  return apiCall(`/api/employee/attendance?user_id=${userId}`);
}

/**
 * API Namespace Objects (for cleaner code organization)
 */

// Admin API methods
const AdminAPI = {
  getEmployees,
  getAttendance,
  getSettings,
  updateSettings,
  getSites,
  createSite,
  toggleSite,
  getGeofenceRequests,
  reviewGeofenceRequest,
  getVisitRequests,
  updateVisitRequest,
  getRemoteRequests,
  updateRemoteRequest,
  getLeaveRequests,
  reviewLeaveRequest,
  getHolidays,
  createHoliday,
  deleteHoliday
};

// Employee API methods
const EmployeeAPI = {
  getAttendanceData,
  checkIn,
  checkOut,
  getEmployeeVisitRequests,
  submitVisitRequest,
  getEmployeeRemoteRequests,
  submitRemoteRequest
};

// Authentication API methods
const AuthAPI = {
  login,
  logout,
  checkAuth,
  async getSession() {
    console.log("[API] Getting session");
    return apiCall("/session");
  }
};
