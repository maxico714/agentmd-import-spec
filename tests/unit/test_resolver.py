from __future__ import annotations

import os
from pathlib import Path

import pytest

from agentmd_import.profile import Profile
from agentmd_import.resolver import ResolveError, ResolveResult, _read, resolve

STRICT = Profile(name="strict")


def build(tmp_path: Path, files: dict[str, str | bytes]) -> Path:
    for rel, content in files.items():
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8", newline="\n")
    return tmp_path / "AGENTS.md"


def plain(tmp_path: Path, files: dict[str, str]) -> Path:
    files.setdefault("AGENTS.md", "# Root\n")
    return build(tmp_path, files)


def rules(result: ResolveResult) -> list[tuple[str, str]]:
    return [(error.rule, error.path) for error in result.errors]


def test_empty_root_resolves_to_itself(tmp_path: Path) -> None:
    result = resolve(plain(tmp_path, {}), STRICT)
    assert result.ok
    assert result.order == ["AGENTS.md"]
    assert result.errors == []


def test_depth_first_document_order(tmp_path: Path) -> None:
    root = plain(
        tmp_path,
        {
            "AGENTS.md": "@a/x.md\n@b/y.md\n",
            "a/x.md": "@z.md\n",
            "a/z.md": "z\n",
            "b/y.md": "y\n",
        },
    )
    result = resolve(root, STRICT)
    assert result.order == ["AGENTS.md", "a/x.md", "a/z.md", "b/y.md"]


def test_paths_use_forward_slashes_in_order(tmp_path: Path) -> None:
    root = plain(tmp_path, {"AGENTS.md": "@docs/a.md\n", "docs/a.md": "a\n"})
    assert resolve(root, STRICT).order == ["AGENTS.md", "docs/a.md"]


def test_duplicate_import_is_reported_once(tmp_path: Path) -> None:
    root = plain(
        tmp_path,
        {"AGENTS.md": "@shared.md\n@other.md\n", "shared.md": "s\n", "other.md": "@shared.md\n"},
    )
    assert resolve(root, STRICT).order == ["AGENTS.md", "shared.md", "other.md"]


def test_equivalent_spellings_resolve_to_one_entry(tmp_path: Path) -> None:
    root = plain(
        tmp_path,
        {"AGENTS.md": "@docs/a.md\n@./docs/../docs/a.md\n", "docs/a.md": "a\n"},
    )
    assert resolve(root, STRICT).order == ["AGENTS.md", "docs/a.md"]


def test_dotdot_inside_root_is_allowed(tmp_path: Path) -> None:
    root = plain(tmp_path, {"AGENTS.md": "@sub/../docs/a.md\n", "docs/a.md": "a\n"})
    result = resolve(root, STRICT)
    assert result.ok
    assert result.order == ["AGENTS.md", "docs/a.md"]


def test_missing_root_is_reported(tmp_path: Path) -> None:
    result = resolve(tmp_path / "missing.md", STRICT)
    assert result.order == []
    assert rules(result) == [("E_MISSING", str(tmp_path / "missing.md"))]


def test_missing_import_is_a_hard_error(tmp_path: Path) -> None:
    root = plain(tmp_path, {"AGENTS.md": "@sub/gone.md\n"})
    result = resolve(root, STRICT)
    assert not result.ok
    assert result.order == ["AGENTS.md"]
    assert rules(result) == [("E_MISSING", "sub/gone.md")]


def test_import_of_a_directory_is_a_path_error(tmp_path: Path) -> None:
    root = plain(tmp_path, {"AGENTS.md": "@dir\n"})
    (tmp_path / "dir").mkdir()
    result = resolve(root, STRICT)
    assert rules(result) == [("E_PATH", "dir")]


def test_direct_cycle_is_reported_with_the_cycle_path(tmp_path: Path) -> None:
    root = plain(
        tmp_path,
        {"AGENTS.md": "@a.md\n", "a.md": "@b.md\n", "b.md": "@a.md\n"},
    )
    result = resolve(root, STRICT)
    assert result.order == ["AGENTS.md", "a.md", "b.md"]
    assert rules(result) == [("E_CYCLE", "a.md")]
    assert "AGENTS.md -> a.md -> b.md -> a.md" in result.errors[0].detail


