from __future__ import annotations

from pathlib import Path

import pytest

from agentmd_import.profile import Profile, ProfileError, builtin, builtin_names, load


def test_builtin_strict_profile() -> None:
    profile = builtin("strict")
    assert profile.name == "strict"
    assert profile.max_depth == 32
    assert profile.allow_absolute is False
    assert profile.allow_unc is False
    assert profile.allow_home is False
    assert profile.allow_remote is False


def test_builtin_claude_profile() -> None:
    profile = builtin("claude-4hop")
    assert profile.max_depth == 4
    assert profile.allow_absolute is True
    assert "code.claude.com" in profile.source


def test_builtin_names_lists_shipped_profiles() -> None:
    assert builtin_names() == ["claude-4hop", "strict"]


def test_unknown_builtin_profile_raises() -> None:
    with pytest.raises(ProfileError, match="unknown profile"):
        builtin("nope")


def test_profile_name_with_path_separator_is_rejected() -> None:
    with pytest.raises(ProfileError, match="invalid profile name"):
        builtin("../strict")


def test_profile_file_is_loaded_from_path(tmp_path: Path) -> None:
    path = tmp_path / "custom.yaml"
    path.write_text(
        "name: custom\nmax_depth: 1\nmax_bytes: 2048\nallow_absolute: true\n",
        encoding="utf-8",
    )
    profile = load(str(path))
    assert profile == Profile(
        name="custom",
        max_depth=1,
        max_bytes=2048,
        allow_absolute=True,
        source="project proposal",
    )


def test_unknown_boolean_key_is_accepted_but_unknown_keys_are_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("name: x\nmax_depth: 2\nmax_bytes: 10\nsurprise: true\n", encoding="utf-8")
    with pytest.raises(ProfileError, match="unknown profile keys"):
        load(str(path))


def test_missing_required_key_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("max_depth: 2\n", encoding="utf-8")
    with pytest.raises(ProfileError, match="missing required key 'name'"):
        load(str(path))


def test_boolean_is_not_accepted_as_an_integer(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("name: x\nmax_depth: true\nmax_bytes: 10\n", encoding="utf-8")
    with pytest.raises(ProfileError, match="'max_depth' must be an integer"):
        load(str(path))


def test_wrong_type_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        "name: x\nmax_depth: 2\nmax_bytes: 10\nallow_unc: yes-please\n", encoding="utf-8"
    )
    with pytest.raises(ProfileError, match="'allow_unc' has the wrong type"):
        load(str(path))


def test_negative_depth_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("name: x\nmax_depth: -1\nmax_bytes: 10\n", encoding="utf-8")
    with pytest.raises(ProfileError, match="max_depth must be non-negative"):
        load(str(path))


def test_zero_byte_cap_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("name: x\nmax_depth: 1\nmax_bytes: 0\n", encoding="utf-8")
    with pytest.raises(ProfileError, match="max_bytes must be positive"):
        load(str(path))


def test_invalid_yaml_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text("name: [unclosed\n", encoding="utf-8")
    with pytest.raises(ProfileError, match="invalid YAML"):
        load(str(path))


def test_empty_mapping_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "empty.yaml"
    path.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ProfileError, match="missing required key 'name'"):
        load(str(path))


def test_profile_round_trips_to_dict() -> None:
    data = builtin("strict").to_dict()
    assert data["name"] == "strict"
    assert data["max_depth"] == 32
    assert data["allow_remote"] is False
