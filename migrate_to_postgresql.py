#!/usr/bin/env python3
"""
SQLite to PostgreSQL Query Converter
Converts all SQLite syntax to PostgreSQL in app.py
"""

import re
import sys

def convert_queries(file_path):
    """Convert SQLite queries to PostgreSQL syntax"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Track conversions
    conversions = []
    
    # 1. Replace sqlite3-specific syntax
    original_content = content
    
    # Replace SQLite CAST syntax with PostgreSQL CAST
    content = re.sub(
        r'CAST\(([^)]+)\s+AS\s+UNSIGNED\)',
        r'CAST(\1 AS INTEGER)',
        content
    )
    if content != original_content:
        conversions.append("✅ Converted CAST(... AS UNSIGNED) to CAST(... AS INTEGER)")
    
    original_content = content
    
    # Replace SQLite REGEXP with PostgreSQL LIKE or SIMILAR TO
    content = re.sub(
        r"user_id\s+REGEXP\s+'\\^\\[0-9\\]\\+\\$'",
        "user_id::text ~ '^[0-9]+$'",
        content
    )
    if content != original_content:
        conversions.append("✅ Converted REGEXP to PostgreSQL regex")
    
    original_content = content
    
    # Replace all ? placeholders with %s
    lines = content.split('\n')
    new_lines = []
    
    for line in lines:
        if 'cursor.execute' in line and '?' in line:
            # This is a query line with ? placeholders
            # Count and replace ? with %s
            old_line = line
            # Find the string part (between quotes) and replace ? with %s only there
            
            # Handle both triple quotes and regular quotes
            if "'''" in line:
                # Triple quoted strings
                parts = line.split("'''")
                for i in range(len(parts)):
                    if i % 2 == 1:  # Inside quotes
                        parts[i] = parts[i].replace('?', '%s')
                line = "'''".join(parts)
            else:
                # Regular quoted strings - be more careful
                # Replace ? only in SQL strings (before the parameter list)
                matches = re.finditer(r'"""(.*?)"""|\'\'\'(.*?)\'\'\'|"(.*?)"|\'(.*?)\'', line)
                offset = 0
                for match in matches:
                    string_content = match.group(1) or match.group(2) or match.group(3) or match.group(4)
                    if '?' in string_content:
                        new_string_content = string_content.replace('?', '%s')
                        old_string = match.group(0)
                        quote_type = old_string[0]
                        if old_string.startswith('"""') or old_string.startswith("'''"):
                            quote_type = old_string[:3]
                        new_string = quote_type + new_string_content + quote_type
                        line = line[:match.start() + offset] + new_string + line[match.end() + offset:]
                        offset += len(new_string) - len(old_string)
            
            if old_line != line:
                new_lines.append(line)
                if old_line.count('?') > 0:
                    conversions.append(f"✅ Converted {old_line.count('?')} placeholders in query")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    # Write back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("="*60)
    print("🔄 SQLite to PostgreSQL Conversion Complete")
    print("="*60)
    for conversion in conversions:
        print(conversion)
    
    return len(conversions)

if __name__ == '__main__':
    file_path = 'd:\\Users\\Pradeep\\Downloads\\cggs\\CGS\\app.py'
    try:
        count = convert_queries(file_path)
        print(f"\n✅ {count} conversion blocks applied")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
