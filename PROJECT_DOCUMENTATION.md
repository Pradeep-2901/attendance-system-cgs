# CGS Attendance Management System - Complete Project Documentation

**Last Updated:** May 5, 2026  
**Project Status:** Production Ready  
**Environment:** Python 3.13 | Windows | Flask 3.0.0

---

## 📋 Table of Contents

1. [Technology Stack](#technology-stack)
2. [Project Files & Structure](#project-files--structure)
3. [Database Schema](#database-schema)
4. [API Routes & Endpoints](#api-routes--endpoints)
5. [Configuration & Setup](#configuration--setup)
6. [Key Features](#key-features)

---

## 🛠️ Technology Stack

### Backend
| Technology | Version | Purpose |
|-----------|---------|---------|
| **Python** | 3.13 | Core programming language |
| **Flask** | 3.0.0 | Web framework & routing |
| **SQLite3** | Native | Database (relational, file-based) |
| **Werkzeug** | 3.0.1 | Security utilities & password hashing |
| **Gunicorn** | 21.2.0 | Production WSGI application server |
| **Flask-CORS** | 4.0.0 | Cross-Origin Resource Sharing |
| **Flask-WTF** | 1.2.1 | CSRF Protection & form handling |
| **python-dotenv** | 1.0.1 | Environment variable management |
| **requests** | 2.31.0 | HTTP client for API calls (Geocoding) |

### Frontend
| Technology | Version | Purpose |
|-----------|---------|---------|
| **HTML5** | Latest | Semantic markup & structure |
| **CSS3** | Latest | Styling & responsive design |
| **Bootstrap** | 5.x | Responsive UI framework |
| **JavaScript** | ES6+ | Client-side logic & interactivity |
| **Font Awesome** | 6.x | Icon library for UI elements |
| **Jinja2** | Native | Server-side templating engine |

### Infrastructure & Deployment
| Component | Details |
|-----------|---------|
| **Server** | Gunicorn (production) / Flask dev server (development) |
| **Database** | SQLite3 (attendance_system.db) |
| **Deployment** | Railway / Heroku (via Procfile) |
| **Authentication** | Session-based (server-side sessions) |
| **Security** | Werkzeug password hashing (scrypt), HTTPS cookie flags, CSRF protection |
| **Geolocation APIs** | Google Maps Geocoding API (primary), OpenStreetMap Nominatim (fallback) |

---

## 📁 Project Files & Structure

### Core Application Files

```
CGS/
├── app.py                         # Main Flask application (2,776 lines)
├── requirements.txt               # Python dependencies list
├── Procfile                       # Deployment configuration (gunicorn app:app)
├── setup_sqlite_db.py            # Database initialization & demo user setup
├── cleanup_database.py            # Database maintenance utility
├── .env                          # Environment variables (SECRET_KEY, API keys)
├── .gitignore                    # Git exclusion rules
└── .venv/                        # Python virtual environment
```

### Database Files

```
CGS/
├── attendance_system.db          # Main SQLite database (production)
├── database_schema/
│   ├── database_cleanup_geofencing.sql
│   ├── database_migration_work_modes.sql
│   ├── geofencing_missing_tables.sql
│   └── unified_geofencing_schema.sql
└── setup_sqlite_db.py            # Database initialization script
```

### Frontend - HTML Templates (26 files)

#### Authentication
- `index.html` - Login page with Employee/Admin role toggle

#### Employee Pages (11 templates)
- `dashboard.html` - Main employee dashboard with quick stats
- `mark_attendance.html` - Check-in/Check-out interface with geolocation
- `view_attendance.html` - Attendance history and details
- `employee_attendance.html` - Attendance records table display
- `employee_report.html` - Personal attendance reports & analytics
- `myleave.html` - Leave balance and history
- `request_compoff.html` - Compensatory off request form
- `compoff_requests.html` - Comp-off request tracking
- `request_remote.html` - Remote work request form
- `request_visit.html` - Site visit request form
- `geofence_requests.html` - Geofence change requests

#### Admin Pages (14 templates)
- `admin_dashboard.html` - Admin overview with key metrics
- `manage_employees.html` - Employee management interface
- `add_employee.html` - Add new employee form
- `edit_employee.html` - Edit employee details form
- `leave_management.html` - Leave request approval interface
- `holidays.html` - Holiday calendar management
- `admin_attendance.html` - All-employee attendance overview
- `admin_sites.html` - Work site management
- `admin_remote_requests.html` - Remote work request approvals
- `admin_visit_requests.html` - Site visit request approvals
- `admin_settings.html` - System configuration settings
- `compoff_report.html` - Comp-off report generation
- `geofence_requests.html` - Geofence change request approvals
- `setup_guide.html` - System setup instructions

#### Error Pages
- `404.html` - 404 Not Found error page

### Frontend - Static Assets

```
CGS/static/
├── script.js                     # Custom JavaScript logic
├── styles.css                    # Custom CSS styles
├── css/
│   ├── bootstrap.min.css         # Bootstrap 5 compiled CSS
│   └── all.min.css               # Font Awesome icon styles
├── js/
│   └── bootstrap.bundle.min.js   # Bootstrap 5 JavaScript bundle
├── images/
│   └── earth.jpg                 # Background imagery
├── webfonts/                     # Font Awesome webfont files
├── attendance_photos/            # User check-in/check-out photos
└── (other asset directories)
```

---

## 🗄️ Database Schema

### Table Structure

#### 1. **users** Table
Primary table for user authentication and profile information.

```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,              -- Scrypt hashed password
    employee_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'employee',  -- 'employee' or 'admin'
    email TEXT,
    phone TEXT,
    department TEXT DEFAULT 'General',
    geofence_status TEXT DEFAULT 'none',
    compoff_balance INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### 2. **attendance** Table
Records daily attendance for each employee.

```sql
CREATE TABLE attendance (
    attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date DATE NOT NULL,
    check_in_time TIME,
    check_out_time TIME,
    check_in_photo TEXT,              -- Base64 encoded or file path
    check_out_photo TEXT,
    check_in_location TEXT,           -- Address from geocoding
    check_out_location TEXT,
    check_in_timestamp TIMESTAMP,
    check_out_timestamp TIMESTAMP,
    duration_minutes INTEGER,         -- Calculated work hours
    status TEXT DEFAULT 'pending',    -- 'pending', 'approved', 'rejected'
    geofence_status TEXT DEFAULT 'valid',  -- 'valid' or 'invalid'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, date)
)
```

#### 3. **leaves** Table
Leave requests management.

```sql
CREATE TABLE leaves (
    leave_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    leave_type TEXT NOT NULL,         -- 'Annual', 'Sick', 'Casual', etc.
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason TEXT,
    status TEXT DEFAULT 'pending',    -- 'pending', 'approved', 'rejected'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
```

#### 4. **geofence_requests** Table
Geofence location change requests.

```sql
CREATE TABLE geofence_requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    request_date DATE NOT NULL,
    latitude REAL,
    longitude REAL,
    location_name TEXT,
    reason TEXT,
    status TEXT DEFAULT 'pending',    -- 'pending', 'approved', 'rejected'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
```

#### 5. **compoff_requests** Table
Compensatory off requests.

```sql
CREATE TABLE compoff_requests (
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    request_date DATE NOT NULL,
    reason TEXT,
    status TEXT DEFAULT 'pending',    -- 'pending', 'approved', 'rejected'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
)
```

#### 6. **holidays** Table
Company holidays management.

```sql
CREATE TABLE holidays (
    holiday_id INTEGER PRIMARY KEY AUTOINCREMENT,
    holiday_name TEXT NOT NULL,
    holiday_date DATE NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

#### 7. **site_visits** Table
Employee site visit requests.

```sql
CREATE TABLE site_visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    site_name TEXT NOT NULL,
    site_address TEXT NOT NULL,
    site_latitude REAL NOT NULL,
    site_longitude REAL NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status TEXT DEFAULT 'Pending',    -- 'Pending', 'Approved', 'Rejected'
    approved_by INTEGER,
    approval_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (approved_by) REFERENCES users(user_id)
)
```

#### 8. **remote_requests** Table
Remote work requests.

```sql
CREATE TABLE remote_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    request_date DATE NOT NULL,
    remote_address TEXT,
    remote_latitude REAL,
    remote_longitude REAL,
    reason TEXT,
    status TEXT DEFAULT 'Pending',    -- 'Pending', 'Approved', 'Rejected'
    approved_by INTEGER,
    approval_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (approved_by) REFERENCES users(user_id)
)
```

#### 9. **company_settings** Table
System configuration settings.

```sql
CREATE TABLE company_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_name TEXT UNIQUE NOT NULL,
    setting_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

---

## 🔌 API Routes & Endpoints

### Authentication Routes

#### Login Route
- **Path:** `/login`
- **Method:** `POST`
- **Authentication:** None (public endpoint)
- **Parameters:**
  ```
  username: string (form data)
  password: string (form data)
  role: string (form data) - 'employee' or 'admin'
  ```
- **Response:** Redirects to dashboard or renders index.html with error
- **Description:** Validates credentials against users table with scrypt password hashing

#### Logout Route
- **Path:** `/logout`
- **Method:** `GET`
- **Authentication:** Session required
- **Response:** Clears session and redirects to home
- **Description:** Terminates user session

#### Home Route
- **Path:** `/`
- **Method:** `GET`
- **Response:** Renders index.html (login page)

---

### Debug & Health Check Routes

#### Session Test
- **Path:** `/test_session`
- **Method:** `GET`
- **Response:** JSON with current session data
- **Description:** Returns session user_id, username, role, employee_name

#### Health Check
- **Path:** `/health`
- **Method:** `GET`
- **Response:** JSON with database status and session state
- **Description:** Verifies database connection and application health

---

### Employee Routes

#### Dashboard
- **Path:** `/dashboard`
- **Method:** `GET`
- **Authentication:** Employee required
- **Response:** Renders dashboard.html
- **Description:** Main employee portal with attendance status and quick links

#### Mark Attendance
- **Path:** `/mark`
- **Method:** `GET`
- **Authentication:** Employee required
- **Response:** Renders mark_attendance.html
- **Description:** Check-in/Check-out interface with geolocation capture

#### Check-In Endpoint
- **Path:** `/checkin`
- **Method:** `POST`, `OPTIONS` (CORS preflight)
- **Authentication:** Employee required
- **Parameters:**
  ```json
  {
    "latitude": number,
    "longitude": number,
    "photo": string (base64 encoded),
    "address": string
  }
  ```
- **Response:** JSON with success/error status
- **Description:** Records employee check-in with location and photo

#### Check-Out Endpoint
- **Path:** `/checkout`
- **Method:** `POST`
- **Authentication:** Employee required
- **Parameters:**
  ```json
  {
    "latitude": number,
    "longitude": number,
    "photo": string (base64 encoded),
    "address": string
  }
  ```
- **Response:** JSON with success/error and duration calculation
- **Description:** Records employee check-out and calculates work duration

#### View Attendance
- **Path:** `/view_attendance`
- **Method:** `GET`
- **Authentication:** Employee required
- **Response:** Renders view_attendance.html
- **Description:** Displays employee's attendance history

#### Request Leave
- **Path:** `/request_leave`
- **Method:** `POST`
- **Authentication:** Employee required
- **Parameters:**
  ```
  leave_type: string ('Annual', 'Sick', 'Casual')
  start_date: date
  end_date: date
  reason: string
  ```
- **Response:** JSON with success/error
- **Description:** Submits leave request for admin approval

#### My Leave
- **Path:** `/myleave`
- **Method:** `GET`
- **Authentication:** Employee required
- **Response:** Renders myleave.html
- **Description:** Displays leave balance and history

#### My Leave Export
- **Path:** `/myleave/export`
- **Method:** `GET`
- **Authentication:** Employee required
- **Response:** Downloadable leave report
- **Description:** Exports leave data (CSV or PDF format)

#### Request Geofence
- **Path:** `/request_geofence`
- **Method:** `POST`
- **Authentication:** Employee required
- **Parameters:**
  ```json
  {
    "latitude": number,
    "longitude": number,
    "location_name": string,
    "reason": string
  }
  ```
- **Response:** JSON with success/error
- **Description:** Requests geofence location change

#### Request Comp-Off
- **Path:** `/request_compoff`
- **Method:** `GET`, `POST`
- **Authentication:** Employee required
- **Parameters (POST):**
  ```
  reason: string
  date: date
  ```
- **Response:** JSON or render form
- **Description:** Requests compensatory off day

#### Request Remote Work
- **Path:** `/request-remote`
- **Method:** `GET`
- **Authentication:** Employee required
- **Response:** Renders request_remote.html
- **Description:** Remote work request form

#### Submit Remote Request
- **Path:** `/request-remote/submit`
- **Method:** `POST`
- **Authentication:** Employee required
- **Parameters:**
  ```
  remote_address: string
  start_date: date
  reason: string
  ```
- **Response:** JSON with success/error
- **Description:** Submits remote work request

#### Request Site Visit
- **Path:** `/request-visit`
- **Method:** `GET`
- **Authentication:** Employee required
- **Response:** Renders request_visit.html
- **Description:** Site visit request form

#### Submit Visit Request
- **Path:** `/request-visit/submit`
- **Method:** `POST`
- **Authentication:** Employee required
- **Parameters:**
  ```
  site_name: string
  site_address: string
  start_date: date
  end_date: date
  reason: string
  ```
- **Response:** JSON with success/error
- **Description:** Submits site visit request for approval

---

### Admin Routes

#### Admin Dashboard
- **Path:** `/admin`
- **Method:** `GET`
- **Authentication:** Admin required
- **Response:** Renders admin_dashboard.html
- **Description:** Admin main dashboard with metrics and pending requests

#### Manage Employees
- **Path:** `/admin/employees`
- **Method:** `GET`
- **Authentication:** Admin required
- **Response:** Renders manage_employees.html
- **Description:** List all employees with management options

#### Add Employee
- **Path:** `/admin/add_employee`
- **Method:** `GET`, `POST`
- **Authentication:** Admin required
- **Parameters (POST):**
  ```
  username: string (unique)
  password: string
  employee_name: string
  email: string
  phone: string
  department: string
  role: string ('employee' or 'admin')
  ```
- **Response:** JSON or render form
- **Description:** Creates new employee account

#### Edit Employee
- **Path:** `/admin/edit_employee/<user_id>`
- **Method:** `GET`, `POST`
- **Authentication:** Admin required
- **Response:** JSON or render form
- **Description:** Updates employee details

#### Delete Employee
- **Path:** `/admin/delete_employee/<user_id>`
- **Method:** `POST`
- **Authentication:** Admin required
- **Response:** JSON with success/error
- **Description:** Deactivates/removes employee account

#### Admin Attendance Overview
- **Path:** `/admin/attendance`
- **Method:** `GET`
- **Authentication:** Admin required
- **Response:** Renders admin_attendance.html
- **Description:** Overview of all employees' attendance

#### Employee Report
- **Path:** `/admin/employee_report/<user_id>`
- **Method:** `GET`
- **Authentication:** Admin required
- **Response:** Renders employee report
- **Description:** Detailed attendance report for specific employee

#### Employee Attendance Data (JSON)
- **Path:** `/admin/employee_attendance_data/<user_id>`
- **Method:** `GET`
- **Authentication:** Admin required
- **Response:** JSON array of attendance records
- **Description:** Returns attendance data for charts/reports

#### Leave Management
- **Path:** `/admin/leave_management`
- **Method:** `GET`
- **Authentication:** Admin required
- **Response:** Renders leave_management.html
- **Description:** View and manage leave requests

#### Review Leave
- **Path:** `/admin/review_leave/<leave_id>`
- **Method:** `POST`
- **Authentication:** Admin required
- **Parameters:**
  ```
  status: string ('approved' or 'rejected')
  remarks: string (optional)
  ```
- **Response:** JSON with success/error
- **Description:** Approve or reject leave request

#### Holiday Management
- **Path:** `/admin/holidays`
- **Method:** `GET`
- **Authentication:** Admin required
- **Response:** Renders holidays.html
- **Description:** View and manage company holidays

#### Add Holiday
- **Path:** `/admin/add_holiday`
- **Method:** `POST`
- **Authentication:** Admin required
- **Parameters:**
  ```
  holiday_name: string
  holiday_date: date
  description: string
  ```
- **Response:** JSON with success/error
- **Description:** Adds company holiday

#### Delete Holiday
- **Path:** `/admin/delete_holiday/<holiday_id>`
- **Method:** `POST`
- **Authentication:** Admin required
- **Response:** JSON with success/error
- **Description:** Removes company holiday

#### Comp-Off Requests
- **Path:** `/admin/compoff_requests`
- **Method:** `GET`
- **Authentication:** Admin required
- **Response:** Renders compoff_requests.html
- **Description:** View pending comp-off requests

#### Review Comp-Off
- **Path:** `/admin/review_compoff/<request_id>`
- **Method:** `POST`
- **Authentication:** Admin required
- **Parameters:**
  ```
  status: string ('approved' or 'rejected')
  remarks: string
  ```
- **Response:** JSON with success/error
- **Description:** Approve or reject comp-off request

#### Credit Comp-Off
- **Path:** `/admin/credit_compoff/<attendance_id>`
- **Method:** `POST`
- **Authentication:** Admin required
- **Response:** JSON with success/error
- **Description:** Credit comp-off to employee balance

#### Comp-Off Report
- **Path:** `/admin/compoff_report`
- **Method:** `GET`
- **Authentication:** Admin required
- **Response:** Renders compoff_report.html
- **Description:** Generate comp-off usage reports

#### Comp-Off History
- **Path:** `/admin/compoff_history/<user_id>`
- **Method:** `GET`
- **Authentication:** Admin required
- **Response:** JSON with comp-off transaction history
- **Description:** Returns employee comp-off history

#### Remote Work Requests
- **Path:** `/admin/remote-requests`
- **Method:** `GET`
- **Authentication:** Admin required
- **Response:** Renders admin_remote_requests.html
- **Description:** View pending remote work requests

#### Review Remote Request
- **Path:** `/admin/remote-requests/update/<request_id>`
- **Method:** `POST`
- **Authentication:** Admin required
- **Parameters:**
  ```
  status: string ('Approved' or 'Rejected')
  remarks: string
  ```
- **Response:** JSON with success/error
- **Description:** Approve or reject remote work request

#### Site Visit Requests
- **Path:** `/admin/visit-requests`
- **Method:** `GET`
- **Authentication:** Admin required
- **Response:** Renders admin_visit_requests.html
- **Description:** View pending site visit requests

#### Review Site Visit
- **Path:** `/admin/visit-requests/update/<request_id>`
- **Method:** `POST`
- **Authentication:** Admin required
- **Parameters:**
  ```
  status: string ('Approved' or 'Rejected')
  remarks: string
  ```
- **Response:** JSON with success/error
- **Description:** Approve or reject site visit request

#### Site Management
- **Path:** `/admin/sites`
- **Method:** `GET`
- **Authentication:** Admin required
- **Response:** Renders admin_sites.html
- **Description:** View and manage work sites

#### Add Site
- **Path:** `/admin/sites/add`
- **Method:** `POST`
- **Authentication:** Admin required
- **Parameters:**
  ```
  site_name: string
  site_address: string
  latitude: number
  longitude: number
  ```
- **Response:** JSON with success/error
- **Description:** Adds new work site location

#### Toggle Site Status
- **Path:** `/admin/sites/toggle/<site_id>`
- **Method:** `POST`
- **Authentication:** Admin required
- **Response:** JSON with success/error
- **Description:** Enable/disable work site

#### Geofence Requests
- **Path:** `/admin/geofence_requests`
- **Method:** `GET`
- **Authentication:** Admin required
- **Response:** Renders geofence_requests.html
- **Description:** View geofence change requests

#### Review Geofence
- **Path:** `/admin/review_geofence/<request_id>`
- **Method:** `POST`
- **Authentication:** Admin required
- **Parameters:**
  ```
  status: string ('approved' or 'rejected')
  remarks: string
  ```
- **Response:** JSON with success/error
- **Description:** Approve or reject geofence request

#### Admin Settings
- **Path:** `/admin/settings`
- **Method:** `GET`
- **Authentication:** Admin required
- **Response:** Renders admin_settings.html
- **Description:** System configuration interface

#### Update Settings
- **Path:** `/admin/settings/update`
- **Method:** `POST`
- **Authentication:** Admin required
- **Parameters:**
  ```
  setting_name: string
  setting_value: string
  ```
- **Response:** JSON with success/error
- **Description:** Updates system configuration

---

### Debug Endpoints

#### Debug Users
- **Path:** `/debug/users`
- **Method:** `GET`
- **Authentication:** Admin required
- **Response:** HTML table with all users
- **Description:** Shows all users in database for debugging

#### Test Login
- **Path:** `/debug/test-login`
- **Method:** `GET`
- **Authentication:** None
- **Response:** HTML form for testing login
- **Description:** Interactive login test interface

#### Debug Database
- **Path:** `/admin/debug-database`
- **Method:** `GET`
- **Authentication:** Admin required
- **Response:** HTML with database structure and stats
- **Description:** Database schema verification and statistics

#### Cleanup Geofencing
- **Path:** `/admin/cleanup-geofencing`
- **Method:** `GET`
- **Authentication:** Admin required
- **Response:** JSON with cleanup results
- **Description:** Removes geofencing tables and columns

#### Migrate Database
- **Path:** `/admin/migrate-database`
- **Method:** `GET`
- **Authentication:** Admin required
- **Response:** JSON with migration results
- **Description:** Runs database schema migrations

---

## ⚙️ Configuration & Setup

### Environment Variables (.env File)

```bash
# Flask Configuration
SECRET_KEY=demo-secret-key-railway
FLASK_ENV=production

# Database
DATABASE_URL=sqlite:///attendance_system.db

# Google Maps API (Optional)
GOOGLE_MAPS_API_KEY=YOUR_GOOGLE_MAPS_API_KEY_HERE

# Server Configuration
DEBUG=False
PORT=5000
HOST=0.0.0.0
```

### Flask Configuration (in app.py)

```python
# Core Flask Setup
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = "demo-secret-key-railway"
app.secret_key = "demo-secret-key-railway"

# Security Configuration
app.config['WTF_CSRF_ENABLED'] = False  # Demo mode
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# app.config['SESSION_COOKIE_SECURE'] = True  # Enable in production with HTTPS

# Database Path
DB_PATH = 'attendance_system.db'
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'attendance_photos')

# CORS Headers Configuration
@app.after_request
def after_request(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    # CORS headers for AJAX requests
    origin = request.headers.get('Origin')
    if origin:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken, X-Requested-With'
    return response
```

### Database Initialization (setup_sqlite_db.py)

```python
# Demo Users (auto-created)
DEMO_USERS = [
    {
        'username': 'francis',
        'password': 'francis123',
        'employee_name': 'Francis Johnson',
        'role': 'admin'
    },
    {
        'username': 'pradeep',
        'password': 'pradeep123',
        'employee_name': 'Pradeep Kumar',
        'role': 'employee'
    },
    {
        'username': 'sounthar',
        'password': 'sounthar123',
        'employee_name': 'Sounthar S',
        'role': 'employee'
    },
    {
        'username': 'aadhi',
        'password': 'aadhi123',
        'employee_name': 'Aadhi P',
        'role': 'employee'
    },
]
```

### Deployment Configuration (Procfile)

```
web: gunicorn app:app
```

### Requirements (requirements.txt)

```
Flask==3.0.0
python-dotenv==1.0.1
requests==2.31.0
Werkzeug==3.0.1
Flask-WTF==1.2.1
gunicorn==21.2.0
flask-cors==4.0.0
```

---

## 🎯 Key Features

### 1. Authentication & Authorization
- Role-based access control (Employee / Admin)
- Session-based authentication
- Password hashing with Werkzeug (scrypt algorithm)
- Login validation with credentials check

### 2. Attendance Management
- Check-in/Check-out with geolocation capture
- Photo verification during check-in/out
- Automatic location address resolution (Google Maps + OpenStreetMap)
- Work duration calculation
- Attendance history and reports

### 3. Leave Management
- Leave request submission (Annual, Sick, Casual)
- Admin approval/rejection workflow
- Leave balance tracking
- Leave export functionality

### 4. Compensatory Off (Comp-Off)
- Comp-off request submission
- Admin approval and crediting
- Comp-off balance tracking
- Comp-off usage reports
- Transaction history

### 5. Remote Work Management
- Remote work request submission
- Location and address capture
- Admin approval workflow
- Request tracking and history

### 6. Site Visit Management
- Site visit request submission
- Multi-day visit support
- Site management (add, enable, disable)
- Admin approval workflow

### 7. Geofencing & Location Services
- Location validation system
- Geofence request management
- Reverse geocoding (Google Maps + OpenStreetMap fallback)
- Location-based attendance tracking
- Demo mode (location validation bypassed)

### 8. Employee & Admin Management
- Create, read, update, delete employee accounts
- Department assignment
- Email and phone management
- Role assignment (Employee/Admin)
- Employee list and details management

### 9. Holiday Management
- Add company holidays
- Delete holidays
- Holiday calendar view
- Holiday-aware attendance calculations

### 10. Reporting & Analytics
- Attendance reports (individual and company-wide)
- Comp-off usage reports
- Attendance data export
- Employee-specific analytics

### 11. Admin Dashboard
- Key metrics display (total employees, today's attendance, pending requests)
- Recent attendance records
- Pending comp-off count
- Quick navigation to management sections

### 12. Security Features
- CSRF protection (configurable)
- Session security with HttpOnly and SameSite flags
- Password hashing with scrypt
- CORS configuration for cross-origin requests
- Admin-only route protection with decorators
- Employee-only route protection with decorators

---

## 📊 Database Statistics

- **Total Tables:** 9
- **Total Columns:** ~80 (across all tables)
- **Primary Key Type:** AUTOINCREMENT (auto-incrementing integers)
- **Foreign Keys:** User references in attendance, leaves, requests tables
- **Indexes:** On user_id, date, status fields for performance

---

## 🚀 Deployment Instructions

### Development Mode
```bash
python app.py
```

### Production Mode (Railway/Heroku)
```bash
gunicorn app:app
```

### Initial Setup
```bash
# 1. Create virtual environment
python -m venv .venv

# 2. Activate virtual environment
.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database
python setup_sqlite_db.py

# 5. Run application
python app.py
```

---

## 📝 Notes

- **Demo Mode:** Geofencing is disabled for demo deployments
- **CSRF Protection:** Currently disabled for demo; enable in production
- **SSL/TLS:** Configure SESSION_COOKIE_SECURE = True in production
- **API Keys:** Set Google Maps API key in .env for location services
- **Database:** SQLite3 is suitable for development; consider PostgreSQL for large-scale production

---

**End of Documentation**
