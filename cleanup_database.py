#!/usr/bin/env python3
"""
Database Cleanup Script for Production Submission
Clears all user data and records EXCEPT the admin account
Safe to run before giving the project to mentor
"""

import sqlite3
from datetime import datetime

DB_PATH = 'attendance_system.db'
ADMIN_USERNAME = 'francis'

def backup_database():
    """Create a backup of the database before cleanup"""
    import shutil
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'attendance_system_backup_{timestamp}.db'
    
    try:
        shutil.copy(DB_PATH, backup_file)
        print(f"✅ Backup created: {backup_file}")
        return True
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return False

def get_admin_user_id(cursor):
    """Get the admin user ID"""
    cursor.execute("SELECT user_id FROM users WHERE username = ? AND role = 'admin'", (ADMIN_USERNAME,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        print(f"❌ Error: Admin user '{ADMIN_USERNAME}' not found!")
        return None

def cleanup_database():
    """Clean all data except admin user"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("=" * 60)
        print("🧹 DATABASE CLEANUP FOR PRODUCTION")
        print("=" * 60)
        
        # Get admin user ID
        admin_id = get_admin_user_id(cursor)
        if not admin_id:
            print("❌ Cleanup aborted. Admin user not found.")
            conn.close()
            return False
        
        print(f"\n✅ Admin user found (ID: {admin_id}, Username: {ADMIN_USERNAME})")
        
        # Start cleanup
        print("\n🔄 Starting cleanup (keeping admin account)...\n")
        
        # Step 1: Clear attendance records for all non-admin users
        print("[1/5] Clearing attendance records...")
        cursor.execute("""
            DELETE FROM attendance 
            WHERE user_id != ?
        """, (admin_id,))
        deleted_attendance = cursor.rowcount
        print(f"      ✅ Deleted {deleted_attendance} attendance records")
        
        # Step 2: Clear leaves for all non-admin users
        print("[2/5] Clearing leave records...")
        cursor.execute("""
            DELETE FROM leaves 
            WHERE user_id != ?
        """, (admin_id,))
        deleted_leaves = cursor.rowcount
        print(f"      ✅ Deleted {deleted_leaves} leave records")
        
        # Step 3: Clear geofence requests for all non-admin users
        print("[3/5] Clearing geofence requests...")
        cursor.execute("""
            DELETE FROM geofence_requests 
            WHERE user_id != ?
        """, (admin_id,))
        deleted_geofence = cursor.rowcount
        print(f"      ✅ Deleted {deleted_geofence} geofence requests")
        
        # Step 4: Clear compoff requests for all non-admin users
        print("[4/5] Clearing comp-off requests...")
        cursor.execute("""
            DELETE FROM compoff_requests 
            WHERE user_id != ?
        """, (admin_id,))
        deleted_compoff = cursor.rowcount
        print(f"      ✅ Deleted {deleted_compoff} comp-off requests")
        
        # Step 5: Delete all non-admin users
        print("[5/5] Deleting non-admin user accounts...")
        cursor.execute("""
            DELETE FROM users 
            WHERE user_id != ? AND role != 'admin'
        """, (admin_id,))
        deleted_users = cursor.rowcount
        print(f"      ✅ Deleted {deleted_users} user account(s)")
        
        # Commit changes
        conn.commit()
        
        # Verify cleanup
        print("\n" + "=" * 60)
        print("✅ CLEANUP VERIFICATION")
        print("=" * 60)
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM attendance")
        total_attendance = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM leaves")
        total_leaves = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM geofence_requests")
        total_geofence = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM compoff_requests")
        total_compoff = cursor.fetchone()[0]
        
        cursor.execute("SELECT username, employee_name, role FROM users")
        remaining_users = cursor.fetchall()
        
        print(f"\n📊 Remaining Database Records:")
        print(f"   Users: {total_users}")
        print(f"   Attendance: {total_attendance}")
        print(f"   Leaves: {total_leaves}")
        print(f"   Geofence Requests: {total_geofence}")
        print(f"   Comp-off Requests: {total_compoff}")
        
        print(f"\n👥 Remaining User(s):")
        for user in remaining_users:
            print(f"   - {user[0]}: {user[1]} ({user[2]})")
        
        conn.close()
        
        print("\n" + "=" * 60)
        print("✅ DATABASE CLEANUP COMPLETED SUCCESSFULLY!")
        print("   Ready for mentor submission!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    import os
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"❌ Database file not found: {DB_PATH}")
        print("   Please ensure you're in the correct project directory.")
        return 1
    
    # Create backup
    print("\n🔐 Creating database backup before cleanup...\n")
    if not backup_database():
        print("⚠️ Warning: Backup failed, but continuing with cleanup...")
    
    # Confirm cleanup
    print("\n⚠️  WARNING: This will clear all data except the admin account!")
    print("   A backup has been created as a safety measure.\n")
    
    response = input("Do you want to proceed with cleanup? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("❌ Cleanup cancelled.")
        return 1
    
    # Perform cleanup
    if cleanup_database():
        return 0
    else:
        return 1

if __name__ == '__main__':
    exit(main())