def test_self_cycle_is_reported(tmp_path: Path) -> None:
    root = plain(tmp_path, {"AGENTS.md": "@a.md\n", "a.md": "@a.md\n"})
    result = resolve(root, STRICT)
    assert rules(result) == [("E_CYCLE", "a.md")]


def test_traversal_out_of_root_is_rejected(tmp_path: Path) -> None:
    outside = tmp_path / "outside.md"
    outside.write_text("outside\n", encoding="utf-8")
    root = plain(tmp_path / "input", {"AGENTS.md": "@../outside.md\n"})
    result = resolve(root, STRICT)
    assert result.order == ["AGENTS.md"]
    assert rules(result) == [("E_TRAVERSAL", "../outside.md")]


@pytest.mark.parametrize(
    "directive",
    ["@/etc/passwd", "@/tmp/agents.md"],
)
def test_absolute_paths_are_rejected_by_strict(tmp_path: Path, directive: str) -> None:
    root = plain(tmp_path, {"AGENTS.md": directive + "\n"})
    assert rules(resolve(root, STRICT)) == [("E_PATH", directive[1:])]


@pytest.mark.parametrize("raw", [r"\\server\share\a.md", "//server/share/a.md"])
def test_unc_paths_are_rejected_by_strict(tmp_path: Path, raw: str) -> None:
    root = plain(tmp_path, {"AGENTS.md": "@" + raw + "\n"})
    assert rules(resolve(root, STRICT)) == [("E_PATH", raw)]


def test_windows_drive_path_is_rejected_by_strict(tmp_path: Path) -> None:
    raw = r"C:\temp\agents.md"
    root = plain(tmp_path, {"AGENTS.md": "@" + raw + "\n"})
    assert rules(resolve(root, STRICT)) == [("E_PATH", raw)]


def test_home_path_is_rejected_by_strict(tmp_path: Path) -> None:
    root = plain(tmp_path, {"AGENTS.md": "@~/notes.md\n"})
    assert rules(resolve(root, STRICT)) == [("E_PATH", "~/notes.md")]


@pytest.mark.parametrize(
    "raw",
    ["https://example.com/agents.md", "ssh://host/repo/a.md", "git+ssh://host/a.md"],
)
def test_remote_imports_are_rejected(tmp_path: Path, raw: str) -> None:
    root = plain(tmp_path, {"AGENTS.md": "@" + raw + "\n"})
    assert rules(resolve(root, STRICT)) == [("E_REMOTE", raw)]


def test_remote_imports_are_not_implemented_even_when_allowed(tmp_path: Path) -> None:
    profile = Profile(name="open", allow_remote=True)
    root = plain(tmp_path, {"AGENTS.md": "@https://example.com/agents.md\n"})
    errors = resolve(root, profile).errors
    assert errors[0].rule == "E_REMOTE"
    assert "not implemented" in errors[0].detail


def test_absolute_import_inside_root_is_allowed_by_claude_profile(tmp_path: Path) -> None:
    target = tmp_path / "docs" / "a.md"
    target.parent.mkdir()
    target.write_text("a\n", encoding="utf-8")
    root = plain(tmp_path, {"AGENTS.md": "@" + target.as_posix() + "\n"})
    profile = Profile(name="claude", allow_absolute=True)
    result = resolve(root, profile)
    assert result.ok
    assert result.order == ["AGENTS.md", "docs/a.md"]


def test_absolute_import_outside_root_is_still_traversal(tmp_path: Path) -> None:
    outside = tmp_path / "outside" / "a.md"
    outside.parent.mkdir()
    outside.write_text("a\n", encoding="utf-8")
    root = plain(tmp_path / "input", {"AGENTS.md": "@" + outside.as_posix() + "\n"})
    profile = Profile(name="claude", allow_absolute=True)
    result = resolve(root, profile)
    assert result.errors[0].rule == "E_TRAVERSAL"


def test_depth_limit_counts_hops_from_the_root(tmp_path: Path) -> None:
    root = plain(
        tmp_path,
        {
            "AGENTS.md": "@a.md\n",
            "a.md": "@b.md\n",
            "b.md": "@c.md\n",
            "c.md": "leaf\n",
        },
    )
    profile = Profile(name="two", max_depth=2)
    result = resolve(root, profile)
    assert result.order == ["AGENTS.md", "a.md", "b.md"]
    assert rules(result) == [("E_DEPTH", "c.md")]


