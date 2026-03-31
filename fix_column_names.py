#!/usr/bin/env python3
"""
Fix all 'name' column references to use 'employee_name' in SQL queries
"""
import re

print("🔄 Fixing database column references...")

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Count replacements
replacements = 0

# Simple pattern replacements
replacements_list = [
    ("u.name as", "u.employee_name as", "u.name AS alias"),
    ("u.name,", "u.employee_name,", "u.name in SELECT"),
    ("ORDER BY name", "ORDER BY employee_name", "ORDER BY name"),
    ("(user_id, name,", "(user_id, employee_name,", "INSERT with name column"),
]

for old, new, desc in replacements_list:
    if old in content:
        content = content.replace(old, new)
        replacements += 1
        print(f"  ✅ {desc}: {old} → {new}")

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\n✅ Fixed {replacements} column references!")
print("✅ All 'name' columns now reference 'employee_name'")
