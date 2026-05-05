# 📊 How to View Your SQLite Database

## Option 1: Using SQLite Command Line (Recommended)

### Step 1: Open Command Prompt or PowerShell
Navigate to your project directory:
```powershell
cd D:\Users\Pradeep\Downloads\cggs\CGS
```

### Step 2: Open SQLite CLI
```bash
sqlite3 attendance_system.db
```

### Step 3: Useful Commands

**View all tables:**
```sql
.tables
```

**View table structure:**
```sql
.schema users
.schema attendance
.schema leaves
.schema geofence_requests
.schema compoff_requests
```

**View all data in a table:**
```sql
SELECT * FROM users;
SELECT * FROM attendance;
SELECT * FROM leaves;
```

**Count records:**
```sql
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM attendance;
SELECT COUNT(*) FROM leaves;
```

**View specific columns:**
```sql
SELECT username, employee_name, role FROM users;
SELECT user_id, date, check_in_time, check_out_time FROM attendance;
```

**Exit SQLite:**
```bash
.quit
```

---

## Option 2: Using Python Script

Create a temporary Python script to view database:

```python
import sqlite3

DB_PATH = 'attendance_system.db'
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# View all users
print("=== USERS ===")
cursor.execute("SELECT user_id, username, employee_name, role FROM users")
for row in cursor.fetchall():
    print(dict(row))

# View all attendance records
print("\n=== ATTENDANCE ===")
cursor.execute("SELECT * FROM attendance LIMIT 10")
for row in cursor.fetchall():
    print(dict(row))

conn.close()
```

---

## Option 3: Using Flask Shell (Interactive)

```bash
# Activate your virtual environment
.\.venv\Scripts\Activate.ps1

# Start Flask shell
flask shell
```

Then in Python shell:
```python
import sqlite3
conn = sqlite3.connect('attendance_system.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM users")
print(cursor.fetchall())
conn.close()
```

---

## 🗂️ Database Tables & Structure

| Table | Purpose |
|-------|---------|
| **users** | User accounts, roles, and employee info |
| **attendance** | Daily check-in/check-out records |
| **leaves** | Leave requests |
| **geofence_requests** | Geofence location requests |
| **compoff_requests** | Comp-off (compensatory day off) requests |

---

## 📝 Admin User Info

**Username:** `francis`  
**Role:** `admin`  
**Password:** `francis123` (default)

---

## 🧹 To Clear Database (Except Admin)

See **cleanup_database.py** in the same directory. Run it before giving your project to your mentor:

```bash
python cleanup_database.py
```
