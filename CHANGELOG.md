# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- Imports are now required to resolve to regular files (SPEC R2 and the "regular files
  only" rule). Directories, devices, and pipes fail with `E_PATH` instead of being read
  (a Windows `@NUL` import previously succeeded as an empty file).
- `max_bytes` is enforced while reading as well as from `stat`, so a file that grows
  between the check and the read cannot exceed the cap.

## [0.1.0] - 2026-10-26

### Added

- Normative import semantics in `docs/SPEC.md`: whole-line `@path` directives,
  depth-first document order, single occurrence per file, and fail-closed error rules
  R1–R12.
- Reference resolver (`agentmd_import`) with structured errors `E_MISSING`, `E_CYCLE`,
  `E_TRAVERSAL`, `E_PATH`, `E_REMOTE`, `E_DEPTH`, `E_ENCODING`, `E_SIZE`, and
  `E_SYNTAX`.
- Trust profiles as data: `strict` (default) and `claude-4hop`; custom profiles load
  from a YAML/JSON path with validated keys.
- 27 conformance vectors covering ordering, nesting, duplicate handling, cycles,
  traversal, symlink escape, absolute/UNC/drive/home paths, remote schemes, depth
  limits, malformed directives, fenced code, BOM, invalid UTF-8, size caps, and empty
  roots.
- CLI: `resolve`, `verify`, and `profiles`, with `--json` output and documented exit
  codes 0–3.
- Example trees under `examples/` for a valid tree, a missing import, and a cycle.
- Tests: unit coverage for parser, profiles, resolver, and vectors; CLI integration
  tests; adversarial tests for depth bombs, wide fan-out, symlink escape/cycle, and
  path normalisation.

### Security

- Containment checks run on canonical paths, so symlinks cannot escape the root.
- Depth and byte caps bound untrusted input; remote imports are rejected.
- Files are opened read-only; the resolver performs no network access and spawns no
  subprocesses.

### Verified

- `python -m pytest`: 97 passed (Python 3.12.10, Windows).
- `agentmd-import verify vectors`: 27/27 passed.
- `ruff check`, `ruff format --check`, `mypy` (strict): clean.
- Mutation checks: disabling containment, cycle detection, the depth bound, or
  fail-closed missing-file handling each fails the corresponding tests.
- Packaging: wheel (13,852 bytes) and sdist (15,490 bytes) build; `twine check` passes;
  both built-in profiles and the license file are present in the wheel; a clean-venv
  wheel install runs `--version`, `profiles`, `resolve`, and `verify` successfully.

[0.1.0]: https://github.com/maxico714/agentmd-import-spec/releases/tag/v0.1.0
