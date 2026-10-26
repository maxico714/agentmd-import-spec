from __future__ import annotations

import re
from dataclasses import dataclass

_FENCE = re.compile(r"^(`{3,}|~{3,})")


@dataclass(frozen=True)
class Import:
    path: str
    line: int


@dataclass(frozen=True)
class SyntaxIssue:
    line: int
    text: str


def parse(text: str) -> list[Import | SyntaxIssue]:
    """Return directives and malformed directives in document order.

    A directive is a whole line of the form `@relative/path` with no embedded whitespace.
    Lines inside fenced code blocks are ignored so documentation examples are never followed.
    """
    if text.startswith("\ufeff"):
        text = text[1:]
    items: list[Import | SyntaxIssue] = []
    fence: str | None = None
    for number, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        fence_match = _FENCE.match(stripped)
        if fence_match:
            marker = fence_match.group(1)
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            continue
        if fence is not None:
            continue
        if not stripped.startswith("@"):
            continue
        body = stripped[1:]
        if not body or any(char.isspace() for char in body):
            items.append(SyntaxIssue(line=number, text=raw))
        else:
            items.append(Import(path=body, line=number))
    return items
