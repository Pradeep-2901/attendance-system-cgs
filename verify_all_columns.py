import sqlite3

conn = sqlite3.connect('attendance_system.db')
cursor = conn.cursor()

cursor.execute('PRAGMA table_info(attendance)')
columns = cursor.fetchall()

required_cols = [
    'check_in_latitude', 'check_in_longitude', 'check_out_latitude', 'check_out_longitude',
    'check_in_address', 'check_out_address', 
    'image_path_checkin', 'image_path_checkout', 
    'attendance_type'
]
found_cols = [col[1] for col in columns]

print('✓ All Attendance Columns Verification:\n')
for col in required_cols:
    status = '✓' if col in found_cols else '✗'
    print(f'{status} {col}')

print(f'\nTotal columns in attendance table: {len(columns)}')
conn.close()
