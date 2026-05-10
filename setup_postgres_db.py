#!/usr/bin/env python3
"""
PostgreSQL Database Setup for Neon + Render Deployment
Initializes PostgreSQL database with essential tables and demo users
"""

import psycopg2
from werkzeug.security import generate_password_hash
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ ERROR: DATABASE_URL not set in environment variables!")
    print("   Set DATABASE_URL=postgresql://user:password@host:5432/dbname")
    exit(1)

# Demo users with hashed passwords - EXACTLY SAME AS BEFORE
DEMO_USERS = [
    {'username': 'francis', 'password': 'francis123', 'employee_name': 'Francis Johnson', 'role': 'admin'},
    {'username': 'pradeep', 'password': 'pradeep123', 'employee_name': 'Pradeep Kumar', 'role': 'employee'},
    {'username': 'sounthar', 'password': 'sounthar123', 'employee_name': 'Sounthar S', 'role': 'employee'},
    {'username': 'aadhi', 'password': 'aadhi123', 'employee_name': 'Aadhi P', 'role': 'employee'},
]

def get_db_connection():
    """Create PostgreSQL connection"""
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def create_tables():
    """Create essential tables for attendance system in PostgreSQL"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("[1/5] Creating users table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            employee_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'employee',
            email TEXT,
            phone TEXT,
            department TEXT DEFAULT 'General',
            geofence_status TEXT DEFAULT 'none',
            compoff_balance INTEGER DEFAULT 0,
            work_mode TEXT DEFAULT 'Office',
            remote_address TEXT,
            remote_lat REAL,
            remote_lon REAL,
            vacation_days_total INTEGER DEFAULT 0,
            sick_days_total INTEGER DEFAULT 0,
            vacation_days_taken INTEGER DEFAULT 0,
            sick_days_taken INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("[2/5] Creating attendance table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            attendance_id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            date DATE NOT NULL,
            check_in_time TIME,
            check_out_time TIME,
            check_in_photo TEXT,
            check_out_photo TEXT,
            check_in_location TEXT,
            check_out_location TEXT,
            check_in_address TEXT,
            check_out_address TEXT,
            check_in_latitude REAL,
            check_in_longitude REAL,
            check_out_latitude REAL,
            check_out_longitude REAL,
            check_in_timestamp TIMESTAMP,
            check_out_timestamp TIMESTAMP,
            duration_minutes INTEGER,
            status TEXT DEFAULT 'pending',
            geofence_status TEXT DEFAULT 'valid',
            attendance_type TEXT DEFAULT 'Regular',
            image_path_checkin TEXT,
            image_path_checkout TEXT,
            compoff_credited INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, date)
        )
    ''')
    
    print("[3/5] Creating leaves table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaves (
            leave_id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            leave_type TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("[4/5] Creating geofence_requests table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS geofence_requests (
            request_id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            request_date DATE NOT NULL,
            latitude REAL,
            longitude REAL,
            location_name TEXT,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("[5/5] Creating compoff_requests table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS compoff_requests (
            request_id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            work_date DATE,
            request_date DATE NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            review_date TIMESTAMP,
            reviewed_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("[6/6] Creating additional tables...")
    
    # Leave requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leave_requests (
            leave_request_id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            leave_type TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            reviewed_by INTEGER,
            review_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Remote work requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS remote_work_requests (
            request_id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Site visits table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS site_visits (
            visit_id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            site_name TEXT NOT NULL,
            visit_date DATE,
            purpose TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Sites table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sites (
            site_id SERIAL PRIMARY KEY,
            site_name TEXT NOT NULL UNIQUE,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            radius_km REAL DEFAULT 1.0,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Company settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS company_settings (
            setting_id SERIAL PRIMARY KEY,
            setting_key TEXT NOT NULL UNIQUE,
            setting_value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Holidays table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS holidays (
            holiday_id SERIAL PRIMARY KEY,
            holiday_name TEXT NOT NULL,
            holiday_date DATE NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    cursor.close()
    print("✅ All tables created successfully!")
    return conn

def insert_demo_users(conn):
    """Insert demo users into the PostgreSQL database"""
    cursor = conn.cursor()
    
    print("\nInserting demo users...")
    for user in DEMO_USERS:
        hashed_password = generate_password_hash(user['password'], method='scrypt')
        try:
            cursor.execute('''
                INSERT INTO users (username, password, employee_name, role)
                VALUES (%s, %s, %s, %s)
            ''', (user['username'], hashed_password, user['employee_name'], user['role']))
            print(f"  ✅ {user['username']} ({user['employee_name']}) - {user['role']}")
        except psycopg2.IntegrityError:
            conn.rollback()
            print(f"  ⚠️ {user['username']} already exists (skipping)")
    
    conn.commit()
    cursor.close()
    print("✅ Demo users inserted!")

def verify_setup(conn):
    """Verify the PostgreSQL database setup"""
    cursor = conn.cursor()
    
    print("\n=== Database Verification ===")
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()[0]
    print(f"Users created: {user_count}")
    
    cursor.execute("SELECT COUNT(*) as count FROM attendance")
    attendance_count = cursor.fetchone()[0]
    print(f"Attendance records: {attendance_count}")
    
    print("\nUser accounts:")
    cursor.execute("SELECT username, employee_name, role FROM users ORDER BY user_id")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]} ({row[2]})")
    
    cursor.close()
    print("\n✅ Database setup complete!")
    print("\nDemo credentials:")
    for user in DEMO_USERS:
        print(f"  - {user['username']} / {user['password']}")

def main():
    """Main setup function"""
    print("="*60)
    print("🚀 PostgreSQL Database Setup for Render + Neon")
    print("="*60)
    
    try:
        conn = create_tables()
        insert_demo_users(conn)
        verify_setup(conn)
        conn.close()
        
        print("\n" + "="*60)
        print("✅ Ready for Render + Neon deployment!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
