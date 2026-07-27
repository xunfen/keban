#!/usr/bin/env python3
"""Remove ALL orphaned code blocks to fix missing bindings."""
import re

filepath = 'src/views/TeacherDashboard.vue'
with open(filepath, 'r') as f:
    content = f.read()

# Strategy: Find ALL occurrences of orphaned batch operation patterns
# and remove ALL of them. Keep ONLY patterns that are properly inside
# a function declaration.

# Find all locations of orphaned patterns
patterns_to_remove = []

# Pattern: orphaned if (selectedStuIds... block
# These appear outside any function definition
# They start with "if (selectedStuIds.value.length === 0)" or "if (!confirm(`确定删除"

# Let me find ALL blocks that are between the last proper function's '}'
# and the 'const teacherMsgs' declaration

# Find the resetStuPw function end
# Find batchDeleteStu function start
# Find teacherMsgs

# Strategy: mark orphaned sections by finding code blocks that are
# NOT preceded by a 'function' keyword within the same brace depth

lines = content.split('\n')
script_start = -1
script_end = -1
for i, line in enumerate(lines):
    if '<script setup>' in line:
        script_start = i
    if '</script>' in line and i > script_start:
        script_end = i
        break

print(f"Script: lines {script_start+1}-{script_end+1}")

# Check for orphaned code in the script section
in_script = False
brace_depth = 0
in_orphan = False
orphan_lines = []
for i, line in enumerate(lines):
    stripped = line.strip()
    
    if '<script setup>' in stripped:
        in_script = True
        continue
    if '</script>' in stripped:
        in_script = False
        continue
    if not in_script:
        continue
    
    # Track brace depth
    brace_depth += line.count('{') - line.count('}')
    
    # At top level (brace_depth <= 0 after counting this line's braces)
    # Check if this is a valid top-level declaration
    is_decl = bool(re.match(r'^(const|let|var|function |async function |import |/\*|//|\*|$)', stripped))
    
    # A line at top level that isn't a declaration and isn't a comment is orphaned
    if brace_depth == 0 and stripped and not is_decl and not stripped.startswith('}') and not in_script:
        orphan_lines.append(f"  L{i+1}: {stripped[:60]} (depth was {brace_depth})")

print(f"\nPotential orphaned lines ({len(orphan_lines)}):")
for l in orphan_lines:
    print(l)

# Now find all lines that contain orphaned batch operation code
# by scanning for patterns that should only exist inside functions

orphaned_blocks = []
for i, line in enumerate(lines):
    s = line.strip()
    # Mark lines with these patterns as potential orphan targets
    if ('selectedStuIds.value.length === 0' in s or 
        s.startswith('if (!confirm(`确定删除') or
        (s.startswith('if (!newPw') and 'length < 4' in s) or
        s.startswith('if (d && d.ok)') or
        s.startswith("alert(`✅ 删除") or
        s.startswith("alert(`✅ 密码已重置")):
        orphaned_blocks.append(i+1)

print(f"\nLines with orphan-prone patterns: {orphaned_blocks}")
