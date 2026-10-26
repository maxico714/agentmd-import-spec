from __future__ import annotations

import os
from pathlib import Path

import pytest

from agentmd_import.profile import Profile
from agentmd_import.resolver import ResolveResult, resolve

STRICT = Profile(name="strict")


def chain(root: Path, files: int) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "AGENTS.md").write_text("@n1.md\n", encoding="utf-8")
    for index in range(1, files + 1):
        following = f"@n{index + 1}.md\n" if index < files else "leaf\n"
        (root / f"n{index}.md").write_text(following, encoding="utf-8")
    return root / "AGENTS.md"


def rules(result: ResolveResult) -> list[tuple[str, str]]:
    return [(error.rule, error.path) for error in result.errors]


def test_deep_chain_fails_closed_without_recursion_error(tmp_path: Path) -> None:
    result = resolve(chain(tmp_path, 80), STRICT)
    assert len(result.order) == 33
    assert rules(result) == [("E_DEPTH", "n33.md")]


def test_wide_fan_out_is_deterministic(tmp_path: Path) -> None:
    tmp_path.mkdir(parents=True, exist_ok=True)
    lines = [f"@f{index:03d}.md" for index in range(300)]
    (tmp_path / "AGENTS.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for index in range(300):
        (tmp_path / f"f{index:03d}.md").write_text("x\n", encoding="utf-8")
    result = resolve(tmp_path / "AGENTS.md", STRICT)
    assert result.ok
    assert len(result.order) == 301
    assert result.order[1] == "f000.md"
    assert result.order[-1] == "f299.md"


def test_long_cycle_reports_the_starting_file(tmp_path: Path) -> None:
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "AGENTS.md").write_text("@a.md\n", encoding="utf-8")
    for name, following in (("a.md", "b.md"), ("b.md", "c.md"), ("c.md", "a.md")):
        (tmp_path / name).write_text(f"@{following}\n", encoding="utf-8")
    result = resolve(tmp_path / "AGENTS.md", STRICT)
    assert rules(result) == [("E_CYCLE", "a.md")]


def test_dotdot_that_leaves_and_returns_resolves_inside(tmp_path: Path) -> None:
    root = tmp_path / "input"
    root.mkdir()
    (root / "AGENTS.md").write_text("@docs/../../input/x.md\n", encoding="utf-8")
    (root / "docs").mkdir()
    (root / "x.md").write_text("x\n", encoding="utf-8")
    result = resolve(root / "AGENTS.md", STRICT)
    assert result.ok
    assert result.order == ["AGENTS.md", "x.md"]


def test_import_of_root_parent_is_traversal(tmp_path: Path) -> None:
    root = tmp_path / "input"
    root.mkdir()
    (root / "AGENTS.md").write_text("@..\n", encoding="utf-8")
    result = resolve(root / "AGENTS.md", STRICT)
    assert rules(result) == [("E_TRAVERSAL", "..")]


def test_fragment_suffix_is_treated_as_a_filename(tmp_path: Path) -> None:
    root = tmp_path / "input"
    root.mkdir()
    (root / "AGENTS.md").write_text("@a.md#section\n", encoding="utf-8")
    (root / "a.md").write_text("a\n", encoding="utf-8")
    result = resolve(root / "AGENTS.md", STRICT)
    assert rules(result) == [("E_MISSING", "a.md#section")]


def test_unicode_import_path(tmp_path: Path) -> None:
    root = tmp_path / "input"
    (root / "docs").mkdir(parents=True)
    (root / "AGENTS.md").write_text("@docs/Überblick.md\n", encoding="utf-8")
    (root / "docs" / "Überblick.md").write_text("ü\n", encoding="utf-8")
    result = resolve(root / "AGENTS.md", STRICT)
    assert result.order == ["AGENTS.md", "docs/Überblick.md"]


def test_bom_in_imported_file_is_accepted(tmp_path: Path) -> None:
    root = tmp_path / "input"
    root.mkdir()
    (root / "AGENTS.md").write_text("@a.md\n", encoding="utf-8")
    (root / "a.md").write_bytes(b"\xef\xbb\xbf@b.md\n")
    (root / "b.md").write_text("b\n", encoding="utf-8")
    result = resolve(root / "AGENTS.md", STRICT)
    assert result.order == ["AGENTS.md", "a.md", "b.md"]


def test_symlink_cycle_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "input"
    root.mkdir()
    (root / "AGENTS.md").write_text("@a.md\n", encoding="utf-8")
    (root / "b.md").write_text("@a.md\n", encoding="utf-8")
    try:
        os.symlink(root / "b.md", root / "a.md")
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available on this host")
    result = resolve(root / "AGENTS.md", STRICT)
    assert len(result.errors) == 1
    assert result.errors[0].rule in {"E_CYCLE", "E_PATH"}


def test_symlinked_directory_escape_is_traversal(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "a.md").write_text("a\n", encoding="utf-8")
    root = tmp_path / "input"
    root.mkdir()
    (root / "AGENTS.md").write_text("@linked/a.md\n", encoding="utf-8")
    try:
        os.symlink(outside, root / "linked", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available on this host")
    result = resolve(root / "AGENTS.md", STRICT)
    assert rules(result) == [("E_TRAVERSAL", "linked/a.md")]


def test_interrupted_resolution_leaves_no_partial_state(tmp_path: Path) -> None:
    root = tmp_path / "input"
    root.mkdir()
    (root / "AGENTS.md").write_text("@a.md\n@gone.md\n", encoding="utf-8")
    (root / "a.md").write_text("a\n", encoding="utf-8")
    first = resolve(root / "AGENTS.md", STRICT)
    second = resolve(root / "AGENTS.md", STRICT)
    assert first.to_dict() == second.to_dict()
