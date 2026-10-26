from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .profile import Profile, ProfileError, load
from .resolver import resolve


@dataclass
class VectorFailure:
    vector: str
    detail: str


@dataclass
class VerifyReport:
    directory: str
    total: int = 0
    failures: list[VectorFailure] = field(default_factory=list)

    @property
    def passed(self) -> int:
        return self.total - len(self.failures)

    @property
    def ok(self) -> bool:
        return not self.failures

    def to_dict(self) -> dict[str, object]:
        return {
            "directory": self.directory,
            "total": self.total,
            "passed": self.passed,
            "failures": [
                {"vector": failure.vector, "detail": failure.detail} for failure in self.failures
            ],
        }


def _load_profile(name: str, vector: Path) -> Profile:
    local = vector / name
    if local.is_file():
        return load(str(local))
    return load(name)


def verify(directory: str | Path, profile_name: str | None = None) -> VerifyReport:
    base = Path(directory)
    if not base.is_dir():
        raise FileNotFoundError(f"vectors directory not found: {base}")
    report = VerifyReport(directory=str(base))
    for vector in sorted(path for path in base.iterdir() if path.is_dir()):
        report.total += 1
        problem = _check_vector(vector, profile_name)
        if problem:
            report.failures.append(VectorFailure(vector=vector.name, detail=problem))
    return report


def _check_vector(vector: Path, profile_name: str | None) -> str | None:
    expected_path = vector / "expected.json"
    try:
        expected = json.loads(expected_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return f"cannot read expected.json: {exc}"
    if not isinstance(expected, dict):
        return "expected.json must be an object"
    name = profile_name or str(expected.get("profile", "strict"))
    try:
        profile = _load_profile(name, vector)
    except ProfileError as exc:
        return f"invalid profile: {exc}"
    root = vector / "input" / str(expected.get("root", "AGENTS.md"))
    result = resolve(root, profile)

    problems: list[str] = []
    if "order" in expected and result.order != expected["order"]:
        problems.append(f"order {result.order!r} != expected {expected['order']!r}")
    expected_errors = [
        (str(item.get("rule")), str(item.get("path")))
        for item in expected.get("errors", [])
        if isinstance(item, dict)
    ]
    actual_errors = [(error.rule, error.path) for error in result.errors]
    if actual_errors != expected_errors:
        problems.append(f"errors {actual_errors!r} != expected {expected_errors!r}")
    return "; ".join(problems) or None
