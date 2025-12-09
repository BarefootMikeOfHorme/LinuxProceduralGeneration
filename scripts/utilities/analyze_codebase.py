"""
Codebase Structure Analyzer
Recursive tree analysis of Python/Rust modules, nodes, and components
"""

from pathlib import Path
from collections import defaultdict
import json

class CodebaseAnalyzer:
    def __init__(self, root_path: str):
        self.root = Path(root_path)
        self.stats = {
            'python_modules': [],
            'rust_modules': [],
            'cpp_modules': [],
            'total_lines': 0,
            'by_category': defaultdict(lambda: {'files': 0, 'lines': 0})
        }

    def analyze(self):
        """Recursively analyze codebase structure"""
        print("=" * 80)
        print("VAULTMIND FORGE - CODEBASE ANALYSIS")
        print("=" * 80)
        print()

        # Analyze by category
        categories = {
            'forge_ai': 'AI Backends & LLM Integration',
            'forge_agent': 'Job Planning & Orchestration',
            'forge_agents': 'Specialized AI Agents',
            'forge_diffusion': 'Image Generation (SDXL, etc.)',
            'forge_sr': 'Super Resolution',
            'forge_video': 'Video Generation',
            'forge_3d': '3D Asset Generation',
            'forge_validator': 'Quality Validation',
            'forge_lineage': 'Lineage Tracking',
            'forge_packaging': 'Asset Packaging',
            'forge_monitor': 'System Monitoring',
            'forge_versioning': 'Version Control',
            'forge_cli': 'CLI Interface',
            'forge_converter': 'Format Conversion',
            'forge_procedural': 'Procedural Generation',
            'forge_intake': 'Asset Ingestion',
            'forge_batch': 'Batch Processing',
            'forge_bots': 'Automation Bots',
            'forge_executor': 'Task Execution',
            'forge_semantic': 'Semantic Control',
            'native/cpp': 'C++ Native Modules',
            'native/rust': 'Rust Native Modules',
            'cli': 'Advanced CLI Components',
            'tests': 'Test Suite',
        }

        print("[MODULE BREAKDOWN]")
        print("-" * 80)

        total_py = 0
        total_rs = 0
        total_cpp = 0

        for category, description in categories.items():
            category_path = self.root / 'vaultmind_forge' / category
            if not category_path.exists():
                continue

            # Count files
            py_files = list(category_path.rglob('*.py'))
            rs_files = list(category_path.rglob('*.rs'))
            cpp_files = list(category_path.rglob('*.cpp')) + list(category_path.rglob('*.h'))

            # Count lines
            py_lines = sum(self._count_lines(f) for f in py_files)
            rs_lines = sum(self._count_lines(f) for f in rs_files)
            cpp_lines = sum(self._count_lines(f) for f in cpp_files)

            total_py += len(py_files)
            total_rs += len(rs_files)
            total_cpp += len(cpp_files)

            if py_files or rs_files or cpp_files:
                print(f"\n[{category}] {description}")
                if py_files:
                    print(f"  [PY] Python:  {len(py_files):3d} files  {py_lines:6d} lines")
                if rs_files:
                    print(f"  [RS] Rust:    {len(rs_files):3d} files  {rs_lines:6d} lines")
                if cpp_files:
                    print(f"  [C+] C++:     {len(cpp_files):3d} files  {cpp_lines:6d} lines")

                # List key files
                key_files = [f.name for f in py_files[:5]] + [f.name for f in rs_files[:3]]
                if key_files:
                    print(f"  Key: {', '.join(key_files[:5])}")

        print()
        print("=" * 80)
        print("[SUMMARY STATISTICS]")
        print("=" * 80)
        print(f"Total Python modules:  {total_py}")
        print(f"Total Rust modules:    {total_rs}")
        print(f"Total C++ modules:     {total_cpp}")
        print(f"Total modules:         {total_py + total_rs + total_cpp}")
        print()

        # Potential node types
        print("=" * 80)
        print("[POTENTIAL NODE TYPES - for node editor]")
        print("=" * 80)
        self._suggest_node_types()

        return self.stats

    def _count_lines(self, file_path: Path) -> int:
        """Count non-empty lines in file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return len([line for line in f if line.strip()])
        except:
            return 0

    def _suggest_node_types(self):
        """Suggest node types based on codebase modules"""
        node_categories = {
            'Input Nodes': [
                'Text Prompt Input',
                'Image Reference Input',
                'Style Profile Selector',
                'Asset Loader',
                'Batch Input',
            ],
            'Generation Nodes': [
                'SDXL Generator (forge_diffusion)',
                'Video Generator (forge_video)',
                '3D Mesh Generator (forge_3d)',
                'Procedural Generator (forge_procedural)',
            ],
            'Enhancement Nodes': [
                'Super Resolution (forge_sr)',
                'Semantic Downrez (forge_semantic)',
                'Color Correction',
                'Upscale',
            ],
            'Control Nodes': [
                'ControlNet',
                'IP-Adapter',
                'Palette Lock',
                'Style Transfer',
            ],
            'AI Agent Nodes': [
                'Prompt Refiner (forge_agents)',
                'Parameter Optimizer (forge_agents)',
                'Material Suggester (forge_agents)',
                'Merlinv1 Planner (forge_ai)',
            ],
            'Validation Nodes': [
                'Quality Check (forge_validator)',
                'Anatomy Validator',
                'PBR Validator',
                'Drift Detector',
            ],
            'Processing Nodes': [
                'Format Converter (forge_converter)',
                'Batch Processor (forge_batch)',
                'Asset Packager (forge_packaging)',
            ],
            'Output Nodes': [
                'Save Image',
                'Export to Unreal',
                'Export to Unity',
                'Package Asset Bundle',
                'Lineage Archive (forge_lineage)',
            ],
            'Utility Nodes': [
                'Branch (if/else)',
                'Loop (iterate)',
                'Delay',
                'Cache',
                'Monitor (forge_monitor)',
            ],
        }

        for category, nodes in node_categories.items():
            print(f"\n{category}:")
            for node in nodes:
                print(f"  • {node}")

        print()
        print("[!] These modules can be exposed as drag-and-drop nodes!")
        print()


if __name__ == "__main__":
    analyzer = CodebaseAnalyzer("C:/Users/Administrator/Desktop/Projects/LPG")
    analyzer.analyze()

    print()
    print("=" * 80)
    print("NEXT STEPS FOR NODE EDITOR")
    print("=" * 80)
    print("""
1. Node Graph Core
   - Node base class with inputs/outputs
   - Connection system (type-safe)
   - Execution engine (topological sort)

2. Node Library
   - Wrap each forge_* module as node type
   - Auto-generate from Python introspection
   - Rust/C++ nodes via FFI

3. Visual Editor
   - Web-based UI (React + React Flow?)
   - Terminal UI fallback (textual + rich)
   - Keyboard shortcuts (build as you go)

4. AI Integration
   - Merlinv1 suggests next nodes
   - Auto-complete connections
   - Smart defaults from context
   - Tutorial mode with hints

5. Templates
   - "Anime Character" workflow
   - "Game Asset" workflow
   - "CAD Model" workflow
   - User can save custom templates
    """)
