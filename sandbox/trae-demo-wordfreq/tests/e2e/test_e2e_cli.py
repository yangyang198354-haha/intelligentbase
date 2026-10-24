"""E2E tests: full CLI user journeys, real subprocesses only."""
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


@pytest.mark.e2e
def test_e2e_basic_report_and_top_option(tmp_path) -> None:
    """TC-E2E-001 / US-001, US-002 / AC-001-01, AC-002-01."""
    sample = tmp_path / "story.txt"
    sample.write_text(
        "the quick brown fox jumps over the lazy dog the fox", encoding="utf-8"
    )
    first = run_cli(str(sample))
    second = run_cli(str(sample))
    assert first.returncode == 0
    lines = first.stdout.splitlines()
    assert lines[0] == "the\t3"
    assert lines[1] == "fox\t2"
    assert len(lines) == 8
    assert second.stdout == first.stdout

    limited = run_cli(str(sample), "--top", "2")
    assert limited.returncode == 0
    assert limited.stdout.splitlines() == ["the\t3", "fox\t2"]


@pytest.mark.e2e
def test_e2e_case_and_length_journey(tmp_path) -> None:
    """TC-E2E-002 / US-003, US-004 / AC-003-01, AC-003-02, AC-004-01."""
    sample = tmp_path / "mixed.txt"
    sample.write_text("Alpha alpha ALPHA beta gamma", encoding="utf-8")

    plain = run_cli(str(sample))
    assert plain.returncode == 0
    assert plain.stdout.splitlines() == [
        "ALPHA\t1",
        "Alpha\t1",
        "alpha\t1",
        "beta\t1",
        "gamma\t1",
    ]

    folded = run_cli(str(sample), "--ignore-case")
    assert folded.stdout.splitlines() == ["alpha\t3", "beta\t1", "gamma\t1"]

    filtered = run_cli(str(sample), "--ignore-case", "--min-length", "5")
    assert filtered.stdout.splitlines() == ["alpha\t3", "gamma\t1"]


@pytest.mark.e2e
def test_e2e_ordering_and_failure_exit_codes(tmp_path) -> None:
    """TC-E2E-003 / US-005, US-006 / AC-005-01, AC-006-01."""
    sample = tmp_path / "ties.txt"
    sample.write_text("b a b a c", encoding="utf-8")
    ok = run_cli(str(sample))
    assert ok.returncode == 0
    assert ok.stdout.splitlines() == ["a\t2", "b\t2", "c\t1"]

    missing = run_cli(str(tmp_path / "absent.txt"))
    assert missing.returncode == 2
    assert missing.stdout == ""
    assert "wordfreq" in missing.stderr
