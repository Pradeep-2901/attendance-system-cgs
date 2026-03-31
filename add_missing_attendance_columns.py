import sqlite3
import sys

def add_missing_columns():
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        columns = {
            'check_in_address': 'TEXT',
            'check_out_address': 'TEXT',
            'image_path_checkin': 'TEXT',
            'image_path_checkout': 'TEXT',
            'attendance_type': 'TEXT'
        }
        
        for column, data_type in columns.items():
            try:
                cursor.execute(f'ALTER TABLE attendance ADD COLUMN {column} {data_type}')
                print(f'✓ Added column: {column} ({data_type})')
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e):
                    print(f'✓ Column already exists: {column}')
                else:
                    print(f'✗ Error adding {column}: {e}')
                    raise
        
        conn.commit()
        print('\n✓ All missing columns added successfully')
        
        cursor.execute('PRAGMA table_info(attendance)')
        columns_info = cursor.fetchall()
        print(f'✓ Attendance table now has {len(columns_info)} columns')
        
        conn.close()
        return True
        
    except Exception as e:
        print(f'✗ Error: {e}')
        return False

if __name__ == '__main__':
    success = add_missing_columns()
    sys.exit(0 if success else 1)
