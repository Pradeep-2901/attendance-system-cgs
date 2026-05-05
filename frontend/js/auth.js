/**
 * Authentication Utilities
 */

// Check if user is logged in
function isLoggedIn() {
  return !!localStorage.getItem("userId");
}

// Get current user info
function getCurrentUser() {
  return {
    userId: localStorage.getItem("userId"),
    username: localStorage.getItem("username"),
    role: localStorage.getItem("role"),
    employeeName: localStorage.getItem("employeeName")
  };
}

// Redirect to login if not authenticated
function requireAuth() {
  if (!isLoggedIn()) {
    console.log("[Auth] Not logged in, redirecting to login");
    window.location.href = "/";
  }
}

// Redirect to login if not admin
function requireAdmin() {
  const user = getCurrentUser();
  if (user.role !== "admin") {
    console.log("[Auth] Not admin, redirecting to login");
    window.location.href = "/";
  }
}

// Show error message to user
function showError(message) {
  console.error("[UI] Error:", message);
  
  // Remove any existing error messages
  const existingError = document.querySelector(".alert-error");
  if (existingError) {
    existingError.remove();
  }
  
  // Create and show new error message
  const errorDiv = document.createElement("div");
  errorDiv.className = "alert alert-error";
  errorDiv.textContent = message;
  
  const container = document.querySelector(".container") || document.body;
  container.insertBefore(errorDiv, container.firstChild);
  
  // Auto-hide after 5 seconds
  setTimeout(() => {
    errorDiv.remove();
  }, 5000);
}

// Show success message to user
function showSuccess(message) {
  console.log("[UI] Success:", message);
  
  // Remove any existing success messages
  const existingSuccess = document.querySelector(".alert-success");
  if (existingSuccess) {
    existingSuccess.remove();
  }
  
  // Create and show new success message
  const successDiv = document.createElement("div");
  successDiv.className = "alert alert-success";
  successDiv.textContent = message;
  
  const container = document.querySelector(".container") || document.body;
  container.insertBefore(successDiv, container.firstChild);
  
  // Auto-hide after 3 seconds
  setTimeout(() => {
    successDiv.remove();
  }, 3000);
}
