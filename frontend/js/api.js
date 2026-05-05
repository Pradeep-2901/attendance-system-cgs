/**
 * API Client for CGS Attendance System
 * Handles all communication with Flask backend
 */

const API_BASE = window.location.hostname.includes("netlify.app")
    ? "https://cgs-attendance-system.onrender.com"  // Production Render backend
    : "http://localhost:5000";  // Development

console.log(`[API] Base URL: ${API_BASE}`);

// API Request Handler with retry logic for cold starts
async function apiCall(endpoint, options = {}, retryCount = 0) {
    const maxRetries = options.retries !== undefined ? options.retries : 2;
    const url = `${API_BASE}${endpoint}`;
    
    const config = {
        ...options,
        credentials: "include",  // Essential for cookie-based auth
        headers: {
            ...options.headers,
        }
    };

    // Add Content-Type for JSON requests
    if (options.body && typeof options.body === "object" && !options.headers?.["Content-Type"]) {
        config.headers["Content-Type"] = "application/json";
        config.body = JSON.stringify(options.body);
    }

    try {
        console.log(`[API] ${options.method || "GET"} ${url} (retry ${retryCount}/${maxRetries})`);
        const response = await fetch(url, config);
        
        // Handle unauthorized (401) - redirect to login
        if (response.status === 401) {
            console.warn("[API] ⚠️ Unauthorized (401) - clearing session and redirecting to login");
            localStorage.clear();
            sessionStorage.clear();
            // Redirect to login page
            if (window.location.pathname !== "/index.html") {
                window.location.href = "/index.html";
            }
            return { success: false, error: "Unauthorized", status: 401 };
        }

        // Handle server errors with retry logic (503, 502)
        if ((response.status === 503 || response.status === 502) && retryCount < maxRetries) {
            console.warn(`[API] Server unavailable (${response.status}) - retrying in 2s...`);
            await new Promise(resolve => setTimeout(resolve, 2000));
            return apiCall(endpoint, options, retryCount + 1);
        }

        // Handle server errors
        if (!response.ok && response.status !== 403) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        // Parse response
        const contentType = response.headers.get("content-type");
        let data;
        
        if (contentType?.includes("application/json")) {
            data = await response.json();
        } else {
            data = await response.text();
        }

        if (!response.ok) {
            throw new Error(data?.message || data || "Unknown error");
        }

        console.log(`[API] ✅ Response:`, data);
        return { success: true, data, status: response.status };

    } catch (error) {
        console.error(`[API] ❌ Error:`, error);
        
        // Retry on network errors (cold start)
        if (retryCount < maxRetries && error.message.includes('Failed to fetch')) {
            console.warn(`[API] Network error - retrying in 2s...`);
            await new Promise(resolve => setTimeout(resolve, 2000));
            return apiCall(endpoint, options, retryCount + 1);
        }
        
        return { 
            success: false, 
            error: error.message,
            status: 0
        };
    }
}

// Authentication APIs
const AuthAPI = {
    login: async (username, password, role) => {
        const response = await apiCall("/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: { username, password, role },
            retries: 3  // More retries for login during cold start
        });
        return response;
    },

    logout: async () => {
        return apiCall("/logout", { method: "GET" });
    },

    getSession: async () => {
        return apiCall("/test_session", { method: "GET" });
    },

    checkHealth: async () => {
        return apiCall("/health", { method: "GET" });
    }
};

// Employee APIs
const EmployeeAPI = {
    getDashboard: async () => {
        return apiCall("/dashboard", { method: "GET" });
    },

    checkIn: async (latitude, longitude, photo, address) => {
        return apiCall("/checkin", {
            method: "POST",
            body: { latitude, longitude, photo, address }
        });
    },

    checkOut: async (latitude, longitude, photo, address) => {
        return apiCall("/checkout", {
            method: "POST",
            body: { latitude, longitude, photo, address }
        });
    },

    getAttendance: async () => {
        return apiCall("/view_attendance", { method: "GET" });
    },

    getAttendanceData: async (userId) => {
        return apiCall(`/admin/employee_attendance_data/${userId}`, { method: "GET" });
    },

    requestLeave: async (leaveType, startDate, endDate, reason) => {
        return apiCall("/request_leave", {
            method: "POST",
            body: { leave_type: leaveType, start_date: startDate, end_date: endDate, reason }
        });
    },

    getLeave: async () => {
        return apiCall("/myleave", { method: "GET" });
    },

    requestCompOff: async (reason, date) => {
        return apiCall("/request_compoff", {
            method: "POST",
            body: { reason, date }
        });
    },

    requestRemote: async (remoteAddress, startDate, reason) => {
        return apiCall("/request-remote/submit", {
            method: "POST",
            body: { remote_address: remoteAddress, start_date: startDate, reason }
        });
    },

    requestVisit: async (siteName, siteAddress, startDate, endDate, reason) => {
        return apiCall("/request-visit/submit", {
            method: "POST",
            body: { site_name: siteName, site_address: siteAddress, start_date: startDate, end_date: endDate, reason }
        });
    },

    requestGeofence: async (latitude, longitude, locationName, reason) => {
        return apiCall("/request_geofence", {
            method: "POST",
            body: { latitude, longitude, location_name: locationName, reason }
        });
    }
};

