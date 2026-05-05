from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
import os
from datetime import datetime, date, timedelta
import base64
import requests
import json
import math
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # ✅ Enable CORS for Railway deployment
app.config['SECRET_KEY'] = "demo-secret-key-railway"
app.secret_key = "demo-secret-key-railway"

# ✅ CSRF Protection Disabled for Demo
app.config['WTF_CSRF_ENABLED'] = False

# ✅ Security Configuration
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
# app.config['SESSION_COOKIE_SECURE'] = True  # ⚠️ Uncomment this line in production when using HTTPS

# ✅ Add CORS headers for AJAX requests
@app.after_request
def after_request(response):
    # Cache control for all responses
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    # CORS headers - Accept Netlify, localhost, and specific origins
    origin = request.headers.get('Origin')
    allowed_origins = [
        'https://cgs-attendance.netlify.app',
        'http://localhost:8000',
        'http://localhost:3000',
        'http://localhost:5000'
    ]
    
    if origin in allowed_origins or origin and 'netlify.app' in origin:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken, X-Requested-With, Accept, Authorization'
    
    return response

# ✅ SQLite Configuration (Demo Mode)
DB_PATH = 'attendance_system.db'

class DictRow(dict):
    """Wrapper to make sqlite3.Row objects behave like dictionaries with .get() support"""
    def __init__(self, cursor, row):
        self.keys_ = [description[0] for description in cursor.description]
        for k, v in zip(self.keys_, row):
            self[k] = v
    
    def get(self, key, default=None):
        """Dictionary-like get method"""
        return self.get(key, default) if key in self else default

def dict_factory(cursor, row):
    """Custom row factory that returns dict-like objects"""
    d = {}
    for idx, col in enumerate([c[0] for c in cursor.description]):
        d[col] = row[idx]
    return d

def get_db_connection():
    """Create SQLite database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = dict_factory  # Use dict factory instead of Row
    return conn

# ✅ Enable CSRF Protection (disabled via config)
csrf = CSRFProtect(app)

# ✅ Custom Jinja2 filter to handle timedelta objects
@app.template_filter('time_format')
def time_format(time_obj, format='%H:%M:%S'):
    """Format time objects (handles both datetime and timedelta)"""
    if time_obj is None:
        return 'N/A'
    
    if isinstance(time_obj, timedelta):
        # Convert timedelta to total seconds then to hours:minutes:seconds
        total_seconds = int(time_obj.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if format == '%H:%M':
            return f"{hours:02d}:{minutes:02d}"
        else:  # Default %H:%M:%S
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    elif hasattr(time_obj, 'strftime'):
        # Regular datetime object
        return time_obj.strftime(format)
    
    else:
        # Convert to string as fallback
        return str(time_obj)

@app.template_filter('date_format')
def date_format(date_obj, format='%Y-%m-%d'):
    """Format date objects"""
    if date_obj is None:
        return 'N/A'
    
    if hasattr(date_obj, 'strftime'):
        return date_obj.strftime(format)
    else:
        return str(date_obj)

# ✅ Correct folder to save photos
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'attendance_photos')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ✅ Admin login required decorator
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session.get('role') != 'admin':
            # Return JSON for API clients
            return jsonify({
                'success': False,
                'message': 'Unauthorized: Admin privileges required.'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

# ✅ Employee login required decorator
def employee_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Allow OPTIONS requests to pass through for CORS preflight
        if request.method == 'OPTIONS':
            return '', 200

        if 'role' not in session or session.get('role') not in ('employee', 'admin'):
            # Return JSON for API clients
            return jsonify({
                'success': False,
                'message': 'Unauthorized: Login required.'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

# ✅ General login required decorator (for any logged-in user)
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            # Return JSON for API clients
            return jsonify({
                'success': False,
                'message': 'Unauthorized: Login required.'
            }), 401
        return f(*args, **kwargs)
    return decorated_function

# ✅ High-Accuracy Reverse Geocoding Function (Google Maps + OSM Fallback)
def get_address_from_coords(lat, lon):
    """
    Reverse geocode coordinates to a precise street address.
    
    Primary: Google Maps Geocoding API (high accuracy)
    Fallback: OpenStreetMap Nominatim (if Google key not set or fails)
    
    Args:
        lat (float): Latitude coordinate
        lon (float): Longitude coordinate
    
    Returns:
        str: Formatted street address or coordinates if geocoding fails
    
    Configuration:
        Replace 'YOUR_GOOGLE_MAPS_API_KEY_HERE' with your actual Google Maps API key,
        or set environment variable: GOOGLE_MAPS_API_KEY
    """
    # IMPORTANT: Replace this with your actual Google Maps API key
    # You can also use: os.environ.get('GOOGLE_MAPS_API_KEY', 'YOUR_GOOGLE_MAPS_API_KEY_HERE')
    API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    
    # Fallback function using OpenStreetMap Nominatim
    def fallback_to_osm():
        """Fallback to OpenStreetMap if Google Maps fails or is not configured"""
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
            response = requests.get(url, timeout=5, headers={'User-Agent': 'AttendanceApp/1.0'})
            if response.status_code == 200:
                data = response.json()
                return data.get('display_name', f"Lat: {lat}, Lon: {lon}")
            else:
                print(f"[Geocoding][OSM] HTTP Error {response.status_code}")
        except requests.exceptions.Timeout:
            print("[Geocoding][OSM] Request timeout")
        except requests.exceptions.RequestException as e:
            print(f"[Geocoding][OSM] Network error: {e}")
        except Exception as e:
            print(f"[Geocoding][OSM] Unexpected error: {e}")
        return f"Lat: {lat}, Lon: {lon}"
    
    # Check if Google API key is configured
    if not API_KEY or API_KEY == "YOUR_GOOGLE_MAPS_API_KEY_HERE":
        print("[Geocoding] WARNING: Google Maps API key not configured. Falling back to OpenStreetMap.")
        print("[Geocoding] For better accuracy, set your Google Maps API key in the get_address_from_coords function.")
        return fallback_to_osm()
    
    # Try Google Maps Geocoding API first (for high accuracy)
    try:
        google_url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'latlng': f"{lat},{lon}",
            'key': API_KEY,
            'result_type': 'street_address|premise|subpremise|route|neighborhood',
            'language': 'en'
        }
        
        print(f"[Geocoding] Using Google Maps API for coordinates: {lat}, {lon}")
        
        response = requests.get(google_url, params=params, timeout=8)
        
        # Check HTTP status code
        if response.status_code != 200:
            print(f"[Geocoding][Google] HTTP Error {response.status_code}. Falling back to OSM.")
            return fallback_to_osm()
        
        data = response.json()
        api_status = data.get('status', 'UNKNOWN')
        
        # Handle different Google API response statuses
        if api_status == 'OK':
            results = data.get('results', [])
            if results and len(results) > 0:
                formatted_address = results[0].get('formatted_address', '')
                if formatted_address:
                    print(f"[Geocoding][Google] Success: {formatted_address}")
                    return formatted_address
                else:
                    print("[Geocoding][Google] No formatted_address in response")
            else:
                print("[Geocoding][Google] Empty results array")
        
        elif api_status == 'ZERO_RESULTS':
            print(f"[Geocoding][Google] No results found for coordinates. Falling back to OSM.")
        
        elif api_status == 'REQUEST_DENIED':
            error_msg = data.get('error_message', 'N/A')
            print(f"[Geocoding][Google] API request denied. Check your API key and billing.")
            print(f"[Geocoding][Google] Error message: {error_msg}")
        
        elif api_status == 'INVALID_REQUEST':
            print(f"[Geocoding][Google] Invalid request parameters")
        
        elif api_status == 'OVER_QUERY_LIMIT':
            print(f"[Geocoding][Google] API quota exceeded. Consider upgrading your plan.")
        
        else:
            print(f"[Geocoding][Google] Unexpected status: {api_status}")
        
        # If we reach here, Google API didn't provide a result - use fallback
        print("[Geocoding] Falling back to OpenStreetMap")
        return fallback_to_osm()
    
    except requests.exceptions.Timeout:
        print("[Geocoding][Google] Request timeout. Falling back to OSM.")
        return fallback_to_osm()
    
    except requests.exceptions.RequestException as e:
        print(f"[Geocoding][Google] Network error: {e}. Falling back to OSM.")
        return fallback_to_osm()
    
    except Exception as e:
        print(f"[Geocoding][Google] Unexpected error: {e}. Falling back to OSM.")
        return fallback_to_osm()

# ====================== UNIFIED GEOFENCING SYSTEM ======================
# Complete location validation system with hierarchical priority

def haversine(lat1, lon1, lat2, lon2):
    """Return distance in meters between two lat/lon pairs."""
    if None in (lat1, lon1, lat2, lon2):
        return None
    try:
        R = 6371000  # Earth radius meters
        phi1 = math.radians(float(lat1))
        phi2 = math.radians(float(lat2))
        dphi = math.radians(float(lat2) - float(lat1))
        dlambda = math.radians(float(lon2) - float(lon1))
        a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        return R * c
    except Exception:
        return None

# ====================== GOOGLE GEOCODING API ======================

def geocode_address(address):
    """
    Convert address to coordinates using Google Maps Geocoding API
    
    Returns: dict with 'lat', 'lon', 'formatted_address' or None if failed
    """
    # IMPORTANT: Replace with your actual Google Maps API key
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
    
    if not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY == "YOUR_GOOGLE_MAPS_API_KEY_HERE":
        print("⚠️ WARNING: Google Maps API key not configured!")
        return None
    
    try:
        import requests
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            'address': address,
            'key': GOOGLE_MAPS_API_KEY
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'OK' and data['results']:
                result = data['results'][0]
                location = result['geometry']['location']
                return {
                    'lat': float(location['lat']),
                    'lon': float(location['lng']),
                    'formatted_address': result['formatted_address']
                }
        
        print(f"Geocoding failed: {data.get('status', 'Unknown error')}")
        return None
        
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None

# ====================== UNIFIED VALIDATION SYSTEM ======================

def get_company_setting(cursor, setting_name):
    """Get a company setting value"""
    try:
        cursor.execute("SELECT setting_value FROM company_settings WHERE setting_name = ?",  (setting_name,))
        result = cursor.fetchone()
        return result['setting_value'] if result else None
    except Exception:
        return None

def validate_location_unified(cursor, user_id, current_lat, current_lon, check_date=None):
    """
    Demo Mode Geofencing - Always Validates Successfully
    Location validation bypassed for Railway demo deployment
    """
    return {
        'valid': True,
        'message': 'Location validated (demo mode)',
        'location_type': 'demo',
        'details': 'Geofencing disabled for demo'
    }


# ====================== DEBUG ENDPOINTS ======================

@app.route('/test_session')
def test_session():
    """Debug endpoint to check session state"""
    session_data = {
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'role': session.get('role'),
        'employee_name': session.get('employee_name'),
        'session_keys': list(session.keys())
    }
    return jsonify({
        'status': 'success',
        'session': session_data,
        'is_employee': session.get('role') == 'employee',
        'is_authenticated': 'user_id' in session
    })

@app.route('/health')
def health_check():
    """Health check endpoint for database and session"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'
    
    return jsonify({
        'status': 'ok',
        'database': db_status,
        'session_active': 'user_id' in session,
        'timestamp': datetime.now().isoformat()
    })

