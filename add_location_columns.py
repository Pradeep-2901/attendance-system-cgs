import sqlite3
import sys

def add_location_columns():
    try:
        conn = sqlite3.connect('attendance_system.db')
        cursor = conn.cursor()
        
        columns = [
            'check_in_latitude',
            'check_in_longitude',
            'check_out_latitude',
            'check_out_longitude'
        ]
        
        for column in columns:
            try:
                cursor.execute(f'ALTER TABLE attendance ADD COLUMN {column} REAL')
                print(f'✓ Added column: {column}')
            except sqlite3.OperationalError as e:
                if 'duplicate column name' in str(e):
                    print(f'✓ Column already exists: {column}')
                else:
                    print(f'✗ Error adding {column}: {e}')
                    raise
        
        conn.commit()
        print('\n✓ Database schema updated successfully')
        
        cursor.execute('PRAGMA table_info(attendance)')
        columns_info = cursor.fetchall()
        print(f'\n✓ Attendance table now has {len(columns_info)} columns')
        
        conn.close()
        return True
        
    except Exception as e:
        print(f'✗ Error: {e}')
        return False

if __name__ == '__main__':
    success = add_location_columns()
    sys.exit(0 if success else 1)
