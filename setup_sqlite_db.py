#!/usr/bin/env python3
"""
SQLite Database Setup for Railway Deployment
Initializes attendance_system.db with essential tables and demo users
"""

import sqlite3
from werkzeug.security import generate_password_hash
from datetime import datetime

DB_FILE = 'attendance_system.db'

# Demo users with hashed passwords
DEMO_USERS = [
    {'username': 'francis', 'password': 'francis123', 'employee_name': 'Francis Johnson', 'role': 'admin'},
    {'username': 'pradeep', 'password': 'pradeep123', 'employee_name': 'Pradeep Kumar', 'role': 'employee'},
    {'username': 'sounthar', 'password': 'sounthar123', 'employee_name': 'Sounthar S', 'role': 'employee'},
    {'username': 'aadhi', 'password': 'aadhi123', 'employee_name': 'Aadhi P', 'role': 'employee'},
]

def create_tables():
    """Create essential tables for attendance system"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    print("[1/5] Creating users table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            employee_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'employee',
            email TEXT,
            phone TEXT,
            department TEXT DEFAULT 'General',
            geofence_status TEXT DEFAULT 'none',
            compoff_balance INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    print("[2/5] Creating attendance table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            date DATE NOT NULL,
            check_in_time TIME,
            check_out_time TIME,
            check_in_photo TEXT,
            check_out_photo TEXT,
            check_in_location TEXT,
            check_out_location TEXT,
            check_in_timestamp TIMESTAMP,
            check_out_timestamp TIMESTAMP,
            duration_minutes INTEGER,
            status TEXT DEFAULT 'pending',
            geofence_status TEXT DEFAULT 'valid',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, date)
        )
    ''')
    
    print("[3/5] Creating leaves table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaves (
            leave_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            leave_type TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    print("[4/5] Creating geofence_requests table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS geofence_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            request_date DATE NOT NULL,
            latitude REAL,
            longitude REAL,
            location_name TEXT,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    print("[5/5] Creating compoff_requests table...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS compoff_requests (
            request_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            request_date DATE NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    conn.commit()
    print("✅ All tables created successfully!")
    return conn

def insert_demo_users(conn):
    """Insert demo users into the database"""
    cursor = conn.cursor()
    
    print("\nInserting demo users...")
    for user in DEMO_USERS:
        hashed_password = generate_password_hash(user['password'], method='scrypt')
        try:
            cursor.execute('''
                INSERT INTO users (username, password, employee_name, role)
                VALUES (?, ?, ?, ?)
            ''', (user['username'], hashed_password, user['employee_name'], user['role']))
            print(f"  ✅ {user['username']} ({user['employee_name']}) - {user['role']}")
        except sqlite3.IntegrityError:
            print(f"  ⚠️ {user['username']} already exists (skipping)")
    
    conn.commit()
    print("✅ Demo users inserted!")

def verify_setup(conn):
    """Verify the database setup"""
    cursor = conn.cursor()
    
    print("\n=== Database Verification ===")
    cursor.execute("SELECT COUNT(*) as count FROM users")
    user_count = cursor.fetchone()[0]
    print(f"Users created: {user_count}")
    
    cursor.execute("SELECT COUNT(*) as count FROM attendance")
    attendance_count = cursor.fetchone()[0]
    print(f"Attendance records: {attendance_count}")
    
    print("\nUser accounts:")
    cursor.execute("SELECT username, employee_name, role FROM users")
    for row in cursor.fetchall():
        print(f"  - {row[0]}: {row[1]} ({row[2]})")
    
    print("\n✅ Database setup complete!")
    print("\nDemo credentials:")
    for user in DEMO_USERS:
        print(f"  - {user['username']} / {user['password']}")

def main():
    """Main setup function"""
    print("="*60)
    print("🚀 SQLite Database Setup for Railway Deployment")
    print("="*60)
    
    try:
        # Check if database already exists
        import os
        if os.path.exists(DB_FILE):
            print(f"\n⚠️ {DB_FILE} already exists. Skipping creation...")
            conn = sqlite3.connect(DB_FILE)
        else:
            print(f"📁 Creating {DB_FILE}...")
            conn = create_tables()
        
        insert_demo_users(conn)
        verify_setup(conn)
        conn.close()
        
        print("\n" + "="*60)
        print("Ready for Railway deployment!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