# ====================== BASIC ROUTES ======================

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    # Accept both JSON and form data
    if request.is_json:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        requested_role = data.get('role', 'employee')
        is_json_request = True
    else:
        username = request.form.get('username')
        password = request.form.get('password')
        requested_role = request.form.get('role', 'employee')
        is_json_request = False

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check credentials AND role match
        cursor.execute("SELECT * FROM users WHERE username = ? AND role = ?",  
                      (username, requested_role))
        user = cursor.fetchone()
        
        # Verify password (STRICT: Only hashed passwords allowed)
        if user and check_password_hash(user['password'], password):
            conn.close()
            
            # Set session with explicit values
            session.clear()
            session['user_id'] = str(user['user_id'])
            session['username'] = user['username']
            session['role'] = user['role']
            session['employee_name'] = user['employee_name'] if user['employee_name'] else user['username']
            session.permanent = True
            
            # Log successful login
            print(f"\n[LOGIN] User logged in: {user['username']} (Role: {user['role']}, ID: {user['user_id']})\n")

            # Return JSON for API requests, redirect for form submissions
            if is_json_request:
                return jsonify({
                    'success': True,
                    'user_id': user['user_id'],
                    'username': user['username'],
                    'role': user['role'],
                    'employee_name': user['employee_name'] or username
                })
            else:
                flash(f'Welcome {user["employee_name"] or username}!', 'success')
                if user['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('dashboard'))
        else:
            conn.close()
            # Return JSON for API requests, render template for form submissions
            if is_json_request:
                return jsonify({'success': False, 'message': f'Invalid {requested_role} credentials!'}), 401
            else:
                flash(f'Invalid {requested_role} credentials!', 'error')
                return render_template('index.html')
            
    except Exception as e:
        print(f"Login error: {e}")
        if is_json_request:
            return jsonify({'success': False, 'message': 'Login failed. Please try again.'}), 500
        else:
            flash('Login failed. Please try again.', 'error')
            return render_template('index.html')

@app.route('/logout')
def logout():
    username = session.get('username', 'User')
    session.clear()
    flash(f'Goodbye {username}!', 'success')
    return redirect(url_for('home'))

# ====================== ADMIN ROUTES ======================

@app.route('/admin')
@admin_required
def admin_dashboard():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role = 'employee'")
        total_employees = cursor.fetchone()['total']
        today = date.today()
        cursor.execute("SELECT COUNT(*) as today_attendance FROM attendance WHERE date = ?",  (today,))
        today_attendance = cursor.fetchone()['today_attendance']

        # Pending comp-off
        cursor.execute("SELECT COUNT(*) AS pending_compoff FROM compoff_requests WHERE status='Pending'")
        pending_compoff = cursor.fetchone()['pending_compoff']
        cursor.execute("""
            SELECT a.*, u.employee_name as employee_name 
            FROM attendance a 
            JOIN users u ON a.user_id = u.user_id 
            WHERE u.role = 'employee'
            ORDER BY a.date DESC, a.check_in_time DESC 
            LIMIT 5
        """)
        recent_attendance = cursor.fetchall()
        conn.close()
        
        # Return JSON for API clients
        return jsonify({
            'success': True,
            'data': {
                'username': session.get('username'),
                'total_employees': total_employees,
                'today_attendance': today_attendance,
                'recent_attendance': recent_attendance,
                'pending_compoff': pending_compoff
            }
        })
    except Exception as e:
        print(f"Admin dashboard error: {e}")
        return jsonify({
            'success': False,
            'message': f'Dashboard error: {str(e)}'
        }), 500

@app.route('/api/admin/employees', methods=['GET'])
@admin_required
def get_employees():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, username, employee_name as name, email, role, phone, department, created_at
            FROM users 
            WHERE role = 'employee' 
            ORDER BY user_id ASC
        """)
        employees = cursor.fetchall()
        conn.close()
        
        # Return JSON for API clients
        return jsonify({
            'success': True,
            'data': employees
        })
    except Exception as e:
        print(f"Get employees error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error loading employees: {str(e)}'
        }), 500

@app.route('/api/admin/employees', methods=['POST'])
@admin_required
def create_employee():
    """Create a new employee"""
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        name = data.get('name', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        work_mode = data.get('work_mode', 'Office')
        remote_address = data.get('remote_address', '').strip()
        
        if not name or not username or not password:
            return jsonify({'success': False, 'message': 'Name, username, and password are required!'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Username already exists! Please choose a different username.'}), 400
        
        # Generate next user_id
        cursor.execute("SELECT MAX(CAST(user_id AS UNSIGNED)) FROM users WHERE user_id REGEXP '^[0-9]+$'")
        result = cursor.fetchone()
        next_id = str((result[0] or 0) + 1)
        
        # Geocode remote address if provided
        remote_lat = remote_lon = None
        geocode_message = None
        if work_mode == 'Remote' and remote_address:
            geocode_result = geocode_address(remote_address)
            if geocode_result:
                remote_lat = geocode_result['lat']
                remote_lon = geocode_result['lon']
            else:
                geocode_message = 'Employee added, but unable to geocode remote address. Manual configuration needed.'
        
        # Insert new employee with geofencing support
        hashed_password = generate_password_hash(password)
        cursor.execute("""
            INSERT INTO users (user_id, employee_name, username, password, role, work_mode, 
                             remote_address, remote_lat, remote_lon) 
            VALUES (?, ?, ?, ?, 'employee', ?, ?, ?, ?)
        """, (next_id, name, username, hashed_password, work_mode, remote_address, remote_lat, remote_lon))
        
        conn.commit()
        conn.close()
        
        message = f'Employee {name} added successfully with ID: {next_id}!'
        if geocode_message:
            message += f' {geocode_message}'
        
        return jsonify({'success': True, 'message': message, 'employee_id': next_id}), 201
        
    except Exception as e:
        print(f"Create employee error: {e}")
        return jsonify({'success': False, 'message': f'Error adding employee: {str(e)}'}), 500

@app.route('/api/admin/employees/<user_id>', methods=['DELETE'])
@admin_required
def delete_employee(user_id):
    """Delete an employee"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get employee name before deletion
        cursor.execute("SELECT employee_name FROM users WHERE user_id = ? AND role = 'employee'", (user_id,))
        employee = cursor.fetchone()
        
        if not employee:
            conn.close()
            return jsonify({'success': False, 'message': 'Employee not found!'}), 404
        
        # Delete employee's attendance records first (foreign key constraint)
        cursor.execute("DELETE FROM attendance WHERE user_id = ?", (user_id,))
        
        # Delete employee
        cursor.execute("DELETE FROM users WHERE user_id = ? AND role = 'employee'", (user_id,))
        
        conn.commit()
        conn.close()
        
        employee_name = employee[0] if isinstance(employee, tuple) else employee.get('employee_name', 'Unknown')
        return jsonify({'success': True, 'message': f'Employee {employee_name} deleted successfully!'}), 200
        
    except Exception as e:
        print(f"Delete employee error: {e}")
        return jsonify({'success': False, 'message': f'Error deleting employee: {str(e)}'}), 500

@app.route('/api/admin/employees/<user_id>', methods=['GET'])
@admin_required
def get_employee_details(user_id):
    """Get employee details"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE user_id = ? AND role = 'employee'", (user_id,))
        employee = cursor.fetchone()
        conn.close()
        
        if not employee:
            return jsonify({'success': False, 'message': 'Employee not found!'}), 404
        
        # Convert dict-like row to dict
        if isinstance(employee, dict):
            employee_data = employee
        else:
            # If it's a tuple, we need to map it properly
            employee_data = {
                'user_id': employee[0],
                'employee_name': employee[1],
                'username': employee[2],
                'role': employee[3],
                'work_mode': employee[4],
                'remote_address': employee[5],
                'remote_lat': employee[6],
                'remote_lon': employee[7]
            }
        
        return jsonify({'success': True, 'data': employee_data}), 200
        
    except Exception as e:
        print(f"Get employee error: {e}")
        return jsonify({'success': False, 'message': f'Error fetching employee: {str(e)}'}), 500

@app.route('/api/admin/employees/<user_id>', methods=['PUT'])
@admin_required
def update_employee(user_id):
    """Update employee details"""
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        name = data.get('name', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        work_mode = data.get('work_mode', 'Office')
        remote_address = data.get('remote_address', '').strip()
        
        if not name or not username:
            return jsonify({'success': False, 'message': 'Name and username are required!'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if username exists for other users
        cursor.execute("SELECT user_id FROM users WHERE username = ? AND user_id != ?", (username, user_id))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Username already exists! Please choose a different username.'}), 400
        
        # Geocode remote address if provided
        remote_lat = remote_lon = None
        geocode_message = None
        if work_mode == 'Remote' and remote_address:
            geocode_result = geocode_address(remote_address)
            if geocode_result:
                remote_lat = geocode_result['lat']
                remote_lon = geocode_result['lon']
            else:
                geocode_message = 'Employee updated, but unable to geocode remote address. Manual configuration needed.'
        
        # Update employee
        if password:
            hashed_password = generate_password_hash(password)
            cursor.execute("""
                UPDATE users 
                SET employee_name = ?, username = ?, password = ?, work_mode = ?,
                    remote_address = ?, remote_lat = ?, remote_lon = ?
                WHERE user_id = ? AND role = 'employee'
            """, (name, username, hashed_password, work_mode, remote_address, remote_lat, remote_lon, user_id))
        else:
            cursor.execute("""
                UPDATE users 
                SET employee_name = ?, username = ?, work_mode = ?,
                    remote_address = ?, remote_lat = ?, remote_lon = ?
                WHERE user_id = ? AND role = 'employee'
            """, (name, username, work_mode, remote_address, remote_lat, remote_lon, user_id))
        
        conn.commit()
        conn.close()
        
        message = f'Employee {name} updated successfully!'
        if geocode_message:
            message += f' {geocode_message}'
        
        return jsonify({'success': True, 'message': message}), 200
        
    except Exception as e:
        print(f"Update employee error: {e}")
        return jsonify({'success': False, 'message': f'Error updating employee: {str(e)}'}), 500

@app.route('/api/admin/attendance', methods=['GET'])
@admin_required
def get_attendance():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all employees for dropdown
        cursor.execute("SELECT user_id, employee_name FROM users WHERE role = 'employee' ORDER BY employee_name")
        employees = cursor.fetchall()
        
        # Get selected employee and date range
        selected_employee = request.args.get('employee_id', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        # Build query
        query = """
            SELECT a.*, u.employee_name as employee_name 
            FROM attendance a 
            JOIN users u ON a.user_id = u.user_id 
            WHERE u.role = 'employee'
        """
        params = []
        
        if selected_employee:
            query += " AND a.user_id = ?"
            params.append(selected_employee)
        
        if start_date:
            query += " AND a.date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND a.date <= ?"
            params.append(end_date)
        
        query += " ORDER BY a.date DESC, a.check_in_time DESC LIMIT 100"
        
        cursor.execute(query, params)
        attendance_records = cursor.fetchall()
        
        # Calculate hours worked for each record
        for record in attendance_records:
            try:
                if record['check_in_time'] and record['check_out_time']:
                    checkin_dt = datetime.strptime(str(record['check_in_time']), "%H:%M:%S")
                    checkout_dt = datetime.strptime(str(record['check_out_time']), "%H:%M:%S")
                    time_diff = checkout_dt - checkin_dt
                    record['hours_worked'] = round(time_diff.total_seconds() / 3600, 1)
                else:
                    record['hours_worked'] = None
            except (ValueError, TypeError) as e:
                print(f"Error calculating hours for admin record: {e}")
                record['hours_worked'] = None
        
        conn.close()
        
        # Return JSON for API clients
        return jsonify({
            'success': True,
            'data': {
                'employees': employees,
                'attendance_records': attendance_records,
                'selected_employee': selected_employee,
                'start_date': start_date,
                'end_date': end_date
            }
        })
        
    except Exception as e:
        print(f"View attendance error: {e}")
        return jsonify({
            'success': False,
            'message': f'Error loading attendance: {str(e)}'
        }), 500

@app.route('/api/admin/employees/<user_id>/report', methods=['GET'])
@admin_required
def get_employee_report(user_id):
    """Get employee attendance report"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get employee details
        cursor.execute("SELECT * FROM users WHERE user_id = ? AND role = 'employee'", (user_id,))
        employee = cursor.fetchone()
        
        if not employee:
            conn.close()
            return jsonify({'success': False, 'message': 'Employee not found!'}), 404
        
        # Get attendance records for last 30 days
        cursor.execute("""
            SELECT * FROM attendance 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT 30
        """, (user_id,))
        attendance_records = cursor.fetchall()
        
        # Calculate hours worked for each record
        processed_records = []
        for record in attendance_records:
            try:
                record_dict = dict(record) if isinstance(record, dict) else {
                    'date': record[1],
                    'check_in_time': record[2],
                    'check_out_time': record[3],
                    'status': record[4]
                }
                
                if record_dict.get('check_in_time') and record_dict.get('check_out_time'):
                    checkin_dt = datetime.strptime(str(record_dict['check_in_time']), "%H:%M:%S")
                    checkout_dt = datetime.strptime(str(record_dict['check_out_time']), "%H:%M:%S")
                    time_diff = checkout_dt - checkin_dt
                    record_dict['hours_worked'] = round(time_diff.total_seconds() / 3600, 1)
                else:
                    record_dict['hours_worked'] = None
                
                processed_records.append(record_dict)
            except (ValueError, TypeError) as e:
                print(f"Error calculating hours for employee report: {e}")
                record_dict['hours_worked'] = None
                processed_records.append(record_dict)
        
        # Get monthly stats
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', date) as month,
                COUNT(*) as days_present,
                AVG(CAST(strftime('%H', check_in_time) AS INTEGER)) as avg_checkin_hour
            FROM attendance 
            WHERE user_id = ? AND check_in_time IS NOT NULL
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month DESC
            LIMIT 6
        """, (user_id,))
        monthly_stats = cursor.fetchall()
        
        # Prepare chart data
        months = [stat[0] for stat in monthly_stats] if monthly_stats else ['2025-08']
        attendance_counts = [stat[1] for stat in monthly_stats] if monthly_stats else [0]
        avg_checkin_hours = [float(stat[2]) if stat[2] else 9.0 for stat in monthly_stats] if monthly_stats else [9.0]
        
        chart_data = {
            'months': months,
            'attendance': attendance_counts,
            'avg_checkin_time': avg_checkin_hours
        }
        
        conn.close()
        
        employee_data = dict(employee) if isinstance(employee, dict) else {
            'user_id': employee[0],
            'employee_name': employee[1],
            'username': employee[2],
            'role': employee[3]
        }
        
        return jsonify({
            'success': True,
            'data': {
                'employee': employee_data,
                'attendance_records': processed_records,
                'chart_data': chart_data
            }
        }), 200
        
    except Exception as e:
        print(f"Employee report error: {e}")
        return jsonify({'success': False, 'message': f'Error generating report: {str(e)}'}), 500

@app.route('/api/admin/geofence-requests', methods=['GET'])
@admin_required
def get_geofence_requests():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT gr.request_id, gr.user_id, u.employee_name, u.username, gr.latitude, gr.longitude,
                   gr.request_date, gr.status
            FROM geofence_requests gr
            JOIN users u ON gr.user_id = u.user_id
            ORDER BY gr.request_date DESC
        """)
        requests_list = cursor.fetchall()
        conn.close()
        return render_template('geofence_requests.html', requests=requests_list, username=session['username'])
    except Exception as e:
        print(f"Admin geofence list error: {e}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/api/admin/geofence-requests/<int:request_id>', methods=['POST', 'PUT'])
@admin_required
def review_geofence_request(request_id):
    decision = request.form.get('decision')
    admin_id = session.get('user_id')
    if decision not in ('approve','reject'):
        flash('Invalid decision','error')
        return redirect(url_for('admin_geofence_requests'))
    try:
        conn = get_db_connection(); cursor = conn.cursor()
        cursor.execute("SELECT * FROM geofence_requests WHERE request_id = ?",  (request_id,))
        req = cursor.fetchone()
        if not req:
            conn.close(); flash('Request not found','error'); return redirect(url_for('admin_geofence_requests'))
        if req['status'] != 'pending':
            conn.close(); flash('Request already reviewed','error'); return redirect(url_for('admin_geofence_requests'))
        cursor2 = conn.cursor()
        if decision == 'approve':
            cursor2.execute("UPDATE geofence_requests SET status='approved', reviewed_by=?, review_date=datetime('now') WHERE request_id=?", (admin_id, request_id))
            cursor2.execute("UPDATE users SET geofence_status='approved', geofence_lat=?, geofence_lon=? WHERE user_id=?", (req['latitude'], req['longitude'], req['user_id']))
            flash('Geofence approved','success')
        else:
            cursor2.execute("UPDATE geofence_requests SET status='rejected', reviewed_by=?, review_date=datetime('now') WHERE request_id=?", (admin_id, request_id))
            cursor2.execute("UPDATE users SET geofence_status='rejected' WHERE user_id=%s", (req['user_id'],))
            flash('Geofence rejected','info')
        conn.commit(); conn.close()
        return redirect(url_for('admin_geofence_requests'))
    except Exception as e:
        print(f"Admin review geofence error: {e}")
        flash(f'Error: {str(e)}','error')
        return redirect(url_for('admin_geofence_requests'))

# ====================== ADMIN GEOFENCING ROUTES ======================

@app.route('/api/admin/settings', methods=['GET'])
@admin_required
def get_admin_settings():
    """Get company settings"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all company settings
        cursor.execute("SELECT * FROM company_settings ORDER BY setting_name")
        settings = cursor.fetchall()
        
        conn.close()
        return jsonify({'success': True, 'data': settings}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error loading settings: {str(e)}'}), 500

@app.route('/api/admin/settings', methods=['PUT', 'POST'])
@admin_required
def update_admin_settings():
    """Update company settings"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if request.is_json:
            data = request.get_json()
            office_address = data.get('office_address', '').strip()
            office_radius = data.get('office_radius', '200')
            geofencing_enabled = data.get('geofencing_enabled', False)
        else:
            office_address = request.form.get('office_address', '').strip()
            office_radius = request.form.get('office_radius', '200')
            geofencing_enabled = 'geofencing_enabled' in request.form
        
        # Update basic settings
        cursor.execute("""
            UPDATE company_settings 
            SET setting_value = ? 
            WHERE setting_name = 'office_address'
        """,  (office_address,))
        
        cursor.execute("""
            UPDATE company_settings 
            SET setting_value = ? 
            WHERE setting_name = 'office_radius'
        """,  (office_radius,))
        
        cursor.execute("""
            UPDATE company_settings 
            SET setting_value = ? 
            WHERE setting_name = 'geofencing_enabled'
        """,  ('true' if geofencing_enabled else 'false',))
        
        # Geocode office address if provided
        geocode_message = None
        if office_address:
            geocode_result = geocode_address(office_address)
            if geocode_result:
                cursor.execute("""
                    UPDATE company_settings 
                    SET setting_value = ? 
                    WHERE setting_name = 'office_lat'
                """,  (str(geocode_result['lat']),))
                
                cursor.execute("""
                    UPDATE company_settings 
                    SET setting_value = ? 
                    WHERE setting_name = 'office_lon'
                """,  (str(geocode_result['lon']),))
                
                geocode_message = f'Settings updated! Office coordinates: {geocode_result["lat"]:.6f}, {geocode_result["lon"]:.6f}'
            else:
                geocode_message = 'Settings updated, but unable to geocode office address. Please verify the address.'
        else:
            geocode_message = 'Settings updated successfully!'
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': geocode_message}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating settings: {str(e)}'}), 500

