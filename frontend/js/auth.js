/**
 * Authentication Module
 * Handles login, logout, and session management
 */

const AUTH_KEY = "cgs_user";
const ROLE_KEY = "cgs_role";

// Get current user from localStorage
function getCurrentUser() {
    const user = localStorage.getItem(AUTH_KEY);
    return user ? JSON.parse(user) : null;
}

// Get current user role
function getCurrentRole() {
    return localStorage.getItem(ROLE_KEY);
}

// Check if user is logged in
function isLoggedIn() {
    return getCurrentUser() !== null;
}

// Check if user is admin
function isAdmin() {
    return getCurrentRole() === "admin";
}

// Check if user is employee
function isEmployee() {
    return getCurrentRole() === "employee";
}

// Login handler
async function handleLogin(e) {
    e.preventDefault();

    const role = document.getElementById("roleToggle")?.textContent?.toLowerCase().includes("admin") ? "admin" : "employee";
    const username = document.getElementById("username")?.value;
    const password = document.getElementById("password")?.value;

    if (!username || !password) {
        showMessage("Please enter username and password", "error");
        return;
    }

    try {
        const result = await AuthAPI.login(username, password, role);

        if (!result.success) {
            showMessage(result.error || "Login failed", "error");
            return;
        }

        // Get session data to confirm login
        const sessionResult = await AuthAPI.getSession();
        if (!sessionResult.success) {
            showMessage("Failed to establish session", "error");
            return;
        }

        const sessionData = sessionResult.data;
        
        // Store user info in localStorage
        const userInfo = {
            userId: sessionData.session?.user_id,
            username: sessionData.session?.username,
            employeeName: sessionData.session?.employee_name,
            role: sessionData.session?.role
        };

        localStorage.setItem(AUTH_KEY, JSON.stringify(userInfo));
        localStorage.setItem(ROLE_KEY, userInfo.role);

        showMessage(`Welcome ${userInfo.employeeName || username}!`, "success");

        // Redirect based on role
        setTimeout(() => {
            if (userInfo.role === "admin") {
                window.location.href = "/admin.html";
            } else {
                window.location.href = "/dashboard.html";
            }
        }, 500);

    } catch (error) {
        showMessage("Login error: " + error.message, "error");
    }
}

// Logout handler
async function handleLogout() {
    try {
        await AuthAPI.logout();
    } catch (error) {
        console.error("Logout error:", error);
    } finally {
        localStorage.removeItem(AUTH_KEY);
        localStorage.removeItem(ROLE_KEY);
        window.location.href = "/index.html";
    }
}

// Check authentication status
async function checkAuth() {
    const user = getCurrentUser();
    
    if (!user) {
        // Not logged in - redirect to login
        if (!window.location.pathname.includes("index.html")) {
            window.location.href = "/index.html";
        }
        return false;
    }

    // Verify session with backend
    const result = await AuthAPI.getSession();
    if (!result.success || result.status === 401) {
        // Session expired
        localStorage.clear();
        window.location.href = "/index.html";
        return false;
    }

    return true;
}

// Update UI with user info
function updateUserDisplay() {
    const user = getCurrentUser();
    if (!user) return;

    // Update navbar user display
    const userNameElements = document.querySelectorAll(".user-name, .username-display");
    userNameElements.forEach(el => {
        el.textContent = user.employeeName || user.username;
    });

    // Update user role badges
    const roleElements = document.querySelectorAll(".user-role");
    roleElements.forEach(el => {
        el.textContent = user.role.toUpperCase();
        el.className = `user-role badge bg-${user.role === 'admin' ? 'danger' : 'primary'}`;
    });
}

// Guard routes - redirect if not authenticated
async function requireAuth() {
    if (!await checkAuth()) {
        return false;
    }
    updateUserDisplay();
    return true;
}

// Guard admin routes
async function requireAdmin() {
    if (!await checkAuth()) {
        return false;
    }
    if (!isAdmin()) {
        showMessage("Access denied. Admin privileges required.", "error");
        window.location.href = "/dashboard.html";
        return false;
    }
    return true;
}

// Guard employee routes
async function requireEmployee() {
    if (!await checkAuth()) {
        return false;
    }
    if (!isEmployee()) {
        showMessage("Access denied. Employee login required.", "error");
        window.location.href = "/admin.html";
        return false;
    }
    return true;
}

// Show message toast
function showMessage(message, type = "info", duration = 3000) {
    const messageEl = document.getElementById("messageContainer");
    if (!messageEl) return;

    const toast = document.createElement("div");
    toast.className = `alert alert-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'info'} alert-dismissible fade show`;
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    messageEl.appendChild(toast);

    if (duration > 0) {
        setTimeout(() => toast.remove(), duration);
    }
}
