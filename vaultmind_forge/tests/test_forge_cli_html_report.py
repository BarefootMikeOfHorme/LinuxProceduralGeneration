"""Regression tests for the --html-report path.

Two defects are covered here.

The `forge_cli.py` module and the `forge_cli/` directory had the same name.
Python resolved the module, which has no `__path__`, so
`vaultmind_forge.forge_cli.html_report` was unreachable and the `--html-report`
flag raised ModuleNotFoundError. The report module now lives at
`vaultmind_forge.forge_cli_html_report`. The first test pins that it is
importable and is a real module, which is what the flag depends on.

The report template formatted `diagnostics[...]['ms']` unconditionally. Any
diagnostic without a `ms` key raised UndefinedError from inside Jinja's format
filter, and the whole HTML file was lost rather than partially written. The
template now renders `n/a` for a missing or non-numeric timing. The second test
pins both the missing-`ms` and the present-`ms` paths so the fix cannot silently
drop the numeric formatting that was already working.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest

REPORTS = [
    {
        "pass": 1,
        "status": "ok",
        "metrics": {"anatomy": 0.91, "sharpness": 0.77},
        "issues": [],
        "remedies": [],
    },
    {
        "pass": 2,
        "status": "ok",
        "metrics": {"anatomy": 0.88},
        "issues": [{"issue": "soft edges", "prescription": "raise sample count"}],
        "remedies": [],
    },
]


def test_html_report_module_is_importable_as_a_module():
    """The --html-report path must be reachable.

    This fails if the report code is ever moved back under a `forge_cli/`
    directory, because `forge_cli.py` shadows that name and has no __path__.
    """
    module = importlib.import_module("vaultmind_forge.forge_cli_html_report")
    assert callable(module.write_html_report)

    # forge_cli itself must remain the module, not a package, for the above to
    # hold. Assert the shape so a future refactor notices the constraint.
    forge_cli = importlib.import_module("vaultmind_forge.forge_cli")
    assert not hasattr(forge_cli, "__path__"), (
        "forge_cli became a package; vaultmind_forge.forge_cli_html_report and "
        "the console script entry point would need re-checking"
    )
    assert not (Path(forge_cli.__file__).parent / "forge_cli").exists(), (
        "a forge_cli/ directory has reappeared and will shadow forge_cli.py"
    )


def test_html_report_renders_when_diagnostic_has_no_timing(tmp_path: Path):
    """A diagnostic without 'ms' must not abort the whole report."""
    from vaultmind_forge.forge_cli_html_report import write_html_report

    diagnostics = {"gate": {"backend": "rules", "ok": True}}
    path = Path(write_html_report("no-timing", REPORTS, diagnostics, tmp_path))

    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "<html" in text.lower()
    assert "no-timing" in text
    assert "n/a" in text, "a missing timing should render as n/a, not crash"


def test_html_report_formats_numeric_timing(tmp_path: Path):
    """The numeric timing path must keep working after the template change."""
    from vaultmind_forge.forge_cli_html_report import write_html_report

    diagnostics = {"gate": {"backend": "rules", "ok": True, "ms": 12.345}}
    path = Path(write_html_report("with-timing", REPORTS, diagnostics, tmp_path))

    text = path.read_text(encoding="utf-8")
    assert "12.3 ms" in text, "numeric timing formatting regressed to n/a"


def test_html_report_creates_missing_output_directory(tmp_path: Path):
    """The report directory is created on demand rather than assumed."""
    from vaultmind_forge.forge_cli_html_report import write_html_report

    target = tmp_path / "nested" / "reports"
    assert not target.exists()

    path = Path(write_html_report("mk-dirs", REPORTS, {}, target))
    assert path.is_file()
    assert path.parent == target