def test_zero_depth_rejects_the_first_import(tmp_path: Path) -> None:
    root = plain(tmp_path, {"AGENTS.md": "@a.md\n", "a.md": "a\n"})
    result = resolve(root, Profile(name="zero", max_depth=0))
    assert result.order == ["AGENTS.md"]
    assert rules(result) == [("E_DEPTH", "a.md")]


def test_syntax_error_stops_resolution(tmp_path: Path) -> None:
    root = plain(tmp_path, {"AGENTS.md": "# Root\n@a.md extra\n", "a.md": "a\n"})
    result = resolve(root, STRICT)
    assert result.order == ["AGENTS.md"]
    assert rules(result) == [("E_SYNTAX", "AGENTS.md")]
    assert result.errors[0].line == 2


def test_invalid_utf8_is_a_hard_error(tmp_path: Path) -> None:
    root = build(tmp_path, {"AGENTS.md": b"@a.md\n", "a.md": b"\xffnot utf-8\n"})
    result = resolve(root, STRICT)
    assert result.order == ["AGENTS.md"]
    assert rules(result) == [("E_ENCODING", "a.md")]


def test_bom_is_accepted(tmp_path: Path) -> None:
    root = build(tmp_path, {"AGENTS.md": b"\xef\xbb\xbf@a.md\n", "a.md": b"a\n"})
    assert resolve(root, STRICT).order == ["AGENTS.md", "a.md"]


def test_size_cap_is_enforced(tmp_path: Path) -> None:
    root = plain(tmp_path, {"AGENTS.md": "# Root\n", "a.md": "0123456789\n"})
    result = resolve(root, Profile(name="tiny", max_bytes=5))
    assert result.order == []
    assert rules(result) == [("E_SIZE", "AGENTS.md")]


def test_nul_byte_in_directive_is_a_path_error(tmp_path: Path) -> None:
    root = plain(tmp_path, {"AGENTS.md": "@a\x00b.md\n"})
    result = resolve(root, STRICT)
    assert result.errors[0].rule == "E_PATH"
    assert "NUL" in result.errors[0].detail


def test_result_serializes_to_a_dict(tmp_path: Path) -> None:
    root = plain(tmp_path, {"AGENTS.md": "@a.md\n", "a.md": "@gone.md\n"})
    data = resolve(root, STRICT).to_dict()
    assert data["root"] == str(root)
    assert data["profile"] == "strict"
    assert data["order"] == ["AGENTS.md", "a.md"]
    assert data["errors"] == [
        {
            "rule": "E_MISSING",
            "path": "gone.md",
            "detail": "imported file does not exist",
            "file": None,
            "line": None,
        }
    ]


def test_symlink_escape_is_traversal(tmp_path: Path) -> None:
    outside = tmp_path / "outside.md"
    outside.write_text("outside\n", encoding="utf-8")
    root = plain(tmp_path / "input", {"AGENTS.md": "@link.md\n"})
    link = tmp_path / "input" / "link.md"
    try:
        os.symlink(outside, link)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available on this host")
    assert rules(resolve(root, STRICT)) == [("E_TRAVERSAL", "link.md")]


def test_directory_is_not_a_regular_file(tmp_path: Path) -> None:
    (tmp_path / "sub").mkdir()
    with pytest.raises(ResolveError) as excinfo:
        _read(tmp_path / "sub", tmp_path, STRICT)
    assert excinfo.value.rule == "E_PATH"
    assert "regular file" in excinfo.value.detail


def test_size_cap_is_enforced_while_reading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "a.md"
    target.write_bytes(b"x" * 11)
    profile = Profile(name="tiny", max_bytes=10)
    real_stat = Path.stat

    def small_stat(self: Path, *args: object, **kwargs: object) -> os.stat_result:
        info = real_stat(self, *args, **kwargs)  # type: ignore[arg-type]
        if self == target:
            return os.stat_result(
                (
                    info.st_mode,
                    info.st_ino,
                    info.st_dev,
                    info.st_nlink,
                    info.st_uid,
                    info.st_gid,
                    1,
                    info.st_atime,
                    info.st_mtime,
                    info.st_ctime,
                )
            )
        return info

    monkeypatch.setattr(Path, "stat", small_stat)
    with pytest.raises(ResolveError) as excinfo:
        _read(target, tmp_path, profile)
    assert excinfo.value.rule == "E_SIZE"
    assert "max_bytes=10" in excinfo.value.detail
