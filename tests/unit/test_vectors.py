from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from agentmd_import.vectors import verify

VECTORS = Path(__file__).resolve().parents[2] / "vectors"


def test_shipped_vectors_all_pass() -> None:
    report = verify(VECTORS)
    assert report.total == 27
    assert report.failures == []
    assert report.passed == 27
    assert report.ok


def test_wrong_expected_order_is_reported(tmp_path: Path) -> None:
    shutil.copytree(VECTORS / "001-basic-order", tmp_path / "001-basic-order")
    expected_path = tmp_path / "001-basic-order" / "expected.json"
    data = json.loads(expected_path.read_text(encoding="utf-8"))
    data["order"] = list(reversed(data["order"]))
    expected_path.write_text(json.dumps(data), encoding="utf-8")
    report = verify(tmp_path)
    assert report.total == 1
    assert not report.ok
    assert report.failures[0].vector == "001-basic-order"
    assert "order" in report.failures[0].detail


def test_wrong_expected_error_is_reported(tmp_path: Path) -> None:
    shutil.copytree(VECTORS / "004-missing-file", tmp_path / "004-missing-file")
    expected_path = tmp_path / "004-missing-file" / "expected.json"
    data = json.loads(expected_path.read_text(encoding="utf-8"))
    data["errors"] = [{"rule": "E_CYCLE", "path": "gone.md"}]
    expected_path.write_text(json.dumps(data), encoding="utf-8")
    report = verify(tmp_path)
    assert "E_MISSING" in report.failures[0].detail


def test_profile_override_is_applied(tmp_path: Path) -> None:
    shutil.copytree(VECTORS / "014-claude-depth-limit", tmp_path / "014-claude-depth-limit")
    report = verify(tmp_path, profile_name="strict")
    assert not report.ok


def test_unknown_profile_in_expected_json_is_a_failure(tmp_path: Path) -> None:
    shutil.copytree(VECTORS / "001-basic-order", tmp_path / "001-basic-order")
    expected_path = tmp_path / "001-basic-order" / "expected.json"
    data = json.loads(expected_path.read_text(encoding="utf-8"))
    data["profile"] = "does-not-exist"
    expected_path.write_text(json.dumps(data), encoding="utf-8")
    report = verify(tmp_path)
    assert "invalid profile" in report.failures[0].detail


def test_missing_expected_json_is_a_failure(tmp_path: Path) -> None:
    (tmp_path / "900-empty").mkdir()
    report = verify(tmp_path)
    assert report.failures[0].detail.startswith("cannot read expected.json")


def test_expected_json_must_be_an_object(tmp_path: Path) -> None:
    (tmp_path / "901-list").mkdir()
    (tmp_path / "901-list" / "expected.json").write_text("[]", encoding="utf-8")
    report = verify(tmp_path)
    assert report.failures[0].detail == "expected.json must be an object"


def test_missing_vector_directory_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        verify(tmp_path / "nope")


def test_report_serializes_to_a_dict() -> None:
    data = verify(VECTORS).to_dict()
    assert data["total"] == 27
    assert data["passed"] == 27
    assert data["failures"] == []
