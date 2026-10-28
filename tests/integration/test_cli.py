from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

VECTORS = Path(__file__).resolve().parents[2] / "vectors"


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "agentmd_import", *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=60,
    )


def test_resolve_prints_the_order(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("@a.md\n", encoding="utf-8")
    (tmp_path / "a.md").write_text("a\n", encoding="utf-8")
    completed = run("resolve", str(tmp_path / "AGENTS.md"))
    assert completed.returncode == 0
    assert completed.stdout.splitlines() == ["AGENTS.md", "a.md"]
    assert completed.stderr == ""


def test_resolve_reports_errors_on_stderr_and_exits_two(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("@gone.md\n", encoding="utf-8")
    completed = run("resolve", str(tmp_path / "AGENTS.md"))
    assert completed.returncode == 2
    assert completed.stdout.splitlines() == ["AGENTS.md"]
    assert "E_MISSING: gone.md" in completed.stderr


def test_resolve_json_output(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("@a.md\n", encoding="utf-8")
    (tmp_path / "a.md").write_text("a\n", encoding="utf-8")
    completed = run("resolve", str(tmp_path / "AGENTS.md"), "--json")
    data = json.loads(completed.stdout)
    assert data == {
        "root": str(tmp_path / "AGENTS.md"),
        "profile": "strict",
        "order": ["AGENTS.md", "a.md"],
        "errors": [],
    }


def test_resolve_honours_the_profile_flag(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("@a.md\n", encoding="utf-8")
    (tmp_path / "a.md").write_text("@b.md\n", encoding="utf-8")
    (tmp_path / "b.md").write_text("b\n", encoding="utf-8")
    completed = run("resolve", str(tmp_path / "AGENTS.md"), "--profile", "claude-4hop")
    assert completed.returncode == 0
    assert completed.stdout.splitlines() == ["AGENTS.md", "a.md", "b.md"]


def test_unknown_profile_exits_three(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("# empty\n", encoding="utf-8")
    completed = run("resolve", str(tmp_path / "AGENTS.md"), "--profile", "nope")
    assert completed.returncode == 3
    assert "unknown profile" in completed.stderr


def test_verify_shipped_vectors() -> None:
    completed = run("verify", str(VECTORS))
    assert completed.returncode == 0
    assert "27/27 vectors passed" in completed.stdout


def test_verify_json_output() -> None:
    completed = run("verify", str(VECTORS), "--json")
    data = json.loads(completed.stdout)
    assert data["total"] == 27
    assert data["passed"] == 27
    assert data["failures"] == []


def test_verify_failure_exits_one(tmp_path: Path) -> None:
    shutil.copytree(VECTORS / "001-basic-order", tmp_path / "001-basic-order")
    expected_path = tmp_path / "001-basic-order" / "expected.json"
    data = json.loads(expected_path.read_text(encoding="utf-8"))
    data["order"] = ["AGENTS.md"]
    expected_path.write_text(json.dumps(data), encoding="utf-8")
    completed = run("verify", str(tmp_path))
    assert completed.returncode == 1
    assert "FAIL 001-basic-order" in completed.stdout
    assert "0/1 vectors passed" in completed.stdout


def test_verify_missing_directory_exits_three(tmp_path: Path) -> None:
    completed = run("verify", str(tmp_path / "nope"))
    assert completed.returncode == 3
    assert "vectors directory not found" in completed.stderr


def test_profiles_command_lists_builtins() -> None:
    completed = run("profiles")
    assert completed.returncode == 0
    assert completed.stdout.splitlines() == [
        "claude-4hop: max_depth=4",
        "strict: max_depth=32",
    ]


@pytest.mark.skipif(os.name != "nt", reason="Windows character devices are Windows-only")
def test_windows_device_import_fails_closed_without_reading(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("@NUL\n", encoding="utf-8")
    completed = run("resolve", str(tmp_path / "AGENTS.md"))
    assert completed.returncode == 2
    assert "E_PATH" in completed.stderr
    assert "regular file" in completed.stderr


def test_missing_subcommand_is_a_usage_error() -> None:
    completed = run()
    assert completed.returncode == 3
    assert "usage:" in completed.stderr


def test_unknown_flag_is_a_usage_error() -> None:
    completed = run("resolve", "x", "--nope")
    assert completed.returncode == 3


def test_version_flag() -> None:
    completed = run("--version")
    assert completed.returncode == 0
    assert completed.stdout.strip() == "agentmd-import 0.1.0"