// Admin APIs
const AdminAPI = {
    getDashboard: async () => {
        return apiCall("/admin", { method: "GET" });
    },

    getEmployees: async () => {
        return apiCall("/admin/employees", { method: "GET" });
    },

    addEmployee: async (username, password, employeeName, email, phone, department, role) => {
        return apiCall("/admin/add_employee", {
            method: "POST",
            body: { username, password, employee_name: employeeName, email, phone, department, role }
        });
    },

    editEmployee: async (userId, username, employeeName, email, phone, department, role) => {
        return apiCall(`/admin/edit_employee/${userId}`, {
            method: "POST",
            body: { username, employee_name: employeeName, email, phone, department, role }
        });
    },

    deleteEmployee: async (userId) => {
        return apiCall(`/admin/delete_employee/${userId}`, { method: "POST" });
    },

    getAttendance: async () => {
        return apiCall("/admin/attendance", { method: "GET" });
    },

    getEmployeeReport: async (userId) => {
        return apiCall(`/admin/employee_report/${userId}`, { method: "GET" });
    },

    getCompOffRequests: async () => {
        return apiCall("/admin/compoff_requests", { method: "GET" });
    },

    reviewCompOff: async (requestId, status, remarks) => {
        return apiCall(`/admin/review_compoff/${requestId}`, {
            method: "POST",
            body: { status, remarks }
        });
    },

    creditCompOff: async (attendanceId) => {
        return apiCall(`/admin/credit_compoff/${attendanceId}`, { method: "POST" });
    },

    getCompOffReport: async () => {
        return apiCall("/admin/compoff_report", { method: "GET" });
    },

    getCompOffHistory: async (userId) => {
        return apiCall(`/admin/compoff_history/${userId}`, { method: "GET" });
    },

    getLeaveManagement: async () => {
        return apiCall("/admin/leave_management", { method: "GET" });
    },

    reviewLeave: async (leaveId, status, remarks) => {
        return apiCall(`/admin/review_leave/${leaveId}`, {
            method: "POST",
            body: { status, remarks }
        });
    },

    getHolidays: async () => {
        return apiCall("/admin/holidays", { method: "GET" });
    },

    addHoliday: async (holidayName, holidayDate, description) => {
        return apiCall("/admin/add_holiday", {
            method: "POST",
            body: { holiday_name: holidayName, holiday_date: holidayDate, description }
        });
    },

    deleteHoliday: async (holidayId) => {
        return apiCall(`/admin/delete_holiday/${holidayId}`, { method: "POST" });
    },

    getRemoteRequests: async () => {
        return apiCall("/admin/remote-requests", { method: "GET" });
    },

    reviewRemoteRequest: async (requestId, status, remarks) => {
        return apiCall(`/admin/remote-requests/update/${requestId}`, {
            method: "POST",
            body: { status, remarks }
        });
    },

    getVisitRequests: async () => {
        return apiCall("/admin/visit-requests", { method: "GET" });
    },

    reviewVisitRequest: async (requestId, status, remarks) => {
        return apiCall(`/admin/visit-requests/update/${requestId}`, {
            method: "POST",
            body: { status, remarks }
        });
    },

    getSites: async () => {
        return apiCall("/admin/sites", { method: "GET" });
    },

    addSite: async (siteName, siteAddress, latitude, longitude) => {
        return apiCall("/admin/sites/add", {
            method: "POST",
            body: { site_name: siteName, site_address: siteAddress, latitude, longitude }
        });
    },

    toggleSite: async (siteId) => {
        return apiCall(`/admin/sites/toggle/${siteId}`, { method: "POST" });
    },

    getGeofenceRequests: async () => {
        return apiCall("/admin/geofence_requests", { method: "GET" });
    },

    reviewGeofence: async (requestId, status, remarks) => {
        return apiCall(`/admin/review_geofence/${requestId}`, {
            method: "POST",
            body: { status, remarks }
        });
    },

    getSettings: async () => {
        return apiCall("/admin/settings", { method: "GET" });
    },

    updateSettings: async (settingName, settingValue) => {
        return apiCall("/admin/settings/update", {
            method: "POST",
            body: { setting_name: settingName, setting_value: settingValue }
        });
    }
};
