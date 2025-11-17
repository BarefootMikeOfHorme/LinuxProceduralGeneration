#!/usr/bin/env python3
"""
Batch fix Unicode symbols for Windows cp1252 compatibility
"""

import re
from pathlib import Path

# Replacement mappings
REPLACEMENTS = {
    '[OK]': '[OK]',
    '[X]': '[X]',
    '[WARN]': '[WARN]',
    '[FAIL]': '[FAIL]',
    '[OK]': '[OK]',
}

# Files to fix
FILES_TO_FIX = [
    'vaultmind_forge/cli/distributed_executor.py',
    'vaultmind_forge/cli/multi_modal_pipeline.py',
    'vaultmind_forge/examples/bot_deployment_example.py',
    'vaultmind_forge/forge_agent/planner.py',
   'vaultmind_forge/forge_agents/quality_guardian.py',
]

def fix_file(filepath):
    """Fix Unicode symbols in a single file"""
    path = Path(filepath)
    if not path.exists():
        print(f"Skipping {filepath} (not found)")
        return False

    content = path.read_text(encoding='utf-8')
    original = content

    for unicode_char, replacement in REPLACEMENTS.items():
        content = content.replace(unicode_char, replacement)

    if content != original:
        path.write_text(content, encoding='utf-8')
        print(f"Fixed: {filepath}")
        return True
    else:
        print(f"No changes: {filepath}")
        return False

def main():
    """Main execution"""
    print("Fixing Unicode symbols for Windows compatibility...\n")

    fixed_count = 0
    for filepath in FILES_TO_FIX:
        if fix_file(filepath):
            fixed_count += 1

    print(f"\nFixed {fixed_count}/{len(FILES_TO_FIX)} files")

if __name__ == '__main__':
    main()