@app.route('/api/admin/sites', methods=['GET'])
@admin_required
def get_sites():
    """Get all sites"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id, s.site_name, s.site_address, s.site_lat, s.site_lon, s.site_radius, s.site_description, s.is_active,
                   COUNT(sv.id) as total_visits,
                   SUM(CASE WHEN sv.status = 'Pending' THEN 1 ELSE 0 END) as pending_visits
            FROM sites s
            LEFT JOIN site_visits sv ON s.id = sv.site_id
            GROUP BY s.id, s.site_name, s.site_address, s.site_lat, s.site_lon, s.site_radius, s.site_description, s.is_active
            ORDER BY s.site_name
        """)
        sites = cursor.fetchall()
        conn.close()
        
        sites_list = [dict(site) if isinstance(site, dict) else {
            'id': site[0],
            'site_name': site[1],
            'site_address': site[2],
            'site_lat': site[3],
            'site_lon': site[4],
            'site_radius': site[5],
            'site_description': site[6],
            'is_active': site[7],
            'total_visits': site[8],
            'pending_visits': site[9]
        } for site in sites]
        
        return jsonify({'success': True, 'data': sites_list}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error loading sites: {str(e)}'}), 500

@app.route('/api/admin/sites', methods=['POST'])
@admin_required
def create_site():
    """Create new site"""
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        site_name = data.get('site_name', '').strip()
        site_address = data.get('site_address', '').strip()
        site_radius = int(data.get('site_radius', 200))
        site_description = data.get('site_description', '').strip()
        
        if not site_name or not site_address:
            return jsonify({'success': False, 'message': 'Site name and address are required'}), 400
        
        # Geocode the address
        geocode_result = geocode_address(site_address)
        if not geocode_result:
            return jsonify({'success': False, 'message': 'Unable to geocode the address. Please verify and try again.'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sites (site_name, site_address, site_lat, site_lon, site_radius, site_description)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (site_name, site_address, geocode_result['lat'], geocode_result['lon'], site_radius, site_description))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Site "{site_name}" added successfully!'}), 201
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error adding site: {str(e)}'}), 500

@app.route('/api/admin/sites/<int:site_id>/toggle', methods=['POST'])
@admin_required
def toggle_site_status(site_id):
    """Toggle site active/inactive status"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT is_active FROM sites WHERE id = ?", (site_id,))
        site = cursor.fetchone()
        
        if not site:
            conn.close()
            return jsonify({'success': False, 'message': 'Site not found'}), 404
        
        current_status = site[0] if isinstance(site, tuple) else site.get('is_active')
        new_status = not current_status
        
        cursor.execute("UPDATE sites SET is_active = ? WHERE id = ?", (new_status, site_id))
        conn.commit()
        conn.close()
        
        status_text = "activated" if new_status else "deactivated"
        return jsonify({'success': True, 'message': f'Site {status_text} successfully!', 'new_status': new_status}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating site status: {str(e)}'}), 500

@app.route('/api/admin/visit-requests', methods=['GET'])
@admin_required
def get_visit_requests():
    """Get visit requests"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sv.*, s.site_name, s.site_address, u.employee_name as employee_name
            FROM site_visits sv
            JOIN sites s ON sv.site_id = s.id
            JOIN users u ON sv.user_id = u.user_id
            ORDER BY sv.requested_at DESC, sv.visit_date DESC
        """)
        visit_requests = cursor.fetchall()
        conn.close()
        
        requests_list = [dict(r) if isinstance(r, dict) else {
            'id': r[0],
            'user_id': r[1],
            'site_id': r[2],
            'visit_date': r[3],
            'status': r[4],
            'reason': r[5],
            'admin_notes': r[6],
            'approved_by': r[7],
            'approved_date': r[8],
            'requested_at': r[9],
            'site_name': r[10],
            'site_address': r[11],
            'employee_name': r[12]
        } for r in visit_requests]
        
        return jsonify({'success': True, 'data': requests_list}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error loading visit requests: {str(e)}'}), 500

@app.route('/api/admin/visit-requests/<int:request_id>', methods=['POST'])
@admin_required
def update_visit_request(request_id):
    """Approve or reject visit request"""
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        action = data.get('action')
        admin_notes = data.get('admin_notes', '').strip()
        
        if action not in ['approve', 'reject']:
            return jsonify({'success': False, 'message': 'Invalid action'}), 400
        
        new_status = 'Approved' if action == 'approve' else 'Rejected'
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE site_visits 
            SET status = ?, admin_notes = ?, approved_by = ?, approved_date = datetime('now')
            WHERE id = ?
        """, (new_status, admin_notes, session['user_id'], request_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Visit request {new_status.lower()} successfully!'}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating visit request: {str(e)}'}), 500

@app.route('/api/admin/remote-requests', methods=['GET'])
@admin_required
def get_remote_requests():
    """Get remote work requests"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, u.employee_name as employee_name
            FROM remote_work_requests r
            JOIN users u ON r.user_id = u.user_id
            ORDER BY r.start_date DESC, r.requested_at DESC
        """)
        remote_requests = cursor.fetchall()
        conn.close()
        
        requests_list = [dict(r) if isinstance(r, dict) else {
            'id': r[0],
            'user_id': r[1],
            'start_date': r[2],
            'end_date': r[3],
            'reason': r[4],
            'status': r[5],
            'review_notes': r[6],
            'reviewed_by': r[7],
            'reviewed_at': r[8],
            'requested_at': r[9],
            'employee_name': r[10]
        } for r in remote_requests]
        
        return jsonify({'success': True, 'data': requests_list}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error loading remote requests: {str(e)}'}), 500

@app.route('/api/admin/remote-requests/<int:request_id>', methods=['POST'])
@admin_required
def update_remote_request(request_id):
    """Approve or reject remote work request"""
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        action = data.get('action')
        review_notes = data.get('review_notes', '').strip()
        
        if action not in ['approve', 'reject']:
            return jsonify({'success': False, 'message': 'Invalid action'}), 400
        
        new_status = 'Approved' if action == 'approve' else 'Rejected'
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE remote_work_requests 
            SET status = ?, review_notes = ?, reviewed_by = ?, reviewed_at = datetime('now')
            WHERE id = ?
        """, (new_status, review_notes, session['user_id'], request_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Remote request {new_status.lower()} successfully!'}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error updating remote request: {str(e)}'}), 500

# ====================== EMPLOYEE GEOFENCING ROUTES ======================

@app.route('/api/employee/visit-requests', methods=['GET'])
@login_required
def get_employee_visit_requests():
    """Get employee's visit requests"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get active sites
        cursor.execute("SELECT * FROM sites WHERE is_active = 1 ORDER BY site_name")
        sites = cursor.fetchall()
        
        # Get user's pending/approved requests
        cursor.execute("""
            SELECT sv.*, s.site_name, s.site_address
            FROM site_visits sv
            JOIN sites s ON sv.site_id = s.id
            WHERE sv.user_id = ? 
            AND sv.visit_date >= date('now')
            ORDER BY sv.visit_date DESC
        """, (session['user_id'],))
        my_requests = cursor.fetchall()
        
        conn.close()
        
        sites_list = [dict(s) if isinstance(s, dict) else {
            'id': s[0],
            'site_name': s[1],
            'site_address': s[2],
            'site_lat': s[3],
            'site_lon': s[4],
            'site_radius': s[5],
            'site_description': s[6],
            'is_active': s[7]
        } for s in sites]
        
        requests_list = [dict(r) if isinstance(r, dict) else {
            'id': r[0],
            'user_id': r[1],
            'site_id': r[2],
            'visit_date': r[3],
            'status': r[4],
            'reason': r[5],
            'admin_notes': r[6],
            'approved_by': r[7],
            'approved_date': r[8],
            'requested_at': r[9],
            'site_name': r[10],
            'site_address': r[11]
        } for r in my_requests]
        
        return jsonify({'success': True, 'data': {'sites': sites_list, 'my_requests': requests_list}}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error loading visit requests: {str(e)}'}), 500

@app.route('/api/employee/visit-requests', methods=['POST'])
@login_required
def submit_visit_request():
    """Submit new visit request"""
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        site_id = data.get('site_id')
        visit_date = data.get('visit_date')
        purpose = data.get('purpose', '').strip()
        
        if not site_id or not visit_date or not purpose:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        # Validate date is not in the past
        try:
            visit_date_obj = datetime.strptime(visit_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        if visit_date_obj < date.today():
            return jsonify({'success': False, 'message': 'Visit date cannot be in the past'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check for existing request for same date
        cursor.execute("""
            SELECT id FROM site_visits 
            WHERE user_id = ? AND visit_date = ?
        """, (session['user_id'], visit_date))
        
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'You already have a visit request for this date'}), 400
        
        # Insert new request
        cursor.execute("""
            INSERT INTO site_visits (user_id, site_id, visit_date, purpose, status, requested_at)
            VALUES (?, ?, ?, ?, 'Pending', datetime('now'))
        """, (session['user_id'], site_id, visit_date, purpose))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Visit request submitted successfully! Awaiting admin approval.'}), 201
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error submitting visit request: {str(e)}'}), 500

@app.route('/api/employee/remote-requests', methods=['GET'])
@login_required
def get_employee_remote_requests():
    """Get employee's remote work requests"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM remote_work_requests 
            WHERE user_id = ? 
            AND end_date >= date('now')
            ORDER BY start_date DESC
        """, (session['user_id'],))
        requests_list = cursor.fetchall()
        
        conn.close()
        
        requests_data = [dict(r) if isinstance(r, dict) else {
            'id': r[0],
            'user_id': r[1],
            'start_date': r[2],
            'end_date': r[3],
            'address': r[4],
            'lat': r[5],
            'lon': r[6],
            'reason': r[7],
            'status': r[8],
            'review_notes': r[9],
            'reviewed_by': r[10],
            'reviewed_at': r[11],
            'requested_at': r[12]
        } for r in requests_list]
        
        return jsonify({'success': True, 'data': requests_data}), 200
        
    except Exception as e:
        print(f"[ERROR] get_employee_remote_requests failed: {e}")
        return jsonify({'success': False, 'message': f'Error loading remote requests: {str(e)}'}), 500

@app.route('/api/employee/remote-requests', methods=['POST'])
@login_required
def submit_remote_request():
    """Submit new remote work request"""
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        address = data.get('address', '').strip()
        lat = data.get('lat')
        lon = data.get('lon')
        reason = data.get('reason', '').strip()
        
        if not start_date or not end_date or not address or not lat or not lon or not reason:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        # Validate date format
        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        if start_date_obj < date.today():
            return jsonify({'success': False, 'message': 'Start date cannot be in the past'}), 400
            
        if end_date_obj < start_date_obj:
            return jsonify({'success': False, 'message': 'End date cannot be before start date'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check for overlapping requests
        cursor.execute("""
            SELECT id FROM remote_work_requests 
            WHERE user_id = ? 
            AND (
                (start_date <= ? AND end_date >= ?)
            )
        """, (session['user_id'], end_date, start_date))
        
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'You already have a remote work request overlapping with this period'}), 400
        
        # Insert new request
        cursor.execute("""
            INSERT INTO remote_work_requests (user_id, start_date, end_date, address, lat, lon, reason, status, requested_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending', datetime('now'))
        """, (session['user_id'], start_date, end_date, address, lat, lon, reason))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Remote work request submitted successfully! Awaiting admin approval.'}), 201
        
    except Exception as e:
        print(f"[ERROR] submit_remote_request failed: {e}")
        return jsonify({'success': False, 'message': f'Error submitting remote request: {str(e)}'}), 500
        
    except Exception as e:
        flash(f'Error submitting remote request: {str(e)}', 'error')
    
    return redirect(url_for('request_remote'))

# ====================== EMPLOYEE ROUTES ======================

@app.route('/dashboard')
@employee_required
def dashboard():
    user_id = session.get('user_id')
    today = date.today()
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM attendance WHERE user_id = ? AND date = ?",  (user_id, today))
        today_attendance = cursor.fetchone()
        cursor.execute("SELECT geofence_status, compoff_balance FROM users WHERE user_id = ?",  (user_id,))
        row = cursor.fetchone()
        geofence_status = row['geofence_status'] if row else 'none'
        compoff_balance = row.get('compoff_balance',0) if row else 0
        conn.close()
        
        # Return JSON for API clients
        return jsonify({
            'success': True,
            'data': {
                'username': session.get('username'),
                'employee_name': session.get('employee_name'),
                'today_attendance': today_attendance,
                'geofence_status': geofence_status,
                'compoff_balance': compoff_balance
            }
        })
    except Exception as e:
        print(f"Dashboard error: {e}")
        return jsonify({
            'success': False,
            'message': f'Dashboard error: {str(e)}'
        }), 500
        return redirect(url_for('home'))

@app.route('/mark')
@employee_required
def mark_attendance():
    user_id = session.get('user_id')
    today = date.today()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM attendance WHERE user_id = ? AND date = ?", 
            (user_id, today)
        )
        today_attendance = cursor.fetchone()
        conn.close()
        
        return render_template('mark_attendance.html',
                             username=session['username'],
                             employee_name=session['employee_name'],
                             today_attendance=today_attendance)
    except Exception as e:
        print(f"Mark attendance error: {e}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/checkin', methods=['POST', 'OPTIONS'])
@csrf.exempt
@employee_required
def checkin():
    """
    SIMPLIFIED CHECK-IN LOGIC (v2)
    - Returns 200 OK for ALL outcomes to prevent browser 'Network Error'
    - Uses 'status' field in JSON to indicate success/failure
    """
    print(f"\n[CHECKIN v2] Request received from {session.get('username')}")
    
    # Handle CORS Preflight
    if request.method == 'OPTIONS':
        print("[CHECKIN v2] Handling OPTIONS preflight")
        return jsonify({'status': 'ok'}), 200

    # 1. Safe Data Extraction
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Session expired. Please login again.'}), 200

        # Handle Data (JSON or FormData)
        if request.is_json:
            data = request.get_json()
            lat = data.get('latitude')
            lon = data.get('longitude')
            image_data = data.get('image')
            print(f"[CHECKIN v2] JSON Payload received")
        else:
            lat = request.form.get('latitude')
            lon = request.form.get('longitude')
            image_data = request.form.get('image')
            print(f"[CHECKIN v2] FormData Payload received")
        
        print(f"[CHECKIN v2] Data: Lat={lat}, Lon={lon}, Image={'Yes' if image_data else 'No'}")

        if not lat or not lon:
            return jsonify({'status': 'error', 'message': 'Location data missing.'}), 200
            
        try:
            latitude = float(lat)
            longitude = float(lon)
        except:
            return jsonify({'status': 'error', 'message': 'Invalid coordinates format.'}), 200

    except Exception as e:
        print(f"[CHECKIN v2] Input Error: {e}")
        return jsonify({'status': 'error', 'message': 'Invalid request data.'}), 200

    # 2. Database Operations
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        today = date.today()
        now = datetime.now()

        # Check existing
        cursor.execute("SELECT check_in_time FROM attendance WHERE user_id=? AND date=?",  (user_id, str(today)))
        existing = cursor.fetchone()
        if existing and existing[0]:
            return jsonify({'status': 'error', 'message': 'Already checked in today.'}), 200

        # Validate Location (Unified Logic)
        try:
            loc_valid = validate_location_unified(cursor, user_id, latitude, longitude, today)
            if not loc_valid['valid']:
                return jsonify({
                    'status': 'error', 
                    'message': loc_valid['message'],
                    'details': loc_valid.get('details')
                }), 200
        except Exception as loc_e:
            print(f"[CHECKIN v2] Location Validation Error: {loc_e}")
            return jsonify({'status': 'error', 'message': 'Location validation error. Contact admin.'}), 200

        # Save Image (DISABLED - Demo Mode)
        image_filename = None
        # Image saving is disabled in demo mode

        # Get Address
        address = "Unknown Location"
        try:
            address = get_address_from_coords(latitude, longitude)
        except:
            pass

        # Determine attendance type
        cursor.execute("SELECT 1 FROM compoff_requests WHERE user_id=? AND work_date=? AND status='Approved'",  (user_id, str(today)))
        is_compoff = cursor.fetchone()
        attendance_type = 'Comp-Off' if is_compoff else 'Regular'

        # Insert/Update DB (SQLite compatible)
        if existing:
            cursor.execute("""
                UPDATE attendance SET 
                check_in_time=?, check_in_latitude=?, check_in_longitude=?, 
                check_in_address=?, image_path_checkin=?, attendance_type=?
                WHERE user_id=? AND date=?
            """,  (str(now), latitude, longitude, address, image_filename, attendance_type, user_id, str(today)))
        else:
            cursor.execute("""
                INSERT INTO attendance 
                (user_id, date, check_in_time, check_in_latitude, check_in_longitude, 
                 check_in_address, image_path_checkin, attendance_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,  (user_id, str(today), str(now), latitude, longitude, address, image_filename, attendance_type))
        
        conn.commit()
        print(f"[CHECKIN v2] Success for {user_id}")
        
        return jsonify({
            'status': 'success', 
            'message': 'Check-in Successful!',
            'time': now.strftime('%H:%M:%S')
        }), 200

    except Exception as e:
        print(f"[CHECKIN v2] System Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'System Error: {str(e)}'}), 200
    
    finally:
        if conn:
            conn.close()

@app.route('/checkout', methods=['POST'])
@csrf.exempt
@employee_required
def checkout():
    """Handle employee check-out with photo and location"""
    user_id = session.get('user_id')
    today = date.today()
    now = datetime.now()
    
    print(f"\n[CHECKOUT] Starting check-out for user {user_id} at {now}")
    
    conn = None
    try:
        # Get database connection
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if checked in
        cursor.execute(
            "SELECT * FROM attendance WHERE user_id = ? AND date = ?",
            (user_id, str(today))
        )
        existing = cursor.fetchone()
        
        if not existing or not existing.get('check_in_time'):
            print(f"[CHECKOUT] User {user_id} not checked in")
            return jsonify({
                'status': 'error',
                'message': 'Please check-in first!'
            }), 400
        
        if existing.get('check_out_time'):
            print(f"[CHECKOUT] User {user_id} already checked out")
            return jsonify({
                'status': 'error',
                'message': 'Already checked out today!'
            }), 400
        
        # Get request data
        image_data = request.form.get('image', '')
        try:
            latitude = float(request.form.get('latitude', 0))
            longitude = float(request.form.get('longitude', 0))
        except (ValueError, TypeError):
            print(f"[CHECKOUT] Invalid coordinates")
            return jsonify({
                'status': 'error',
                'message': 'Invalid location data'
            }), 400
        
        print(f"[CHECKOUT] Location: {latitude}, {longitude}")
        
        # Validate location
        validation_result = validate_location_unified(cursor, user_id, latitude, longitude, today)
        
        if not validation_result['valid']:
            print(f"[CHECKOUT] Location validation failed: {validation_result['message']}")
            return jsonify({
                'status': 'error',
                'message': validation_result['message'],
                'location_type': validation_result.get('location_type'),
                'details': validation_result.get('details')
            }), 400
        
        print(f"[CHECKOUT] Location validated: {validation_result['message']}")
        
        # Save photo (DISABLED - Demo Mode)
        image_filename = None
        # Photo saving is disabled in demo mode
        
        # Get address
        address = get_address_from_coords(latitude, longitude)
        print(f"[CHECKOUT] Address: {address}")
        
        # Update database
        cursor.execute("""
            UPDATE attendance SET 
            check_out_time = ?, check_out_latitude = ?, check_out_longitude = ?,
            check_out_address = ?, image_path_checkout = ?
            WHERE user_id = ? AND date = ?
        """,  (str(now), latitude, longitude, address, image_filename, user_id, str(today)))
        
        conn.commit()
        print(f"[CHECKOUT] Database updated successfully")
        
        return jsonify({
            'status': 'success',
            'message': 'Check-out successful!',
            'time': now.strftime('%H:%M:%S'),
            'address': address
        }), 200
        
    except Exception as e:
        print(f"[CHECKOUT] ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'status': 'error',
            'message': f'Check-out failed: {str(e)}'
        }), 500
        
    finally:
        if conn:
            try:
                conn.close()
                print(f"[CHECKOUT] Connection closed")
            except:
                pass

@app.route('/view_attendance')
@employee_required
def view_attendance():
    user_id = session.get('user_id')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get attendance records
        cursor.execute("""
            SELECT * FROM attendance 
            WHERE user_id = ? 
            ORDER BY date DESC 
            LIMIT 30
        """,  (user_id,))
        attendance_records = cursor.fetchall()
        
        # Get monthly statistics for charts
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', date) as month,
                COUNT(*) as days_present
            FROM attendance 
            WHERE user_id = ? AND check_in_time IS NOT NULL
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month DESC
            LIMIT 6
        """,  (user_id,))
        monthly_stats = cursor.fetchall()
        
        # Get average check-in times
        cursor.execute("""
            SELECT 
                strftime('%Y-%m', date) as month,
                AVG(CAST(strftime('%H', check_in_time) AS INTEGER)) as avg_hour
            FROM attendance 
            WHERE user_id = ? AND check_in_time IS NOT NULL
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month DESC
            LIMIT 6
        """,  (user_id,))
        checkin_stats = cursor.fetchall()
        
        conn.close()
        
        # Calculate hours worked for each record
        for record in attendance_records:
            try:
                if record['check_in_time'] and record['check_out_time']:
                    checkin_dt = datetime.strptime(str(record['check_in_time']), "%H:%M:%S")
                    checkout_dt = datetime.strptime(str(record['check_out_time']), "%H:%M:%S")
                    time_diff = checkout_dt - checkin_dt
                    record['hours_worked'] = round(time_diff.total_seconds() / 3600, 1)
                else:
                    record['hours_worked'] = None
            except (ValueError, TypeError) as e:
                print(f"Error calculating hours for record: {e}")
                record['hours_worked'] = None
        
        # Prepare chart data
        months = [stat['month'] for stat in monthly_stats] if monthly_stats else ['2025-08', '2025-07', '2025-06']
        attendance_counts = [stat['days_present'] for stat in monthly_stats] if monthly_stats else [5, 8, 6]
        avg_checkin_hours = [float(stat['avg_hour']) if stat['avg_hour'] else 9.0 for stat in checkin_stats] if checkin_stats else [9.2, 9.1, 9.3]
        
        chart_data = {
            'months': months,
            'attendance': attendance_counts,
            'avg_checkin_time': avg_checkin_hours
        }
        
        return render_template('view_attendance.html',
                             username=session['username'],
                             employee_name=session['employee_name'],
                             attendance_records=attendance_records,
                             chart_data=chart_data)
    except Exception as e:
        print(f"View attendance error: {e}")
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/request_geofence', methods=['POST'])
@employee_required
def request_geofence():
    user_id = session.get('user_id')
    try:
        data = request.get_json() or request.form
        lat = data.get('latitude')
        lon = data.get('longitude')
        if lat is None or lon is None:
            flash('Geofence request failed: coordinates missing','error')
            return jsonify({'status': 'error', 'message': 'Latitude & longitude required'}), 400
        lat = float(lat); lon = float(lon)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT geofence_status FROM users WHERE user_id = ?",  (user_id,))
        row = cursor.fetchone()
        if not row:
            conn.close(); flash('Geofence request failed: user not found','error')
            return jsonify({'status': 'error', 'message': 'User not found'}), 404
        if row['geofence_status'] != 'none':
            conn.close(); flash('You have already submitted a geofence request','info')
            return jsonify({'status': 'error', 'message': 'Geofence already requested or decided'}), 400
        cursor2 = conn.cursor()
        cursor2.execute("""
            INSERT INTO geofence_requests (user_id, requested_lat, requested_lon)
            VALUES (%s, %s, %s)
        """, (user_id, lat, lon))
        cursor2.execute("UPDATE users SET geofence_status = 'pending' WHERE user_id = %s", (user_id,))
        conn.commit(); conn.close()
        flash('Geofence request submitted. Await admin approval.','success')
        return jsonify({'status': 'success', 'message': 'Geofence request submitted', 'new_status': 'pending'})
    except Exception as e:
        print(f"[ERROR] Geofence request: {e}")
        flash('Geofence request failed','error')
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ====================== EMPLOYEE LEAVE ROUTES ======================
@app.route('/myleave')
@employee_required
def myleave():
    """Employee self-service leave page: balances + history."""
    user_id = session.get('user_id')
    try:
        conn = get_db_connection(); cursor = conn.cursor()
        # Fetch balances
        cursor.execute("""
            SELECT vacation_days_total, sick_days_total,
                   vacation_days_taken, sick_days_taken
            FROM users WHERE user_id=?
        """,  (user_id,))
        balances = cursor.fetchone() or {}
        # Fetch history (latest 25)
        cursor.execute("""
            SELECT leave_id, leave_type, start_date, end_date, reason, status, created_at, reviewed_by, review_date
            FROM leave_requests WHERE user_id=?
            ORDER BY created_at DESC LIMIT 25
        """,  (user_id,))
        history = cursor.fetchall()
        conn.close()
        # Compute remaining
        vac_remaining = (balances.get('vacation_days_total',0) - balances.get('vacation_days_taken',0)) if balances else 0
        sick_remaining = (balances.get('sick_days_total',0) - balances.get('sick_days_taken',0)) if balances else 0

        # Status counters
        status_counts = {'Approved':0,'Rejected':0,'Pending':0}
        for r in history:
            if r['status'] in status_counts:
                status_counts[r['status']] += 1
        return render_template('myleave.html',
                               username=session['username'],
                               employee_name=session.get('employee_name'),
                               balances=balances,
                               vac_remaining=vac_remaining,
                               sick_remaining=sick_remaining,
                               history=history,
                               status_counts=status_counts)
    except Exception as e:
        print(f"MyLeave error: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Leave page error: {str(e)}','error')
        return redirect(url_for('dashboard'))

@app.route('/request_leave', methods=['POST'])
@employee_required
def request_leave():
    """Handle submission of a leave request with validation and balance checks."""
    user_id = session.get('user_id')
    leave_type = request.form.get('leave_type')
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')
    reason = (request.form.get('reason') or '').strip()

    # Basic presence validation
    if not leave_type or not start_date_str or not end_date_str or not reason:
        flash('All fields are required.','error')
        return redirect(url_for('myleave'))
    try:
        start_dt = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format.','error')
        return redirect(url_for('myleave'))

    if end_dt < start_dt:
        flash('End date cannot be before start date.','error')
        return redirect(url_for('myleave'))

    # Duration (inclusive days)
    days_requested = (end_dt - start_dt).days + 1
    if days_requested <= 0:
        flash('Invalid date range.','error')
        return redirect(url_for('myleave'))

    # Only allow current year for simplicity (optional business rule)
    if start_dt.year != end_dt.year:
        flash('Cross-year leave not supported in this version. Submit separate requests.','error')
        return redirect(url_for('myleave'))

    allowed_types = {'Vacation': 'vacation', 'Sick Leave': 'sick', 'Personal Day': 'vacation'}
    if leave_type not in allowed_types:
        flash('Invalid leave type.','error')
        return redirect(url_for('myleave'))

    try:
        conn = get_db_connection(); cursor = conn.cursor()
        cursor.execute("""
            SELECT vacation_days_total, sick_days_total,
                   vacation_days_taken, sick_days_taken
            FROM users WHERE user_id=?
        """,  (user_id,))
        balances = cursor.fetchone()
        if not balances:
            conn.close(); flash('User not found for leave.','error'); return redirect(url_for('myleave'))

        if leave_type in ('Vacation','Personal Day'):
            remaining = balances['vacation_days_total'] - balances['vacation_days_taken']
            if days_requested > remaining:
                conn.close(); flash(f'Insufficient vacation balance. You have {remaining} day(s) left.','error'); return redirect(url_for('myleave'))
        elif leave_type == 'Sick Leave':
            remaining = balances['sick_days_total'] - balances['sick_days_taken']
            if days_requested > remaining:
                conn.close(); flash(f'Insufficient sick leave balance. You have {remaining} day(s) left.','error'); return redirect(url_for('myleave'))

        # Overlap check: existing approved or pending requests (simple date range overlap)
        cursor.execute("""
            SELECT COUNT(*) AS cnt FROM leave_requests
            WHERE user_id=? AND status IN ('Pending','Approved')
              AND NOT (end_date < ? OR start_date > ?)
        """,  (user_id, start_dt, end_dt))
        overlap = cursor.fetchone()['cnt']
        if overlap:
            conn.close(); flash('You already have a pending/approved leave overlapping these dates.','error'); return redirect(url_for('myleave'))

        # Insert request
        cursor2 = conn.cursor()
        cursor2.execute("""
            INSERT INTO leave_requests (user_id, leave_type, start_date, end_date, reason)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, leave_type, start_dt, end_dt, reason))
        conn.commit(); conn.close()
        flash(f'Leave request submitted for {days_requested} day(s).','success')
        return redirect(url_for('myleave'))
    except Exception as e:
        print(f"Request leave error: {e}")
        flash('Failed to submit leave request.','error')
        return redirect(url_for('myleave'))

@app.route('/myleave/export')
@employee_required
def myleave_export():
    """Export full leave history as CSV."""
    import csv, io
    user_id = session.get('user_id')
    try:
        conn = get_db_connection(); cursor = conn.cursor()
        cursor.execute("""
            SELECT leave_id, leave_type, start_date, end_date, reason, status, request_date, reviewed_by, review_date
            FROM leave_requests WHERE user_id=? ORDER BY request_date DESC
        """,  (user_id,))
        rows = cursor.fetchall(); conn.close()
        output = io.StringIO(); writer = csv.writer(output)
        writer.writerow(['leave_id','leave_type','start_date','end_date','days','status','reason','request_date','reviewed_by','review_date'])
        for r in rows:
            days = (r['end_date'] - r['start_date']).days + 1 if r['start_date'] and r['end_date'] else ''
            writer.writerow([r['leave_id'], r['leave_type'], r['start_date'], r['end_date'], days, r['status'], r['reason'], r['request_date'], r['reviewed_by'], r['review_date']])
        from flask import make_response
        resp = make_response(output.getvalue())
        resp.headers['Content-Type'] = 'text/csv'
        resp.headers['Content-Disposition'] = f'attachment; filename=leave_history_{user_id}.csv'
        return resp
    except Exception as e:
        print(f"Leave export error: {e}")
        flash('Export failed','error')
        return redirect(url_for('myleave'))

# ====================== ADMIN LEAVE ROUTES ======================
@app.route('/api/admin/leave-requests', methods=['GET'])
@admin_required
def get_leave_requests():
    """Get pending leave requests"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT lr.leave_id, lr.user_id, u.employee_name, u.username, lr.leave_type,
                   lr.start_date, lr.end_date, lr.reason, lr.status, lr.created_at as request_date
            FROM leave_requests lr
            JOIN users u ON lr.user_id = u.user_id
            WHERE lr.status='Pending'
            ORDER BY lr.created_at ASC
        """)
        pending = cursor.fetchall()
        
        cursor.execute("SELECT COUNT(*) AS total_pending FROM leave_requests WHERE status='Pending'")
        stats = cursor.fetchone()
        conn.close()
        
        pending_list = [dict(req) if isinstance(req, dict) else {
            'leave_id': req[0],
            'user_id': req[1],
            'employee_name': req[2],
            'username': req[3],
            'leave_type': req[4],
            'start_date': req[5],
            'end_date': req[6],
            'reason': req[7],
            'status': req[8],
            'request_date': req[9]
        } for req in pending]
        
        return jsonify({
            'success': True,
            'data': {
                'pending_requests': pending_list,
                'stats': {'total_pending': stats[0] if isinstance(stats, tuple) else stats.get('total_pending', 0)}
            }
        }), 200
        
    except Exception as e:
        print(f"Get leave requests error: {e}")
        return jsonify({'success': False, 'message': f'Error loading leave requests: {str(e)}'}), 500

@app.route('/api/admin/leave-requests/<int:leave_id>', methods=['POST'])
@admin_required
def review_leave_request(leave_id):
    """Approve or reject a leave request"""
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        decision = data.get('decision')  # 'Approve' or 'Reject'
        if decision not in ('Approve', 'Reject'):
            return jsonify({'success': False, 'message': 'Invalid decision.'}), 400
        
        admin_id = session.get('user_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM leave_requests WHERE leave_id = ?", (leave_id,))
        req = cursor.fetchone()
        
        if not req:
            conn.close()
            return jsonify({'success': False, 'message': 'Leave request not found.'}), 404
        
        req_status = req['status'] if isinstance(req, dict) else req[8]
        if req_status != 'Pending':
            conn.close()
            return jsonify({'success': False, 'message': 'Request already processed.'}), 400
        
        # Calculate days
        start_date = req['start_date'] if isinstance(req, dict) else req[5]
        end_date = req['end_date'] if isinstance(req, dict) else req[6]
        leave_type = req['leave_type'] if isinstance(req, dict) else req[4]
        user_id = req['user_id'] if isinstance(req, dict) else req[1]
        
        from datetime import datetime
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        days = (end_date - start_date).days + 1
        
        cursor2 = conn.cursor()
        if decision == 'Approve':
            cursor2.execute("""
                UPDATE leave_requests SET status='Approved', reviewed_by=?, review_date=datetime('now')
                WHERE leave_id=?
            """, (admin_id, leave_id))
            
            # Update user balances (increment taken)
            if leave_type in ('Vacation', 'Personal Day'):
                cursor2.execute("""
                    UPDATE users SET vacation_days_taken = vacation_days_taken + ?
                    WHERE user_id=?
                """, (days, user_id))
            elif leave_type == 'Sick Leave':
                cursor2.execute("""
                    UPDATE users SET sick_days_taken = sick_days_taken + ?
                    WHERE user_id=?
                """, (days, user_id))
            
            message = f'Leave request #{leave_id} approved for {days} day(s).'
        else:
            cursor2.execute("""
                UPDATE leave_requests SET status='Rejected', reviewed_by=?, review_date=datetime('now')
                WHERE leave_id=?
            """, (admin_id, leave_id))
            message = f'Leave request #{leave_id} rejected.'
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': message}), 200
        
    except Exception as e:
        print(f"Review leave request error: {e}")
        return jsonify({'success': False, 'message': f'Error processing leave request: {str(e)}'}), 500

@app.route('/api/admin/holidays', methods=['GET'])
@admin_required
def get_holidays():
    """Get holidays for the year"""
    try:
        year = int(request.args.get('year', date.today().year))
        start = date(year, 1, 1)
        end = date(year, 12, 31)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM holidays 
            WHERE holiday_date BETWEEN ? AND ? 
            ORDER BY holiday_date
        """, (start, end))
        holidays = cursor.fetchall()
        conn.close()
        
        holidays_list = [dict(h) if isinstance(h, dict) else {
            'holiday_id': h[0],
            'holiday_date': h[1],
            'holiday_name': h[2]
        } for h in holidays]
        
        return jsonify({'success': True, 'data': {'holidays': holidays_list, 'year': year}}), 200
        
    except Exception as e:
        print(f"Get holidays error: {e}")
        return jsonify({'success': False, 'message': f'Error loading holidays: {str(e)}'}), 500

@app.route('/api/admin/holidays', methods=['POST'])
@admin_required
def create_holiday():
    """Add new holiday"""
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        date_str = data.get('holiday_date', '')
        name = data.get('holiday_name', '').strip()
        
        if not date_str or not name:
            return jsonify({'success': False, 'message': 'Holiday date and name required'}), 400
        
        try:
            hdate = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid holiday date format. Use YYYY-MM-DD'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO holidays (holiday_date, holiday_name) 
            VALUES (?, ?)
        """, (hdate, name))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Holiday saved'}), 201
        
    except Exception as e:
        print(f"Create holiday error: {e}")
        return jsonify({'success': False, 'message': f'Error saving holiday: {str(e)}'}), 500

@app.route('/api/admin/holidays/<int:holiday_id>', methods=['DELETE'])
@admin_required
def delete_holiday(holiday_id):
    """Delete a holiday"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM holidays WHERE holiday_id = ?", (holiday_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Holiday deleted'}), 200
        
    except Exception as e:
        print(f"Delete holiday error: {e}")
        return jsonify({'success': False, 'message': f'Error deleting holiday: {str(e)}'}), 500

@app.route('/admin/employee_attendance_data/<user_id>')
@admin_required
def employee_attendance_data(user_id):
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    try:
        today = date.today()
        if not start_date_str:
            start_date = today.replace(day=1)
        else:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        if not end_date_str:
            # last day of current month
            next_month = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1)
            end_date = next_month - timedelta(days=1)
        else:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        if end_date < start_date:
            return jsonify({'error':'Invalid range'}), 400
        conn = get_db_connection(); cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id = ? AND role = 'employee'",  (user_id,))
        if not cursor.fetchone():
            conn.close(); return jsonify({'error':'User not found'}), 404
        # Attendance rows (include type)
        cursor.execute("""
            SELECT date, attendance_type
            FROM attendance
            WHERE user_id=? AND date BETWEEN ? AND ? AND check_in_time IS NOT NULL
        """,  (user_id, start_date, end_date))
        att_rows = cursor.fetchall()
        # Approved leave days with type
        cursor.execute("""
            SELECT leave_type, start_date, end_date FROM leave_requests
            WHERE user_id=? AND status='Approved' AND NOT (end_date < ? OR start_date > ?)
        """,  (user_id, start_date, end_date))
        leave_rows = cursor.fetchall()
        conn.close()
        present_dates = {}
        for r in att_rows:
            if r['attendance_type'] == 'Comp-Off':
                present_dates[r['date']] = 'comp_off'
            else:
                present_dates[r['date']] = 'present'
        leave_map = {}
        for lr in leave_rows:
            cur = max(lr['start_date'], start_date)
            last = min(lr['end_date'], end_date)
            while cur <= last:
                if cur not in present_dates:  # do not override worked days
                    leave_map[cur] = lr['leave_type']
                cur += timedelta(days=1)
        data = []
        for d, st in sorted(present_dates.items()):
            if st == 'comp_off':
                data.append({'date': d.strftime('%Y-%m-%d'), 'status': 'comp_off'})
            else:
                data.append({'date': d.strftime('%Y-%m-%d'), 'status': 'present'})
        for d, ltype in sorted(leave_map.items()):
            data.append({'date': d.strftime('%Y-%m-%d'), 'status': 'on_leave', 'leave_type': ltype})
        return jsonify(data)
    except Exception as e:
        print(f"Attendance data API error: {e}")
        return jsonify({'error':'Server error'}), 500

# ====================== ERROR HANDLERS ======================

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# ====================== DEBUG ROUTES (Remove in production) ======================

@app.route('/debug/users')
def debug_users():
    """Debug route to check users in database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, name, role FROM users")
        users = cursor.fetchall()
        conn.close()
        return f"<h2>Debug: Users in Database</h2><pre>{users}</pre><br><a href='/'>Back to Login</a>"
    except Exception as e:
        return f"<h2>Debug Error:</h2><pre>{str(e)}</pre><br><a href='/'>Back to Login</a>"

@app.route('/debug/test-login')
def debug_test_login():
    """Debug route to test admin login"""
    return '''
    <h2>Debug: Test Admin Login</h2>
    <p>Use these credentials based on your database:</p>
    <ul>
        <li><strong>Username:</strong> francis</li>
        <li><strong>Password:</strong> adminpassword</li>
        <li><strong>Role:</strong> admin</li>
    </ul>
    <form method="POST" action="/login">
        <input type="hidden" name="role" value="admin">
        <input type="text" name="username" value="francis" placeholder="Username"><br><br>
        <input type="password" name="password" value="adminpassword" placeholder="Password"><br><br>
        <button type="submit">Test Admin Login</button>
    </form>
    <br><a href="/">Back to Main Login</a>
    '''

# ====================== COMP-OFF / HOLIDAY HELPERS ======================

def is_sunday(d: date) -> bool:
    return d.weekday() == 6  # Monday=0 .. Sunday=6


def get_holidays_between(cursor, start_d: date, end_d: date):
    """Return set of holiday dates between range inclusive."""
    cursor.execute("SELECT holiday_date FROM holidays WHERE holiday_date BETWEEN ? AND ?",  (start_d, end_d))
    return {row['holiday_date'] for row in cursor.fetchall()}


def is_holiday(cursor, d: date) -> bool:
    cursor.execute("SELECT 1 FROM holidays WHERE holiday_date = ?",  (d,))
    return cursor.fetchone() is not None


def is_non_working_day(cursor, d: date) -> bool:
    """Company non-working day definition: Sunday OR defined holiday."""
    return is_sunday(d) or is_holiday(cursor, d)


def get_upcoming_non_working_days(cursor, days_ahead: int = 45):
    """Compute list of upcoming non-working days (next N days) including today.
    Only include days that do not already have an approved / pending comp-off request for the current user (filtered later).
    Returns list[date]."""
    today = date.today()
    end = today + timedelta(days=days_ahead)
    holidays = get_holidays_between(cursor, today, end)
    results = []
    cur = today
    while cur <= end:
        if cur.weekday() == 6 or cur in holidays:  # Sunday or known holiday
            results.append(cur)
        cur += timedelta(days=1)
    return results

# ====================== COMP-OFF ROUTES (Employee) ======================

@app.route('/request_compoff', methods=['GET', 'POST'])
@employee_required
def request_compoff():
    """Employee requests permission to work on an upcoming non-working day (Sunday/holiday).
    POST: validate date is future non-working day and not already requested/approved; insert pending request.
    GET: list valid upcoming non-working days and recent request history."""
    user_id = session.get('user_id')
    try:
        conn = get_db_connection(); cursor = conn.cursor()
        if request.method == 'POST':
            date_str = request.form.get('work_date')
            reason = (request.form.get('reason') or '').strip()
            if not date_str or not reason:
                flash('Date and reason required','error'); conn.close(); return redirect(url_for('request_compoff'))
            try:
                work_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format','error'); conn.close(); return redirect(url_for('request_compoff'))
            today = date.today()
            if work_date < today:
                flash('Date must be in the future or today','error'); conn.close(); return redirect(url_for('request_compoff'))
            # Must be non-working day
            if not is_non_working_day(cursor, work_date):
                flash('Selected date is not a company non-working day','error'); conn.close(); return redirect(url_for('request_compoff'))
            # No duplicate pending/approved
            cursor.execute("""
                SELECT 1 FROM compoff_requests
                WHERE user_id=? AND work_date=? AND status IN ('Pending','Approved')
            """,  (user_id, work_date))
            if cursor.fetchone():
                flash('You already have a pending/approved request for this date','info'); conn.close(); return redirect(url_for('request_compoff'))
            cursor2 = conn.cursor()
            cursor2.execute("""
                INSERT INTO compoff_requests (user_id, work_date, reason)
                VALUES (?,?,?)
            """, (user_id, work_date, reason))
            conn.commit(); conn.close(); flash('Comp-off request submitted','success'); return redirect(url_for('request_compoff'))
        # GET flow
        # Compute upcoming valid non-working days
        upcoming = get_upcoming_non_working_days(cursor, 60)
        # Filter out those with existing pending/approved requests
        if upcoming:
            cursor.execute("""
                SELECT work_date, status FROM compoff_requests
                WHERE user_id=? AND work_date BETWEEN ? AND ?
            """,  (user_id, min(upcoming), max(upcoming)))
            existing = {row['work_date'] for row in cursor.fetchall()}
            valid_dates = [d for d in upcoming if d not in existing]
        else:
            valid_dates = []
        # Recent history (latest 15)
        cursor.execute("""
            SELECT request_id, work_date, status, reason, request_date, review_date
            FROM compoff_requests
            WHERE user_id=?
            ORDER BY request_date DESC
            LIMIT 15
        """,  (user_id,))
        history = cursor.fetchall(); conn.close()
        return render_template('request_compoff.html', username=session['username'], valid_dates=valid_dates, history=history)
    except Exception as e:
        print(f"Request comp-off error: {e}")
        import traceback
        traceback.print_exc()
        flash(f'Comp-off page error: {str(e)}','error')
        return redirect(url_for('dashboard'))

# ====================== COMP-OFF ROUTES (Admin) ======================

@app.route('/admin/compoff_requests')
@admin_required
def admin_compoff_requests():
    try:
        conn = get_db_connection(); cursor = conn.cursor()
        # Pending list
        cursor.execute("""
            SELECT cr.request_id, cr.user_id, u.employee_name, u.username, cr.work_date, cr.reason, cr.status, cr.request_date
            FROM compoff_requests cr
            JOIN users u ON cr.user_id = u.user_id
            WHERE cr.status='Pending'
            ORDER BY cr.request_date ASC
        """)
        pending = cursor.fetchall()
        # Recent decisions (last 10 approved/rejected)
        cursor.execute("""
            SELECT cr.request_id, u.employee_name, cr.work_date, cr.status, cr.review_date
            FROM compoff_requests cr
            JOIN users u ON cr.user_id = u.user_id
            WHERE cr.status IN ('Approved','Rejected')
            ORDER BY cr.review_date DESC
            LIMIT 10
        """)
        recent = cursor.fetchall()
        # Counts
        cursor.execute("SELECT COUNT(*) AS pending_count FROM compoff_requests WHERE status='Pending'")
        counts = cursor.fetchone() or {'pending_count':0}
        conn.close()
        return render_template('compoff_requests.html', username=session['username'], pending_requests=pending, recent_requests=recent, counts=counts)
    except Exception as e:
        print(f"Admin comp-off list error: {e}")
        flash('Failed to load comp-off requests','error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/review_compoff/<int:request_id>', methods=['POST'])
@admin_required
def review_compoff(request_id):
    decision = request.form.get('decision')  # Approve / Reject
    if decision not in ('Approve','Reject'):
        flash('Invalid decision','error'); return redirect(url_for('admin_compoff_requests'))
    admin_id = session.get('user_id')
    try:
        conn = get_db_connection(); cursor = conn.cursor()
        cursor.execute("SELECT * FROM compoff_requests WHERE request_id = ?",  (request_id,))
        req = cursor.fetchone()
        if not req:
            conn.close(); flash('Request not found','error'); return redirect(url_for('admin_compoff_requests'))
        if req['status'] != 'Pending':
            conn.close(); flash('Already reviewed','info'); return redirect(url_for('admin_compoff_requests'))
        cursor2 = conn.cursor()
        if decision == 'Approve':
            cursor2.execute("""
                UPDATE compoff_requests
                SET status='Approved', reviewed_by=?, review_date=datetime('now')
                WHERE request_id=?
            """, (admin_id, request_id))
            flash(f'Comp-off request #{request_id} approved','success')
        else:
            cursor2.execute("""
                UPDATE compoff_requests
                SET status='Rejected', reviewed_by=?, review_date=datetime('now')
                WHERE request_id=?
            """, (admin_id, request_id))
            flash(f'Comp-off request #{request_id} rejected','info')
        conn.commit(); conn.close()
        return redirect(url_for('admin_compoff_requests'))
    except Exception as e:
        print(f"Review comp-off error: {e}")
        flash('Error processing comp-off request','error')
        return redirect(url_for('admin_compoff_requests'))

@app.route('/admin/credit_compoff/<int:attendance_id>', methods=['POST'])
@admin_required
def credit_compoff(attendance_id):
    """Admin credits a worked comp-off day: mark attendance row credited and increment employee balance once."""
    try:
        conn = get_db_connection(); cursor = conn.cursor()
        # Get attendance record, ensure type comp-off and not credited
        cursor.execute("""
            SELECT a.attendance_id, a.user_id, a.date, a.attendance_type, a.compoff_credited,
                   a.check_in_time, a.check_out_time
            FROM attendance a
            WHERE a.attendance_id=?
        """,  (attendance_id,))
        att = cursor.fetchone()
        if not att:
            conn.close(); flash('Attendance record not found','error'); return redirect(request.referrer or url_for('admin_dashboard'))
        if att['attendance_type'] != 'Comp-Off':
            conn.close(); flash('Not a Comp-Off attendance day','error'); return redirect(request.referrer or url_for('admin_dashboard'))
        if att['compoff_credited']:
            conn.close(); flash('Already credited','info'); return redirect(request.referrer or url_for('admin_dashboard'))
        # Require checkout completed (worked day)
        if not att['check_in_time'] or not att['check_out_time']:
            conn.close(); flash('Incomplete attendance cannot be credited','error'); return redirect(request.referrer or url_for('admin_dashboard'))
        cursor2 = conn.cursor()
        cursor2.execute("UPDATE attendance SET compoff_credited=1 WHERE attendance_id=%s", (attendance_id,))
        cursor2.execute("UPDATE users SET compoff_balance = compoff_balance + 1 WHERE user_id=%s", (att['user_id'],))
        conn.commit(); conn.close(); flash('Comp-off day credited','success')
        return redirect(request.referrer or url_for('admin_dashboard'))
    except Exception as e:
        print(f"Credit comp-off error: {e}")
        flash('Failed to credit comp-off','error')
        return redirect(request.referrer or url_for('admin_dashboard'))

@app.route('/admin/compoff_report')
@admin_required
def admin_compoff_report():
    """Admin page showing detailed comp-off report table (history of all requests)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch ALL requests joined with user names
        cursor.execute("""
            SELECT r.request_id, r.user_id, r.request_date, r.reason, r.status, r.reviewed_by, r.review_date, r.created_at, r.work_date, u.employee_name as employee_name 
            FROM compoff_requests r 
            JOIN users u ON r.user_id = u.user_id 
            ORDER BY r.created_at DESC
        """)
        requests = cursor.fetchall()
        
        report_data = []
        for req in requests:
            # Determine lifecycle status
            lifecycle_status = req['status']
            badge_class = 'secondary'
            
            # Formatting dates (handle both string and datetime objects)
            try:
                formatted_work_date = req['work_date'] if isinstance(req['work_date'], str) else req['work_date'].strftime('%Y-%m-%d') if req['work_date'] else '-'
            except (AttributeError, TypeError):
                formatted_work_date = '-'
            
            try:
                formatted_review_date = req['review_date'] if isinstance(req['review_date'], str) else req['review_date'].strftime('%Y-%m-%d %H:%M') if req['review_date'] else '-'
            except (AttributeError, TypeError):
                formatted_review_date = '-'
            
            if req['status'] == 'Pending':
                badge_class = 'warning'
                lifecycle_status = 'Pending Approval'
            elif req['status'] == 'Rejected':
                badge_class = 'danger'
                lifecycle_status = 'Rejected'
            elif req['status'] == 'Approved':
                lifecycle_status = 'Approved (Pending Work)'
                badge_class = 'info'
                
                # Check if work was done for this approved date
                cursor.execute("""
                    SELECT attendance_id, compoff_credited, check_in_time, check_out_time 
                    FROM attendance 
                    WHERE user_id = ? AND date = ? AND attendance_type = 'Comp-Off'
                """,  (req['user_id'], req['work_date']))
                att = cursor.fetchone()
                
                if att:
                    if att['compoff_credited']:
                        lifecycle_status = 'Credited to Balance'
                        badge_class = 'success'
                    elif att['check_in_time'] and att['check_out_time']:
                        lifecycle_status = 'Work Done (Pending Credit)'
                        badge_class = 'primary'
                    elif att['check_in_time']:
                        lifecycle_status = 'Work In Progress'
                        badge_class = 'primary'

            report_data.append({
                'id': req['request_id'],
                'employee': req['employee_name'],
                'date': formatted_work_date,
                'reason': req['reason'],
                'status': req['status'],
                'lifecycle_status': lifecycle_status,
                'badge_class': badge_class,
                'reviewed': formatted_review_date
            })
        
        conn.close()
        
        return render_template('compoff_report.html',
                             username=session['username'],
                             report_data=report_data)
                             
    except Exception as e:
        print(f"Comp-off report error: {e}")
        flash('Failed to load comp-off report', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/compoff_history/<user_id>')
@admin_required
def admin_compoff_history(user_id):
    """API endpoint returning JSON history of comp-off days earned by specific employee"""
    user_id = user_id.strip() # Clean input
    print(f"DEBUG: Fetching comp-off history for user_id='{user_id}'")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # We need to show:
        # 1. Approved requests that haven't been worked yet (Incomplete)
        # 2. Worked days (Completed/Credited or Pending Credit)
        
        history = []
        
        # 1. Get ALL requests (Pending, Approved, Rejected)
        cursor.execute("""
            SELECT request_id, request_date, reason, status, review_date, reviewed_by, work_date
            FROM compoff_requests 
            WHERE user_id = ? 
            ORDER BY request_date DESC
        """,  (user_id,))
        requests = cursor.fetchall()
        print(f"DEBUG: Found {len(requests)} total requests for {user_id}")
        
        for req in requests:
            # Check for attendance ONLY if Approved
            att = None
            if req['status'] == 'Approved':
                cursor.execute("""
                    SELECT attendance_id, check_in_time, check_out_time, compoff_credited, check_in_address, check_out_address
                    FROM attendance
                    WHERE user_id = ? AND date = ? AND attendance_type = 'Comp-Off'
                """,  (user_id, req['work_date']))
                att = cursor.fetchone()
            
            # Handle both string and datetime for work_date
            date_str = req['work_date'] if isinstance(req['work_date'], str) else req['work_date'].strftime('%Y-%m-%d') if req['work_date'] else 'N/A'
            date_formatted = req['work_date'] if isinstance(req['work_date'], str) else req['work_date'].strftime('%B %d, %Y') if req['work_date'] else 'N/A'
            
            entry = {
                'date': date_str,
                'date_formatted': date_formatted,
                'reason': req['reason'] or 'No reason provided',
                'check_in_time': 'N/A',
                'check_out_time': 'N/A',
                'check_in_address': 'N/A',
                'check_out_address': 'N/A',
                'credited': False,
                'request_status': req['status'],
                'status': req['status'], # Default status is the request status
                'badge_class': 'secondary'
            }

            if req['status'] == 'Pending':
                entry['badge_class'] = 'warning'
                entry['status'] = 'Request Pending'
            elif req['status'] == 'Rejected':
                entry['badge_class'] = 'danger'
                entry['status'] = 'Request Rejected'
            elif req['status'] == 'Approved':
                entry['badge_class'] = 'info'
                entry['status'] = 'Approved (Pending Work)'
                
                if att:
                    entry['check_in_time'] = str(att['check_in_time']) if att['check_in_time'] else 'N/A'
                    entry['check_out_time'] = str(att['check_out_time']) if att['check_out_time'] else 'N/A'
                    entry['check_in_address'] = att['check_in_address'] or 'N/A'
                    entry['check_out_address'] = att['check_out_address'] or 'N/A'
                    entry['credited'] = bool(att['compoff_credited'])
                    
                    if att['compoff_credited']:
                        entry['status'] = 'Added to Leave Balance'
                        entry['badge_class'] = 'success'
                    elif att['check_in_time'] and att['check_out_time']:
                       entry['status'] = 'Work Completed (Pending Credit)'
                       entry['badge_class'] = 'primary'
                    elif att['check_in_time']:
                        entry['status'] = 'Work In Progress'
                        entry['badge_class'] = 'primary'
            
            history.append(entry)
            
        conn.close()
        return jsonify(history)
        
    except Exception as e:
        print(f"Comp-off history API error: {e}")
        return jsonify({'error': 'Failed to fetch history'}), 500

# ====================== RUN APPLICATION ======================



@app.route('/admin/debug-database')
@admin_required
def debug_database():
    """Debug route to check database structure"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SHOW TABLES")
        tables = [row[list(row.keys())[0]] for row in cursor.fetchall()]
        
        # Get users table structure
        cursor.execute("DESCRIBE users")
        users_columns = cursor.fetchall()
        
        # Check if company_settings exists and get structure
        company_settings_columns = []
        if 'company_settings' in tables:
            cursor.execute("DESCRIBE company_settings")
            company_settings_columns = cursor.fetchall()
        
        # Check if site_visits exists and get structure
        site_visits_columns = []
        if 'site_visits' in tables:
            cursor.execute("DESCRIBE site_visits")
            site_visits_columns = cursor.fetchall()
        
        conn.close()
        
        debug_info = f"""
        <h2>Database Structure Debug</h2>
        <h3>Tables: {', '.join(tables)}</h3>
        
        <h3>Users Table Columns:</h3>
        <pre>{users_columns}</pre>
        
        <h3>Company Settings Table Columns:</h3>
        <pre>{company_settings_columns}</pre>
        
        <h3>Site Visits Table Columns:</h3>
        <pre>{site_visits_columns}</pre>
        
        <a href="{url_for('admin_dashboard')}">Back to Dashboard</a>
        """
        
        return debug_info
        
    except Exception as e:
        return f"Debug error: {str(e)}<br><a href='{url_for('admin_dashboard')}'>Back to Dashboard</a>"

@app.route('/admin/cleanup-geofencing')
@admin_required
def cleanup_geofencing():
    """Remove all geofencing features from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        results = []
        
        # Drop tables if they exist
        tables_to_drop = ['site_visits', 'company_settings', 'geofence_requests']
        for table in tables_to_drop:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                conn.commit()
                results.append(f"✅ Dropped table: {table}")
            except Exception as e:
                results.append(f"⚠️ Table {table}: {e}")
        
        # Remove columns from users table
        columns_to_drop = ['geofence_status', 'geofence_lat', 'geofence_lon', 'work_mode', 'remote_address', 'remote_latitude', 'remote_longitude']
        for column in columns_to_drop:
            try:
                cursor.execute(f"ALTER TABLE users DROP COLUMN IF EXISTS {column}")
                conn.commit()
                results.append(f"✅ Removed column: {column}")
            except Exception as e:
                results.append(f"⚠️ Column {column}: {e}")
        
        conn.close()
        
        # Show results to user
        flash('<br>'.join(results), 'success')
        return redirect(url_for('admin_dashboard'))
        
    except Exception as e:
        print(f"Cleanup error: {e}")
        flash(f'Cleanup error: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/migrate-database')
@admin_required
def migrate_database():
    """Run database migration for work modes system"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        results = []
        
        # Check if columns exist before adding them
        cursor.execute("SHOW COLUMNS FROM users LIKE 'work_mode'")
        if not cursor.fetchone():
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN work_mode ENUM('Office', 'Remote') DEFAULT 'Office'")
                conn.commit()
                results.append("✅ Added work_mode column to users table")
            except Exception as e:
                results.append(f"⚠️ work_mode column: {e}")

        cursor.execute("SHOW COLUMNS FROM users LIKE 'remote_address'")
        if not cursor.fetchone():
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN remote_address TEXT")
                conn.commit()
                results.append("✅ Added remote_address column to users table")
            except Exception as e:
                results.append(f"⚠️ remote_address column: {e}")

        cursor.execute("SHOW COLUMNS FROM users LIKE 'remote_latitude'")
        if not cursor.fetchone():
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN remote_latitude DECIMAL(10, 8)")
                conn.commit()
                results.append("✅ Added remote_latitude column to users table")
            except Exception as e:
                results.append(f"⚠️ remote_latitude column: {e}")

        cursor.execute("SHOW COLUMNS FROM users LIKE 'remote_longitude'")
        if not cursor.fetchone():
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN remote_longitude DECIMAL(11, 8)")
                conn.commit()
                results.append("✅ Added remote_longitude column to users table")
            except Exception as e:
                results.append(f"⚠️ remote_longitude column: {e}")
        
        # Create company_settings table
        cursor.execute("SHOW TABLES LIKE 'company_settings'")
        if not cursor.fetchone():
            try:
                cursor.execute("""
                    CREATE TABLE company_settings (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        setting_key VARCHAR(100) UNIQUE NOT NULL,
                        setting_value TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                results.append("✅ Created company_settings table")
            except Exception as e:
                results.append(f"⚠️ company_settings table: {e}")
        
        # Create site_visits table
        cursor.execute("SHOW TABLES LIKE 'site_visits'")
        if not cursor.fetchone():
            try:
                cursor.execute("""
                    CREATE TABLE site_visits (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id VARCHAR(10) NOT NULL,
                        site_name VARCHAR(255) NOT NULL,
                        site_address TEXT NOT NULL,
                        site_latitude DECIMAL(10, 8) NOT NULL,
                        site_longitude DECIMAL(11, 8) NOT NULL,
                        start_date DATE NOT NULL,
                        end_date DATE NOT NULL,
                        status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
                        approved_by VARCHAR(10),
                        approval_date TIMESTAMP NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id),
                        FOREIGN KEY (approved_by) REFERENCES users(user_id)
                    )
                """)
                conn.commit()
                results.append("✅ Created site_visits table")
            except Exception as e:
                results.append(f"⚠️ site_visits table: {e}")
        
        # Insert default office settings
        try:
            cursor.execute("SELECT COUNT(*) as count FROM company_settings WHERE setting_key = 'office_address'")
            if cursor.fetchone()['count'] == 0:
                cursor.execute("""
                    INSERT INTO company_settings (setting_key, setting_value) 
                    VALUES ('office_address', 'Please set your company office address'),
                           ('office_latitude', '40.7128'), 
                           ('office_longitude', '-74.0060')
                """)
                conn.commit()
                results.append("✅ Inserted default office settings")
        except Exception as e:
            results.append(f"⚠️ Default office settings: {e}")
        
        conn.close()
        
        # Show results to user
        flash('<br>'.join(results), 'success')
        return redirect(url_for('admin_dashboard'))
        
    except Exception as e:
        print(f"Migration error: {e}")
        flash(f'Migration error: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    print("Starting CGS Attendance Management System...")
    print("Admin Panel: Login with admin credentials")
    print("Employee Portal: Login with employee credentials")
    print("Access: http://localhost:5000")
    
    # Force auto-reload for development ease
    debug_mode = True 
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)