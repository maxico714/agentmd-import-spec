from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

import yaml


class ProfileError(ValueError):
    code = "E_PROFILE"


@dataclass(frozen=True)
class Profile:
    name: str
    max_depth: int = 32
    max_bytes: int = 1_048_576
    allow_absolute: bool = False
    allow_unc: bool = False
    allow_home: bool = False
    allow_remote: bool = False
    source: str = "project proposal"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "max_depth": self.max_depth,
            "max_bytes": self.max_bytes,
            "allow_absolute": self.allow_absolute,
            "allow_unc": self.allow_unc,
            "allow_home": self.allow_home,
            "allow_remote": self.allow_remote,
            "source": self.source,
        }


_FIELDS = {
    "name": str,
    "max_depth": int,
    "max_bytes": int,
    "allow_absolute": bool,
    "allow_unc": bool,
    "allow_home": bool,
    "allow_remote": bool,
    "source": str,
}


def _from_mapping(data: dict[str, Any], origin: str) -> Profile:
    if not isinstance(data, dict):
        raise ProfileError(f"{origin}: profile root must be a mapping")
    unknown = set(data) - set(_FIELDS)
    if unknown:
        raise ProfileError(f"{origin}: unknown profile keys {sorted(unknown)}")
    values: dict[str, Any] = {}
    for key, kind in _FIELDS.items():
        if key not in data:
            if key in {"name", "max_depth", "max_bytes"}:
                raise ProfileError(f"{origin}: missing required key '{key}'")
            continue
        value = data[key]
        if isinstance(value, bool) and kind is int:
            raise ProfileError(f"{origin}: '{key}' must be an integer")
        if not isinstance(value, kind):
            raise ProfileError(f"{origin}: '{key}' has the wrong type")
        values[key] = value
    if values["max_depth"] < 0:
        raise ProfileError(f"{origin}: max_depth must be non-negative")
    if values["max_bytes"] < 1:
        raise ProfileError(f"{origin}: max_bytes must be positive")
    return Profile(**values)


def builtin(name: str) -> Profile:
    if not name.replace("-", "").replace("_", "").isalnum():
        raise ProfileError(f"invalid profile name '{name}'")
    path = resources.files("agentmd_import").joinpath(f"profiles/{name}.yaml")
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError) as exc:
        raise ProfileError(f"unknown profile '{name}'") from exc
    return _from_mapping(yaml.safe_load(text) or {}, f"profile '{name}'")


def load(value: str) -> Profile:
    candidate = Path(value).expanduser()
    if candidate.is_file():
        try:
            text = candidate.read_text(encoding="utf-8")
        except OSError as exc:
            raise ProfileError(f"cannot read profile '{value}': {exc}") from exc
        try:
            data = yaml.safe_load(text) or {}
        except yaml.YAMLError as exc:
            raise ProfileError(f"invalid YAML in profile '{value}': {exc}") from exc
        return _from_mapping(data, f"profile '{value}'")
    return builtin(value)


def builtin_names() -> list[str]:
    directory = resources.files("agentmd_import").joinpath("profiles")
    return sorted(path.name.removesuffix(".yaml") for path in directory.iterdir())
