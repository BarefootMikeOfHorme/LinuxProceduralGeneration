from pathlib import Path

import pytest

from vaultmind_forge.forge_l1 import AL1ScannerError, build_scanner_args


def test_build_scanner_args_uses_configured_binary(tmp_path, monkeypatch):
    binary = tmp_path / "al1scan"
    binary.write_text("test", encoding="utf-8")
    monkeypatch.setenv("LPG_AL1SCAN_BIN", str(binary))

    command = build_scanner_args(tmp_path, ["--summary"], "LPGL1")

    assert command == [str(binary), "--scope", "LPGL1", "--summary", str(tmp_path)]


def test_build_scanner_args_rejects_missing_configured_binary(tmp_path, monkeypatch):
    missing = tmp_path / "missing-al1scan"
    monkeypatch.setenv("LPG_AL1SCAN_BIN", str(missing))

    with pytest.raises(AL1ScannerError, match="LPG_AL1SCAN_BIN"):
        build_scanner_args(tmp_path, ["--summary"])


def test_build_scanner_args_does_not_mutate_operation_arguments(tmp_path, monkeypatch):
    binary = tmp_path / "al1scan"
    binary.write_text("test", encoding="utf-8")
    monkeypatch.setenv("LPG_AL1SCAN_BIN", str(binary))
    operation_args = ["--resolve", "LPG-L1"]

    command = build_scanner_args(tmp_path, operation_args)

    assert command[-3:] == ["--resolve", "LPG-L1", str(tmp_path)]
    assert operation_args == ["--resolve", "LPG-L1"]
