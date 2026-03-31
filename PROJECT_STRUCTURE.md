# CGS Attendance System - Complete Project Structure & File Documentation

## 📁 Complete Folder Structure

```
CGS/
├── 📄 Core Application Files
│   ├── app.py                           # Main Flask application
│   ├── requirements.txt                 # Python dependencies
│   ├── Procfile                         # Railway/Heroku deployment config
│   ├── .env                             # Environment variables
│   ├── .gitignore                       # Git ignore rules
│   └── .venv/                           # Virtual environment
│
├── 📊 Database Files
│   ├── attendance_system.db             # Main SQLite database
│   ├── attendance.db                    # Backup/old database
│   ├── database_schema/                 # SQL migration scripts
│   │   ├── database_cleanup_geofencing.sql
│   │   ├── database_migration_work_modes.sql
│   │   ├── geofencing_missing_tables.sql
│   │   └── unified_geofencing_schema.sql
│   └── setup_database.py                # Database setup script
│
├── 🔧 Setup & Configuration Scripts
│   ├── setup_sqlite_db.py               # SQLite database initialization
│   ├── add_missing_tables.py            # Create missing tables
│   └── fix_schema.py                    # Add missing columns
│
├── 🐛 Database Debugging & Fixing Scripts
│   ├── check_users_schema.py            # Verify users table structure
│   ├── check_users_data.py              # Inspect user data
│   ├── check_geofence_schema.py         # Verify geofence table
│   ├── check_leave_tables.py            # Check leave tables
│   ├── fix_compoff_table.py             # Fix comp-off table schema
│   ├── fix_employee_names.py            # Normalize employee names
│   ├── verify_schema.py                 # Complete schema verification
│   ├── reset_passwords.py               # Reset user passwords
│   ├── convert_mysql_to_sqlite.py       # MySQL to SQLite conversion
│   └── update_employee_names.py         # Update name format
│
├── 🧪 Testing Scripts
│   ├── full_system_test.py              # Comprehensive 38-test suite (100% PASS)
│   ├── test_db_queries.py               # Database query tests
│   ├── test_routes.py                   # Flask route tests
│   ├── test_routes_fixed_schema.py      # Route tests with fixed schema
│   └── test_sql_fixes.py                # SQL compatibility tests
│
├── 🎨 Frontend - Templates (25 HTML files)
│   ├── 📌 Main Pages
│   │   ├── index.html                   # Login/landing page
│   │   ├── 404.html                     # Error 404 page
│   │   └── setup_guide.html             # Setup instructions
│   │
│   ├── 👤 Employee Pages
│   │   ├── dashboard.html               # Employee main dashboard
│   │   ├── mark_attendance.html         # Check-in/Check-out interface
│   │   ├── view_attendance.html         # Attendance history
│   │   ├── employee_attendance.html     # Attendance records display
│   │   ├── employee_report.html         # Employee reports
│   │   ├── myleave.html                 # My leave records
│   │   ├── request_compoff.html         # Comp-off request form
│   │   ├── compoff_requests.html        # View comp-off requests
│   │   ├── request_remote.html          # Remote work request form
│   │   ├── request_visit.html           # Site visit request form
│   │   └── geofence_requests.html       # Geofence change requests
│   │
│   └── 🔐 Admin Pages
│       ├── admin_dashboard.html         # Admin main dashboard
│       ├── manage_employees.html        # Employee management
│       ├── add_employee.html            # Add new employee
│       ├── edit_employee.html           # Edit employee details
│       ├── leave_management.html        # Leave request approval
│       ├── holidays.html                # Holiday management
│       ├── compoff_report.html          # Comp-off report generation
│       ├── compoff_requests.html        # Admin comp-off approval
│       ├── admin_remote_requests.html   # Remote work approvals
│       ├── admin_visit_requests.html    # Site visit approvals
│       ├── admin_attendance.html        # Attendance overview
│       ├── admin_sites.html             # Work site management
│       ├── geofence_requests.html       # Geofence requests
│       ├── admin_settings.html          # System settings
│       └── admin_remote_requests.html   # Remote request management
│
├── 🎨 Frontend - Static Assets
│   ├── script.js                        # Custom JavaScript
│   ├── styles.css                       # Custom CSS
│   ├── css/
│   │   ├── bootstrap.min.css            # Bootstrap 5 framework
│   │   └── all.min.css                  # Font Awesome icons
│   ├── js/
│   │   └── bootstrap.bundle.min.js      # Bootstrap JavaScript
│   ├── images/
│   │   └── earth.jpg                    # Background image
│   ├── webfonts/                        # Font Awesome webfonts
│   ├── attendance_photos/               # Employee photo storage
│   └── (other asset directories)
│
└── 🔧 System Files
    ├── __pycache__/                     # Python compiled cache
    └── .venv/                           # Virtual environment
```

---

## 📋 Detailed File Explanations

### **Core Application Files**

