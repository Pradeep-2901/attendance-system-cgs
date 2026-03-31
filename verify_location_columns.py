import sqlite3

conn = sqlite3.connect('attendance_system.db')
cursor = conn.cursor()

cursor.execute('PRAGMA table_info(attendance)')
columns = cursor.fetchall()

location_cols = ['check_in_latitude', 'check_in_longitude', 'check_out_latitude', 'check_out_longitude']
found_cols = [col[1] for col in columns]

print('✓ Database Schema Verification:\n')
for col in location_cols:
    status = '✓' if col in found_cols else '✗'
    print(f'{status} {col}')

print(f'\nTotal columns in attendance table: {len(columns)}')
conn.close()
