#!/usr/bin/env python3
"""
Fix corrupted emoji in app.py
"""

# Read the file
with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the corrupted line
old_line = '                    st.success(f"� Trading Amount: ${trading_amount:,.0f}")'
new_line = '                    # Removed useless trading amount display'

# Replace the corrupted content
if old_line in content:
    content = content.replace(old_line, new_line)
    print("✅ Fixed corrupted trading amount line")
else:
    # Try to find and replace any variation
    import re
    pattern = r'st\.success\(f".*Trading Amount.*\$\{trading_amount.*\}"\)'
    if re.search(pattern, content):
        content = re.sub(pattern, '# Removed useless trading amount display', content)
        print("✅ Fixed corrupted trading amount line with regex")
    else:
        print("❌ Could not find corrupted line")

# Write back
with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("File updated successfully")
