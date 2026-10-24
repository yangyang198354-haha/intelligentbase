"""Integration tests: MOD-002 CLI <-> MOD-001 core through a real subprocess."""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

import pytest

PROJECT = pathlib.Path(__file__).resolve().parents[2]
SRC = PROJECT / "src"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "wordfreq", *args],
        cwd=SRC,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=30,
    )


@pytest.mark.integration
def test_cli_top_n_and_default_sorting(tmp_path) -> None:
    """TC-INT-001 / AC-002-01（含 AC-001-01 基础输出）."""
    sample = tmp_path / "five.txt"
    sample.write_text("e d c b a", encoding="utf-8")
    result = run_cli(str(sample), "--top", "2")
    assert result.returncode == 0
    assert result.stdout.splitlines() == ["a\t1", "b\t1"]
    assert result.stderr == ""


@pytest.mark.integration
def test_cli_case_and_length_options_combine(tmp_path) -> None:
    """TC-INT-002 / AC-003-01, AC-004-01."""
    sample = tmp_path / "mixed.txt"
    sample.write_text("Alpha alpha ALPHA beta gamma", encoding="utf-8")
    result = run_cli(str(sample), "--ignore-case", "--min-length", "5")
    assert result.returncode == 0
    assert result.stdout.splitlines() == ["alpha\t3", "gamma\t1"]


@pytest.mark.integration
def test_cli_missing_file_exits_2(tmp_path) -> None:
    """TC-INT-003 / AC-006-01."""
    result = run_cli(str(tmp_path / "nope.txt"))
    assert result.returncode == 2
    assert result.stdout == ""
    assert "wordfreq" in result.stderr


@pytest.mark.integration
def test_cli_directory_and_bad_utf8_exit_2(tmp_path) -> None:
    """TC-INT-004 / AC-006-02, AC-007-01."""
    directory = run_cli(str(tmp_path))
    assert directory.returncode == 2
    assert directory.stdout == ""
    assert directory.stderr.strip()

    bad = tmp_path / "bad.txt"
    bad.write_bytes(b"a\xff\xfeb")
    invalid = run_cli(str(bad))
    assert invalid.returncode == 2
    assert invalid.stdout == ""
    assert invalid.stderr.strip()
