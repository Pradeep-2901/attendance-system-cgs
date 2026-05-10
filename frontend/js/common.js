/**
 * Common Utilities
 */

// Get geolocation
async function getLocation() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error("Geolocation not supported"));
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                resolve({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy
                });
            },
            (error) => {
                reject(new Error(`Geolocation error: ${error.message}`));
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
    });
}

// Capture photo from camera
async function capturePhoto() {
    return new Promise((resolve, reject) => {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = "image/*";
        input.capture = "environment";

        input.onchange = (e) => {
            const file = e.target.files[0];
            if (!file) {
                reject(new Error("No file selected"));
                return;
            }

            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = () => reject(new Error("Failed to read file"));
            reader.readAsDataURL(file);
        };

        input.click();
    });
}

// Format date
function formatDate(date) {
    if (!date) return "";
    if (typeof date === "string") date = new Date(date);
    return date.toISOString().split("T")[0];
}

// Format time
function formatTime(time) {
    if (!time) return "";
    if (typeof time === "string") {
        const [hours, minutes] = time.split(":");
        return `${hours}:${minutes}`;
    }
    return time.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
}

// Format datetime
function formatDateTime(datetime) {
    if (!datetime) return "";
    if (typeof datetime === "string") datetime = new Date(datetime);
    return datetime.toLocaleString();
}

// Calculate duration in minutes
function calculateDuration(checkIn, checkOut) {
    if (!checkIn || !checkOut) return 0;
    
    const start = new Date(`2024-01-01 ${checkIn}`);
    const end = new Date(`2024-01-01 ${checkOut}`);
    
    return Math.round((end - start) / (1000 * 60));
}

// Format duration
function formatDuration(minutes) {
    if (!minutes) return "0h 0m";
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return `${hours}h ${mins}m`;
}

// Create table from data
function createTable(data, columns) {
    if (!data || data.length === 0) {
        return "<p>No data available</p>";
    }

    let html = '<table class="table table-striped table-hover">';
    html += '<thead class="table-dark"><tr>';
    
    columns.forEach(col => {
        html += `<th>${col.label}</th>`;
    });
    
    html += '</tr></thead><tbody>';

    data.forEach(row => {
        html += '<tr>';
        columns.forEach(col => {
            let value = row[col.key];
            
            if (col.format) {
                value = col.format(value, row);
            }
            
            html += `<td>${value || "—"}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    return html;
}

// Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Loading spinner
function showLoading(container, show = true) {
    const spinner = container.querySelector(".spinner-border");
    if (show) {
        if (!spinner) {
            const div = document.createElement("div");
            div.className = "d-flex justify-content-center my-4";
            div.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
            container.appendChild(div);
        }
    } else {
        spinner?.parentElement?.remove();
    }
}

// Initialize tooltips (Bootstrap)
function initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipElements.forEach(el => {
        new bootstrap.Tooltip(el);
    });
}

// URL parameters
const urlParams = new URLSearchParams(window.location.search);

function getUrlParam(key) {
    return urlParams.get(key);
}

/**
 * Unified message display function
 * Supports error, success, warning, and info messages
 */
function showMessage(message, type = "info", duration = 3000) {
    console.log(`[Message] ${type.toUpperCase()}: ${message}`);
    
    // Remove any existing messages
    const existingMessages = document.querySelectorAll(".alert-notification");
    existingMessages.forEach(msg => msg.remove());
    
    // Create message element
    const alertDiv = document.createElement("div");
    alertDiv.className = `alert alert-notification alert-${type === "error" ? "danger" : type}`;
    alertDiv.setAttribute("role", "alert");
    alertDiv.textContent = message;
    
    // Add styling
    alertDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        max-width: 400px;
        padding: 12px 20px;
        border-radius: 4px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        animation: slideIn 0.3s ease-in-out;
    `;
    
    // Add to document
    document.body.appendChild(alertDiv);
    
    // Auto-remove after duration (skip if duration is 0)
    if (duration > 0) {
        setTimeout(() => {
            alertDiv.style.animation = "slideOut 0.3s ease-in-out";
            setTimeout(() => alertDiv.remove(), 300);
        }, duration);
    }
}

// Add animation styles if not already present
if (!document.querySelector("style[data-animations]")) {
    const style = document.createElement("style");
    style.setAttribute("data-animations", "true");
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOut {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(400px);
                opacity: 0;
            }
        }
    `;
    document.head.appendChild(style);
}
