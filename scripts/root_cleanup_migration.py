#!/usr/bin/env python3
"""
Root Directory Cleanup - Automated Migration Script
Organizes 51 root files into proper docs/ structure
"""

import os
import shutil
import re
from pathlib import Path
from typing import Dict, List

class RootCleanupMigration:
    def __init__(self, repo_root: str, dry_run: bool = True):
        self.repo_root = Path(repo_root)
        self.dry_run = dry_run
        self.migrations = []

    def create_directory_structure(self):
        """Create new directory structure"""
        directories = [
            'docs/api',
            'docs/guides',
            'docs/architecture',
            'docs/components',
            'docs/development',
            'docs/reports',
            'docs/consolidation',
            'scripts/tests'
        ]

        print("Creating directory structure...")
        for dir_path in directories:
            full_path = self.repo_root / dir_path
            if self.dry_run:
                print(f"  [DRY RUN] Would create: {dir_path}")
            else:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"  [+] Created: {dir_path}")

    def define_migrations(self) -> Dict[str, List[tuple]]:
        """Define file migration mappings"""
        return {
            'docs/api': [
                ('NODE_API_README.md', 'NODE_API_README.md'),
                ('NODE_API_SUMMARY.md', 'NODE_API_SUMMARY.md'),
                ('QUICKSTART_NODE_API.md', 'QUICKSTART_NODE_API.md'),
            ],
            'docs/guides': [
                ('BUILD_NATIVE.md', 'BUILD_NATIVE.md'),
                ('DOCS_QUICK_NAV.md', 'QUICK_NAV.md'),  # Rename
                ('UTILS_GUIDE.md', 'UTILS_GUIDE.md'),
                ('INTERACTIVE_TUTORIAL.md', 'INTERACTIVE_TUTORIAL.md'),
                ('FORGE_CONVERTER_INTEGRATION_GUIDE.md', 'FORGE_CONVERTER_INTEGRATION_GUIDE.md'),
            ],
            'docs/architecture': [
                ('VAULTMIND_FORGE_PIPELINE.md', 'VAULTMIND_FORGE_PIPELINE.md'),
                ('PROCEDURAL_GENERATION_OVERVIEW.md', 'PROCEDURAL_GENERATION_OVERVIEW.md'),
                ('PROCEDURAL_ASSET_PIPELINE.md', 'PROCEDURAL_ASSET_PIPELINE.md'),
                ('FORGE_CONVERTER_DESIGN.md', 'FORGE_CONVERTER_DESIGN.md'),
                ('AI_CONTROL_FRAMEWORK.md', 'AI_CONTROL_FRAMEWORK.md'),
                ('PROJECT_CONTEXT_COMPACT.md', 'PROJECT_CONTEXT_COMPACT.md'),
                ('ASSET_REFERENCE_CATALOG.md', 'ASSET_REFERENCE_CATALOG.md'),
            ],
            'docs/components': [
                ('LINEAGE_VIEWER_DOCS.md', 'LINEAGE_VIEWER_DOCS.md'),
                ('LINEAGE_VIEWER_SUMMARY.md', 'LINEAGE_VIEWER_SUMMARY.md'),
            ],
            'docs/development': [
                ('INDUSTRY_STANDARDS_ANALYSIS.md', 'INDUSTRY_STANDARDS_ANALYSIS.md'),
                ('INTEGRATION_AUDIT.md', 'INTEGRATION_AUDIT.md'),
                ('NATIVE_HANDLER_EVALUATION.md', 'NATIVE_HANDLER_EVALUATION.md'),
                ('PROCEDURAL_LIBRARY_ANALYSIS.md', 'PROCEDURAL_LIBRARY_ANALYSIS.md'),
                ('VALIDATOR_ENHANCEMENTS.md', 'VALIDATOR_ENHANCEMENTS.md'),
                ('UTILS_AMENDMENTS.md', 'UTILS_AMENDMENTS.md'),
                ('VAULTMIND_FORGE_CURSOR_PROMPT.md', 'VAULTMIND_FORGE_CURSOR_PROMPT.md'),
            ],
            'docs/reports': [
                ('STATE_OF_PROGRAM_REPORT.md', 'STATE_OF_PROGRAM_REPORT.md'),
                ('DOCS_STATUS.md', 'DOCS_STATUS.md'),
                ('SESSION_SUMMARY.md', 'SESSION_SUMMARY.md'),
                ('FORGE_DIFFUSION_SUMMARY.md', 'FORGE_DIFFUSION_SUMMARY.md'),
                ('ASSET_CONVERTER_SUMMARY.md', 'ASSET_CONVERTER_SUMMARY.md'),
            ],
            'docs/consolidation': [
                ('MERGE_REPORT.md', 'MERGE_REPORT.md'),
                ('CONSOLIDATION_COMPLETE.md', 'CONSOLIDATION_COMPLETE.md'),
                ('ARCHIVE_MANIFEST.json', 'ARCHIVE_MANIFEST.json'),
                ('REPO_INVENTORY.json', 'REPO_INVENTORY.json'),
                ('SIMILARITY_MAP.json', 'SIMILARITY_MAP.json'),
                ('nested_package_manifest.json', 'nested_package_manifest.json'),
                ('executor_deprecation_manifest.json', 'executor_deprecation_manifest.json'),
                ('milestone_reports_manifest.json', 'milestone_reports_manifest.json'),
                ('ROOT_CLEANUP_PLAN.md', 'ROOT_CLEANUP_PLAN.md'),
            ],
            'scripts': [
                ('consolidation_script.py', 'consolidation_script.py'),
                ('BACKEND.py', 'BACKEND.py'),
                ('CMakeSettings.json', 'CMakeSettings.json'),
            ],
            'scripts/tests': [
                ('test_async_dag.py', 'test_async_dag.py'),
                ('test_forge_converter.py', 'test_forge_converter.py'),
                ('test_optimization_math.py', 'test_optimization_math.py'),
                ('test_pipeline_paths.py', 'test_pipeline_paths.py'),
            ],
        }

    def migrate_files(self):
        """Execute file migrations"""
        migrations = self.define_migrations()
        total_files = sum(len(files) for files in migrations.values())

        print(f"\nMigrating {total_files} files...")
        migrated = 0

        for destination, file_list in migrations.items():
            print(f"\n{destination}:")
            for source_name, dest_name in file_list:
                source_path = self.repo_root / source_name
                dest_path = self.repo_root / destination / dest_name

                if not source_path.exists():
                    print(f"  [SKIP] {source_name} (not found)")
                    continue

                if self.dry_run:
                    print(f"  [DRY RUN] {source_name} -> {destination}/{dest_name}")
                else:
                    shutil.move(str(source_path), str(dest_path))
                    print(f"  [>>] {source_name} -> {destination}/{dest_name}")

                self.migrations.append({
                    'source': str(source_path),
                    'destination': str(dest_path),
                    'old_path': source_name,
                    'new_path': f"{destination}/{dest_name}"
                })
                migrated += 1

        print(f"\nMigrated: {migrated}/{total_files} files")
        return migrated

    def update_documentation_links(self):
        """Update links in key documentation files"""
        print("\nUpdating documentation links...")

        # Files to update with their link patterns
        docs_to_update = {
            'README.md': [
                (r'\[DOCS_QUICK_NAV\.md\]', '[docs/guides/QUICK_NAV.md]'),
                (r'\[DOCUMENTATION\.md\]', '[DOCUMENTATION.md]'),  # Keep in root
                (r'\[QUICK_START\.md\]', '[QUICK_START.md]'),  # Keep in root
            ],
            'DOCUMENTATION.md': self._generate_doc_link_updates(),
        }

        for doc_file, replacements in docs_to_update.items():
            doc_path = self.repo_root / doc_file
            if not doc_path.exists():
                continue

            if self.dry_run:
                print(f"  [DRY RUN] Would update links in {doc_file}")
                continue

            content = doc_path.read_text(encoding='utf-8')
            original = content

            for pattern, replacement in replacements:
                content = re.sub(pattern, replacement, content)

            if content != original:
                doc_path.write_text(content, encoding='utf-8')
                print(f"  [+] Updated: {doc_file}")
            else:
                print(f"  [-] No changes: {doc_file}")

    def _generate_doc_link_updates(self) -> List[tuple]:
        """Generate comprehensive link updates for DOCUMENTATION.md"""
        updates = []
        migrations = self.define_migrations()

        for destination, file_list in migrations.items():
            for source_name, dest_name in file_list:
                if source_name.endswith('.md'):
                    # Update markdown links
                    old_link = f'\\[{source_name}\\]\\(\\./{source_name}\\)'
                    new_link = f'[{source_name}](./{destination}/{dest_name})'
                    updates.append((old_link, new_link))

        return updates

    def generate_migration_report(self):
        """Generate migration report"""
        from datetime import datetime
        report = f"""# Root Directory Cleanup - Migration Report

Generated: {datetime.now().isoformat()}
Mode: {'DRY RUN' if self.dry_run else 'EXECUTED'}

## Summary

- Total files migrated: {len(self.migrations)}
- Directories created: 8

## File Migrations

"""
        for migration in self.migrations:
            report += f"- `{migration['old_path']}` → `{migration['new_path']}`\n"

        report += """

## Root Directory After Migration

Essential files remaining:
- README.md
- LICENSE.md
- CONTRIBUTING.md
- CHANGELOG.md
- QUICK_START.md
- DOCUMENTATION.md
- package.json (if exists)
- .gitignore (if exists)
- pyproject.toml (if exists)
- requirements.txt (if exists)

**Total: ~10 files (down from 51)**

## Next Steps

1. Verify all links work in documentation
2. Test examples/tests still function
3. Update DOCUMENTATION.md master index
4. Commit changes with: `git add . && git commit -m "Organize root directory into docs/ structure"`

"""

        report_path = self.repo_root / 'docs' / 'consolidation' / 'ROOT_MIGRATION_REPORT.md'

        if self.dry_run:
            print("\n=== MIGRATION REPORT (DRY RUN) ===")
            print(report)
        else:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(report, encoding='utf-8')
            print(f"\n[+] Migration report: {report_path}")

    def run(self, option: str = 'A'):
        """Execute migration"""
        print(f"=== ROOT DIRECTORY CLEANUP ===")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE EXECUTION'}")
        print(f"Option: {option}\n")

        if option == 'A':
            # Full cleanup
            self.create_directory_structure()
            self.migrate_files()
            self.update_documentation_links()
            self.generate_migration_report()
        elif option == 'B':
            # Partial cleanup - only consolidation and scripts
            print("Option B: Partial cleanup (consolidation + scripts only)")
            # TODO: Implement partial migration
        elif option == 'C':
            # Minimal cleanup - only manifests
            print("Option C: Minimal cleanup (manifests only)")
            # TODO: Implement minimal migration

        print("\n=== MIGRATION COMPLETE ===")
        if self.dry_run:
            print("\nThis was a DRY RUN. No files were moved.")
            print("To execute for real, run: python root_cleanup_migration.py --execute")


if __name__ == "__main__":
    import sys

    dry_run = '--execute' not in sys.argv
    option = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in ['A', 'B', 'C'] else 'A'

    migrator = RootCleanupMigration(
        repo_root=r"C:\Users\Administrator\Desktop\Projects\LPG",
        dry_run=dry_run
    )

    migrator.run(option=option)
