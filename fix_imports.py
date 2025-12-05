"""
Quick script to remove sys.path.insert() hacks from all Python files
Part of P0 Task 2: Fix Import System
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

# Files to fix (core modules only, excluding examples and tests)
FILES_TO_FIX = [
    "vaultmind_forge/forge_agents/quality_guardian.py",
    "vaultmind_forge/forge_batch/batch_processor.py",
    "vaultmind_forge/forge_bots/lineage_bot.py",
    "vaultmind_forge/forge_bots/monitor_bot.py",
    "vaultmind_forge/forge_bots/native_bridge.py",
    "vaultmind_forge/forge_bots/optimizer_bot.py",
    "vaultmind_forge/forge_bots/qa_bot.py",
    "vaultmind_forge/forge_bots/scheduler.py",
    "vaultmind_forge/forge_executor/pipeline.py",
    "vaultmind_forge/forge_procedural/billboard_generator.py",
    "vaultmind_forge/forge_procedural/generator.py",
    "vaultmind_forge/forge_validator/ai_validator.py",
    "vaultmind_forge/forge_validator/backends.py",
]

def fix_file(filepath):
    """Remove sys.path.insert() hack from a file"""
    print(f"Fixing: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    removed_count = 0

    for i, line in enumerate(lines):
        # Skip sys.path.insert() lines
        if 'sys.path.insert' in line:
            removed_count += 1
            print(f"  Removed line {i+1}: {line.strip()}")
            continue

        # If line is "import sys" and next line was sys.path.insert, check if sys is used elsewhere
        if line.strip() == 'import sys':
            # Look ahead to see if this was just for sys.path.insert
            if i + 1 < len(lines) and 'sys.path.insert' in lines[i + 1]:
                # Check if 'sys' appears anywhere else in the file
                file_content = ''.join(lines)
                # Remove the two sys lines temporarily
                temp_content = file_content.replace(lines[i], '').replace(lines[i+1], '')
                # Check if sys is still used
                if 'sys.' not in temp_content and 'import sys' not in temp_content:
                    removed_count += 1
                    print(f"  Removed line {i+1}: {line.strip()} (unused)")
                    continue

        new_lines.append(line)

    if removed_count > 0:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print(f"  [OK] Fixed {filepath} ({removed_count} lines removed)")
        return True
    else:
        print(f"  - No changes needed in {filepath}")
        return False

def main():
    print("=" * 60)
    print("IMPORT SYSTEM FIX - Removing sys.path.insert() hacks")
    print("=" * 60)
    print()

    fixed_count = 0
    for filepath in FILES_TO_FIX:
        full_path = PROJECT_ROOT / filepath
        if full_path.exists():
            if fix_file(full_path):
                fixed_count += 1
        else:
            print(f"  ! File not found: {filepath}")
        print()

    print("=" * 60)
    print(f"COMPLETE: Fixed {fixed_count} / {len(FILES_TO_FIX)} files")
    print("=" * 60)

if __name__ == "__main__":
    main()
