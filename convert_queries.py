#!/usr/bin/env python3
"""
SQLite to PostgreSQL Query Converter
Converts all SQLite syntax in app.py to PostgreSQL-compatible syntax
"""

import re

def convert_app_py():
    """Convert app.py from SQLite to PostgreSQL"""
    
    # Read the file
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("="*60)
    print("🔄 Converting SQLite to PostgreSQL Syntax")
    print("="*60)
    
    conversions_made = 0
    
    # 1. Replace ? placeholders with %s
    # Handle both triple quotes and regular quotes
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        if 'cursor.execute' in line and '?' in line:
            # Count question marks in the string part
            old_line = line
            # Simple regex to find quoted strings
            pattern = r'(["\'])((?:(?=(\\?))\3.)*?)\1'
            def replace_in_string(m):
                return m.group(1) + m.group(2).replace('?', '%s') + m.group(1)
            
            line = re.sub(pattern, replace_in_string, line)
            if line != old_line:
                conversions_made += 1
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    print(f"✅ Converted {conversions_made} cursor.execute() calls (? → %s)")
    
    # 2. Replace datetime('now') with CURRENT_TIMESTAMP
    original = content
    content = re.sub(
        r"datetime\s*\(\s*'now'\s*\)",
        "CURRENT_TIMESTAMP",
        content
    )
    if original != content:
        print("✅ Converted datetime('now') → CURRENT_TIMESTAMP")
    
    # 3. Replace CAST(...  AS UNSIGNED) with CAST(... AS INTEGER)
    original = content
    content = re.sub(
        r'CAST\s*\(\s*([^)]+)\s+AS\s+UNSIGNED\s*\)',
        r'CAST(\1 AS INTEGER)',
        content,
        flags=re.IGNORECASE
    )
    if original != content:
        print("✅ Converted CAST(... AS UNSIGNED) → CAST(... AS INTEGER)")
    
    # 4. Replace SQLite strftime patterns
    original = content
    content = re.sub(
        r"strftime\s*\(\s*'%Y-%m-%d'\s*,\s*([^)]+)\s*\)",
        r"DATE_TRUNC('day', \1)::date",
        content
    )
    if original != content:
        print("✅ Converted strftime('%Y-%m-%d', ...) → DATE_TRUNC('day', ...)::date")
    
    # 5. Replace INSERT OR REPLACE with INSERT
    original = content
    content = re.sub(
        r'INSERT\s+OR\s+REPLACE\s+INTO',
        'INSERT INTO',
        content,
        flags=re.IGNORECASE
    )
    if original != content:
        print("✅ Converted INSERT OR REPLACE INTO → INSERT INTO")
    
    # Write back
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("\n" + "="*60)
    print("✅ app.py conversion complete!")
    print("="*60)

if __name__ == '__main__':
    try:
        convert_app_py()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
