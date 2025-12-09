"""
Create complete component inventory of VaultMind Forge
Extracts all classes, functions, and exports from every module
"""

import ast
import sys
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def extract_from_file(filepath):
    """Extract classes and functions from a Python file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        classes = []
        functions = []
        imports = []
        exports = None

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.FunctionDef):
                # Skip private functions
                if not node.name.startswith('_'):
                    functions.append(node.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
            elif isinstance(node, ast.Assign):
                # Check for __all__
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == '__all__':
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            exports = [elt.s if isinstance(elt, ast.Str) else elt.value
                                      for elt in node.value.elts
                                      if isinstance(elt, (ast.Str, ast.Constant))]

        return {
            'classes': classes,
            'functions': functions,
            'imports': imports,
            'exports': exports
        }
    except Exception as e:
        return {'error': str(e)}


def main():
    print("Scanning VaultMind Forge codebase...")

    vaultmind_root = PROJECT_ROOT / "vaultmind_forge"

    inventory = defaultdict(lambda: defaultdict(dict))

    # Scan all Python files
    for py_file in vaultmind_root.rglob("*.py"):
        if '__pycache__' in str(py_file):
            continue

        rel_path = py_file.relative_to(vaultmind_root)
        module_path = str(rel_path.with_suffix('')).replace('\\', '.')

        info = extract_from_file(py_file)

        if 'error' in info:
            continue

        # Organize by top-level module
        parts = module_path.split('.')
        if len(parts) > 0:
            top_module = parts[0]
            sub_path = '.'.join(parts[1:]) if len(parts) > 1 else '__init__'

            inventory[top_module][sub_path] = info

    # Write inventory
    output_file = PROJECT_ROOT / "COMPONENT_INVENTORY.md"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# VaultMind Forge - Complete Component Inventory\n\n")
        f.write("**Generated**: Automatically scanned codebase\n")
        f.write("**Purpose**: Definitive reference of all modules, classes, and functions\n\n")
        f.write("---\n\n")

        for top_module in sorted(inventory.keys()):
            f.write(f"## {top_module}\n\n")

            for sub_path in sorted(inventory[top_module].keys()):
                info = inventory[top_module][sub_path]

                full_module = f"vaultmind_forge.{top_module}"
                if sub_path != '__init__':
                    full_module += f".{sub_path}"

                f.write(f"### `{full_module}`\n\n")

                # Exports
                if info.get('exports'):
                    f.write(f"**Exports** (`__all__`):\n")
                    for exp in info['exports']:
                        f.write(f"- `{exp}`\n")
                    f.write("\n")

                # Classes
                if info.get('classes'):
                    f.write(f"**Classes**:\n")
                    for cls in info['classes']:
                        f.write(f"- `{cls}`\n")
                    f.write("\n")

                # Functions
                if info.get('functions'):
                    f.write(f"**Functions**:\n")
                    for func in info['functions']:
                        f.write(f"- `{func}()`\n")
                    f.write("\n")

                f.write("---\n\n")

    print(f"Inventory written to: {output_file}")
    print(f"Scanned {sum(len(v) for v in inventory.values())} modules")
    print(f"Top-level modules: {len(inventory)}")


if __name__ == "__main__":
    main()
