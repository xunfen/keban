#!/usr/bin/env python3
"""Remove ALL orphaned code blocks in TeacherDashboard.vue"""
import re

filepath = 'src/views/TeacherDashboard.vue'
with open(filepath, 'r') as f:
    content = f.read()

# Strategy: find and remove all code blocks that are at top level
# but NOT inside any function.
# Top-level code that starts with keywords like 'if', 'for', etc. is orphaned.

lines = content.split('\n')
in_script = False
brace_depth = 0
changes = []
new_lines = []

for i, line in enumerate(lines):
    stripped = line.strip()
    
    # Track script boundaries
    if '<script setup>' in stripped:
        in_script = True
        new_lines.append(line)
        continue
    if '</script>' in stripped:
        in_script = False
        new_lines.append(line)
        continue
    if not in_script:
        new_lines.append(line)
        continue
    
    # Inside script: track brace depth
    prev_depth = brace_depth
    brace_depth += line.count('{') - line.count('}')
    
    # If brace_depth was 0 (top level) and this line starts a statement but isn't a declaration,
    # it might be orphaned code
    if prev_depth == 0 and brace_depth >= 0:
        # Check if this is top-level executable code (not a declaration)
        if (stripped.startswith('if ') or stripped.startswith('for ') or 
            stripped.startswith('while ') or stripped.startswith('switch ') or
            stripped.startswith('try ') or stripped.startswith('try{') or
            stripped.startswith('}') or stripped.startswith('const ') or
            stripped.startswith('let ') or stripped.startswith('var ') or
            stripped.startswith('function ') or stripped.startswith('async function ') or
            stripped.startswith('import ') or stripped.startswith('/*') or
            stripped.startswith('//') or stripped.startswith('*') or
            stripped.startswith('return') or stripped == ''):
            # These are valid top-level constructs
            new_lines.append(line)
        elif stripped.startswith('alert(') or stripped.startswith("alert("):
            # Orphaned alert - skip
            changes.append(f"REMOVED orphan alert at line {i+1}: {stripped[:50]}")
        elif stripped.startswith('loadStudents') or stripped.startswith('loadPtStudents'):
            # Orphaned function call - skip
            changes.append(f"REMOVED orphan call at line {i+1}: {stripped[:50]}")
        elif stripped == '}' and brace_depth < 0:
            # Extra closing brace
            brace_depth = 0
            changes.append(f"REMOVED extra '}}' at line {i+1}")
        else:
            # Could be orphaned code
            changes.append(f"KEPT at line {i+1}: {stripped[:60]}")
            new_lines.append(line)
    else:
        new_lines.append(line)

# Write back
with open(filepath, 'w') as f:
    f.writelines('\n'.join(new_lines) if isinstance(new_lines, list) else '')

print(f"Processed {len(lines)} lines -> {len(new_lines)} lines")
print(f"Changes ({len(changes)}):")
for c in changes:
    print(f"  {c}")