| File | Purpose | Details |
|------|---------|---------|
| **app.py** | Main Flask application | 2700+ lines. Contains all routes for employee/admin dashboards, authentication, attendance, leave, comp-off, remote work, site visits, geofence management. Uses SQLite3, Werkzeug for security, Jinja2 templates. |
| **requirements.txt** | Python dependencies | Flask, Werkzeug, SQLite3, Flask-CORS, python-dotenv, Gunicorn (for production server) |
| **Procfile** | Deployment configuration | Specifies `web: gunicorn app:app` for Railway/Heroku deployment |
| **.env** | Environment variables | SECRET_KEY, DATABASE_URL, DEBUG settings (never commit) |
| **.gitignore** | Git ignore rules | Excludes .venv/, __pycache__/, *.pyc, .env, database*.db |
| **.venv/** | Virtual environment | Isolated Python environment with all dependencies |

---

### **Database Files**

| File | Purpose | Details |
|------|---------|---------|
| **attendance_system.db** | Main SQLite database | Contains 9 tables: users, attendance, leave_requests, compoff_requests, holidays, remote_work_requests, site_visits, geofence_requests, sites. 3 active employees (Pradeep, Sounthar, Aadhi). |
| **attendance.db** | Legacy database | Old backup, can be deleted |
| **database_schema/*.sql** | Migration scripts | Four SQL files for schema setup and migrations from MySQL |
| **setup_database.py** | Database initialization | Creates attendance_system.db and initializes schema |

---

### **Setup & Configuration Scripts**

| File | Purpose | Details |
|------|---------|---------|
| **setup_sqlite_db.py** | SQLite initialization | Creates tables and sample data on first run |
| **add_missing_tables.py** | Table creation | Adds holidays, remote_work_requests, site_visits, geofence_requests tables if missing |
| **fix_schema.py** | Schema fixes | Adds missing columns to users table for leave days tracking |

---

### **Database Debugging Scripts**

| File | Purpose | Details |
|------|---------|---------|
| **check_users_schema.py** | Schema inspection | Verifies users table has all required columns |
| **check_users_data.py** | Data inspection | Displays all user records in database |
| **check_geofence_schema.py** | Geofence verification | Checks geofence_requests table structure |
| **check_leave_tables.py** | Leave verification | Verifies leave_requests table schema |
| **fix_compoff_table.py** | Comp-off fix | Recreates compoff_requests table with correct schema (includes work_date column) |
| **fix_employee_names.py** | Name normalization | Updates NULL employee names to use username |
| **verify_schema.py** | Full verification | Comprehensive schema check for all tables |
| **reset_passwords.py** | Password reset | Resets user passwords in database |
| **convert_mysql_to_sqlite.py** | Database conversion | Converts MySQL queries to SQLite syntax |
| **update_employee_names.py** | Name cleanup | Final script that updated names to first names only and removed test user |

---

### **Testing Scripts**

| File | Test Coverage | Status |
|------|---|---|
| **full_system_test.py** | 38 comprehensive tests: 6 employee features + 10 admin features + 22 database integrity checks | ✅ **38/38 PASS (100%)** |
| **test_db_queries.py** | Database query validation | ✅ All queries tested |
| **test_routes.py** | Flask route endpoint testing | ✅ All routes return correct status |
| **test_routes_fixed_schema.py** | Routes with authenticated sessions | ✅ Routes with auth verified |
| **test_sql_fixes.py** | MySQL→SQLite conversion validation | ✅ All 7 tests pass |

---

### **Frontend - Templates (25 HTML Files)**

#### **Main Pages**
- **index.html** - Login screen with username/password
- **404.html** - Error page for invalid routes
- **setup_guide.html** - Initial setup instructions

#### **Employee Features** (11 pages)
- **dashboard.html** - Employee home with attendance stats
- **mark_attendance.html** - Check-in/Check-out buttons
- **view_attendance.html** - Attendance history with date filter
- **employee_attendance.html** - Attendance records table
- **employee_report.html** - Personal attendance reports
- **myleave.html** - My leave balance and history
- **request_compoff.html** - Submit comp-off request
- **compoff_requests.html** - View comp-off request status
- **request_remote.html** - Request remote work
- **request_visit.html** - Request site visit
- **geofence_requests.html** - Request geofence changes

#### **Admin Features** (13 pages)
- **admin_dashboard.html** - Admin overview with metrics
- **manage_employees.html** - List all employees (CRUD)
- **add_employee.html** - Add new employee form
- **edit_employee.html** - Edit employee details
- **leave_management.html** - Approve/Reject leave requests
- **holidays.html** - Manage holiday calendar
- **compoff_report.html** - Generate comp-off reports
- **compoff_requests.html** - Admin approve comp-off
- **admin_remote_requests.html** - Approve remote work
- **admin_visit_requests.html** - Approve site visits
- **admin_attendance.html** - Attendance overview
- **admin_sites.html** - Manage work sites with geofence
- **geofence_requests.html** - Approve geofence changes

---

### **Frontend - Static Assets**

#### **CSS Files**
- **bootstrap.min.css** - Bootstrap 5 CSS framework (responsive design)
- **all.min.css** - Font Awesome icons library
- **styles.css** - Custom CSS overrides

#### **JavaScript Files**
- **bootstrap.bundle.min.js** - Bootstrap 5 JavaScript (modals, dropdowns, etc.)
- **script.js** - Custom JavaScript for interactions

#### **Images & Fonts**
- **earth.jpg** - Background image for login page
- **webfonts/** - Font Awesome font files
- **attendance_photos/** - Folder for employee photos
- **images/** - General images folder

---

## 🎯 Project Architecture Overview

```
Frontend (Templates + Static Assets)
         ↓
    Flask Routes (app.py)
         ↓
   Authentication Decorators
         ↓
   Database Queries (SQLite3)
         ↓
   SQLite Database (attendance_system.db)
```

---

## 📊 Database Schema

**9 Tables**:

### 1. **users**
- Stores employee information
- Columns: user_id, username, password_hash, employee_name, email, designation, department, status, vacation_days_total, sick_days_total, vacation_days_taken, sick_days_taken

### 2. **attendance**
- Daily attendance records
- Columns: attendance_id, user_id, date, check_in_time, check_out_time, total_hours

### 3. **leave_requests**
- Leave applications from employees
- Columns: leave_id, user_id, leave_type, start_date, end_date, reason, status, reviewed_by, review_date

### 4. **compoff_requests**
- Compensatory off requests
- Columns: request_id, user_id, work_date, reason, status, request_date, review_date, reviewed_by

### 5. **holidays**
- Company holidays
- Columns: id, holiday_date, holiday_name

### 6. **remote_work_requests**
- Remote work approvals
- Columns: id, user_id, start_date, end_date, reason, status, requested_at, reviewed_by, review_date

### 7. **site_visits**
- Site visit tracking
- Columns: id, user_id, site_id, visit_date, purpose, status, requested_at

### 8. **geofence_requests**
- Location boundary change requests
- Columns: request_id, user_id, latitude, longitude, radius, reason, status, requested_at, reviewed_by, review_date

### 9. **sites**
- Approved work locations
- Columns: id, site_name, site_address, site_lat, site_lon, site_radius, site_description, is_active

---

## 🔄 Key Features & Routes

### **Employee Routes**
- `GET /` - Login page
- `POST /login` - Authentication
- `GET /dashboard` - Employee dashboard
- `GET /mark_attendance` - Attendance marking interface
- `POST /mark_attendance` - Record check-in/check-out
- `GET /view_attendance` - View attendance history
- `GET /leave_requests` - Manage leave requests
- `POST /request_leave` - Submit leave request
- `GET /compoff_requests` - View comp-off requests
- `POST /request_compoff` - Submit comp-off request
- `GET /request_remote` - Request remote work
- `GET /request_visit` - Request site visit
- `GET /geofence_requests` - Request geofence changes

### **Admin Routes**
- `GET /admin/dashboard` - Admin dashboard
- `GET /admin/employees` - Manage employees
- `GET /admin/add_employee` - Add employee form
- `POST /admin/add_employee` - Create employee
- `GET /admin/edit_employee/<id>` - Edit employee
- `POST /admin/edit_employee/<id>` - Update employee
- `GET /admin/leave_management` - Approve leave requests
- `POST /admin/approve_leave` - Approve/Reject leave
- `GET /admin/compoff-requests` - Comp-off approval
- `GET /admin/compoff-report` - Generate reports
- `GET /admin/remote-requests` - Remote work approval
- `GET /admin/visit-requests` - Site visit approval
- `GET /admin/geofence-requests` - Geofence approval
- `GET /admin/sites` - Manage work sites
- `GET /admin/settings` - System settings

---

## 🔐 Security Features

- **Password Hashing**: Werkzeug security for password storage
- **Session Management**: Secure Flask sessions with SECRET_KEY
- **Authentication Decorators**: `@employee_required` and `@admin_required` on protected routes
- **SQL Injection Prevention**: Parameterized queries with `?` placeholders
- **CORS Support**: Flask-CORS for cross-origin requests

---

## 🚀 Deployment Ready

- **Framework**: Flask 2.3.0+
- **Server**: Gunicorn WSGI server
- **Database**: SQLite3 (portable, no external dependencies)
- **Environment**: Python 3.8+
- **Platforms**: Railway, Heroku, AWS, Azure

---

## ✅ Project Status

| Component | Status | Notes |
|-----------|--------|-------|
| Code Quality | ✅ PASS | No syntax errors, 38/38 tests passing |
| Database | ✅ PASS | Complete schema, 3 active employees |
| Performance | ✅ PASS | Optimized queries, proper indexing |
| Security | ✅ PASS | Parameterized queries, authentication in place |
| Testing | ✅ PASS | 38/38 unit tests (100% success rate) |
| Deployment | ✅ READY | Production-ready with Gunicorn |

---

## 📂 Quick Start

1. **Activate Virtual Environment**:
   ```bash
   .venv\Scripts\Activate.ps1  # Windows
   source .venv/bin/activate    # Linux/Mac
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run Application**:
   ```bash
   python app.py
   ```

4. **Access Application**:
   - Navigate to `http://localhost:5000`
   - Login with credentials

5. **Run Tests**:
   ```bash
   python full_system_test.py
   ```

---

**Document Version**: 1.0  
**Last Updated**: March 31, 2026  
**Status**: ✅ Production Ready
