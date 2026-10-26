from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .parser import SyntaxIssue, parse
from .profile import Profile

_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")
_DRIVE = re.compile(r"^[A-Za-z]:")


class ResolveError(Exception):
    def __init__(
        self,
        rule: str,
        path: str,
        detail: str,
        file: str | None = None,
        line: int | None = None,
    ) -> None:
        super().__init__(detail)
        self.rule = rule
        self.path = path
        self.detail = detail
        self.file = file
        self.line = line

    def to_dict(self) -> dict[str, object]:
        return {
            "rule": self.rule,
            "path": self.path,
            "detail": self.detail,
            "file": self.file,
            "line": self.line,
        }


@dataclass
class ResolveResult:
    root: str
    profile: str
    order: list[str] = field(default_factory=list)
    errors: list[ResolveError] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, object]:
        return {
            "root": self.root,
            "profile": self.profile,
            "order": list(self.order),
            "errors": [error.to_dict() for error in self.errors],
        }


def resolve(root: str | Path, profile: Profile) -> ResolveResult:
    result = ResolveResult(root=str(root), profile=profile.name)
    path = Path(root).expanduser()
    try:
        resolved_root = path.resolve(strict=True)
    except FileNotFoundError:
        result.errors.append(ResolveError("E_MISSING", str(root), "root file does not exist"))
        return result
    except (OSError, RuntimeError, ValueError) as exc:
        result.errors.append(ResolveError("E_PATH", str(root), str(exc)))
        return result

    root_dir = resolved_root.parent
    try:
        _visit(resolved_root, 0, root_dir, profile, set(), [], result)
    except ResolveError as error:
        result.errors.append(error)
    return result


def _visit(
    path: Path,
    depth: int,
    root_dir: Path,
    profile: Profile,
    visited: set[Path],
    stack: list[Path],
    result: ResolveResult,
) -> None:
    text = _read(path, root_dir, profile)
    visited.add(path)
    result.order.append(_display(path, root_dir))
    stack.append(path)
    try:
        for item in parse(text):
            if isinstance(item, SyntaxIssue):
                display = _display(path, root_dir)
                raise ResolveError(
                    "E_SYNTAX",
                    display,
                    f"line {item.line}: malformed import directive (expected a whole line "
                    "of the form @relative/path)",
                    file=display,
                    line=item.line,
                )
            target = _target(path, item.path, root_dir, profile)
            display = _display(target, root_dir)
            if target in stack:
                chain = " -> ".join(_display(entry, root_dir) for entry in [*stack, target])
                raise ResolveError(
                    "E_CYCLE", display, f"import cycle detected: {chain}", file=display
                )
            if target in visited:
                continue
            if depth + 1 > profile.max_depth:
                raise ResolveError(
                    "E_DEPTH",
                    display,
                    f"import depth exceeds max_depth={profile.max_depth}",
                    file=_display(path, root_dir),
                    line=item.line,
                )
            _visit(target, depth + 1, root_dir, profile, visited, stack, result)
    finally:
        stack.pop()


def _read(path: Path, root_dir: Path, profile: Profile) -> str:
    display = _display(path, root_dir)
    try:
        size = path.stat().st_size
    except FileNotFoundError:
        raise ResolveError("E_MISSING", display, "imported file does not exist") from None
    except OSError as exc:
        raise ResolveError("E_PATH", display, str(exc)) from None
    if size > profile.max_bytes:
        raise ResolveError(
            "E_SIZE", display, f"file is {size} bytes (max_bytes={profile.max_bytes})"
        )
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        raise ResolveError("E_MISSING", display, "imported file does not exist") from None
    except OSError as exc:
        raise ResolveError("E_PATH", display, str(exc)) from None
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ResolveError(
            "E_ENCODING", display, f"file is not valid UTF-8 (byte {exc.start})"
        ) from None


def _target(current: Path, raw: str, root_dir: Path, profile: Profile) -> Path:
    if "\x00" in raw:
        raise ResolveError("E_PATH", raw, "path contains a NUL byte")
    if raw.startswith(("\\\\", "//")):
        if not profile.allow_unc:
            raise ResolveError("E_PATH", raw, "UNC paths are not allowed by this profile")
        candidate = Path(raw)
    elif _SCHEME.match(raw):
        if not profile.allow_remote:
            raise ResolveError("E_REMOTE", raw, "remote imports are not allowed by this profile")
        raise ResolveError("E_REMOTE", raw, "remote imports are not implemented in v0.1")
    elif _DRIVE.match(raw) or raw.startswith(("/", "\\")):
        if not profile.allow_absolute:
            raise ResolveError("E_PATH", raw, "absolute paths are not allowed by this profile")
        candidate = Path(raw)
    elif raw.startswith("~"):
        if not profile.allow_home:
            raise ResolveError("E_PATH", raw, "home-relative paths are not allowed by this profile")
        candidate = Path(raw).expanduser()
    else:
        candidate = current.parent / raw
    try:
        resolved = candidate.resolve()
    except (OSError, RuntimeError, ValueError) as exc:
        raise ResolveError("E_PATH", raw, str(exc)) from None
    if not _contained(resolved, root_dir):
        raise ResolveError(
            "E_TRAVERSAL",
            raw,
            "resolved path escapes the root directory (relative imports must stay inside it)",
        )
    return resolved


def _contained(path: Path, root_dir: Path) -> bool:
    try:
        path.relative_to(root_dir)
    except ValueError:
        return False
    return True


def _display(path: Path, root_dir: Path) -> str:
    try:
        return path.relative_to(root_dir).as_posix()
    except ValueError:
        return path.as_posix()
