from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from typing import NoReturn

from . import __version__
from .profile import ProfileError, builtin_names, load
from .resolver import resolve
from .vectors import verify


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        self.exit(3, f"error: {message}\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="agentmd-import",
        description="Resolve and verify @path imports in AGENTS.md files.",
    )
    parser.add_argument("--version", action="version", version=f"agentmd-import {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    resolve_cmd = sub.add_parser("resolve", help="resolve one AGENTS.md import tree")
    resolve_cmd.add_argument("root")
    resolve_cmd.add_argument("--profile", default="strict")
    resolve_cmd.add_argument("--json", action="store_true")

    verify_cmd = sub.add_parser("verify", help="run a conformance vector directory")
    verify_cmd.add_argument("directory")
    verify_cmd.add_argument("--profile", default=None, help="override each vector's profile")
    verify_cmd.add_argument("--json", action="store_true")

    sub.add_parser("profiles", help="list built-in trust profiles")
    return parser


def _resolve(args: argparse.Namespace) -> int:
    profile = load(args.profile)
    result = resolve(args.root, profile)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        for path in result.order:
            print(path)
    for error in result.errors:
        print(f"{error.rule}: {error.path}: {error.detail}", file=sys.stderr)
    return 0 if result.ok else 2


def _verify(args: argparse.Namespace) -> int:
    report = verify(args.directory, args.profile)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        for failure in report.failures:
            print(f"FAIL {failure.vector}: {failure.detail}")
        print(f"{report.passed}/{report.total} vectors passed")
    return 0 if report.ok else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "resolve":
            return _resolve(args)
        if args.command == "verify":
            return _verify(args)
        if args.command == "profiles":
            for name in builtin_names():
                profile = load(name)
                print(f"{name}: max_depth={profile.max_depth}")
            return 0
    except ProfileError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 3
    parser.error(f"unknown command {args.command}")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
