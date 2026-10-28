# agentmd-import-spec

**Normative `@path` import semantics for `AGENTS.md`, with a reference resolver and 27 conformance vectors.**

`AGENTS.md` files are growing into multi-file instruction trees. Harnesses resolve
imports differently, and those differences are silent: the same repository can produce
a different instruction set depending on which tool reads it. This project specifies the
semantics, ships an executable reference resolver, and publishes fixtures a harness
author can run against their own implementation.

**Proposal, not a standard.** `AGENTS.md` belongs to the Agentic AI Foundation. This
work is offered to the upstream discussion in
[`agentsmd/agentsmd#211`](https://github.com/agentsmd/agentsmd/issues/211); it does not
claim the format.

## What is specified

- Whole-line `@path` directives, relative to the importing file.
- Depth-first, document-order resolution; each file once.
- Fail-closed errors: `E_MISSING`, `E_CYCLE`, `E_TRAVERSAL`, `E_PATH`, `E_REMOTE`,
  `E_DEPTH`, `E_ENCODING`, `E_SIZE`, `E_SYNTAX`.
- Security rules as first-class behaviour: canonicalise before containment checks,
  depth caps, size caps, UTF-8 only, no remote fetches.
- Trust profiles as data (`strict`, `claude-4hop`), so a harness can adopt the rules
  without adopting this code.

Full text: [docs/SPEC.md](docs/SPEC.md).

## Install

```console
python -m pip install -e .
```

Requires Python 3.10+ and PyYAML. No network access is used at any point.

## Quickstart

The repository includes a small example tree:

```console
$ agentmd-import resolve examples/project/AGENTS.md
AGENTS.md
docs/style.md
docs/conventions.md
docs/testing.md
```

A missing import fails closed (exit code 2, diagnostic on stderr):

```console
$ agentmd-import resolve examples/broken/AGENTS.md
AGENTS.md
E_MISSING: missing.md: imported file does not exist
```

A cycle reports the chain:

```console
$ agentmd-import resolve examples/cycle/AGENTS.md
AGENTS.md
a.md
b.md
E_CYCLE: a.md: import cycle detected: AGENTS.md -> a.md -> b.md -> a.md
```

Run the conformance suite against the shipped resolver from a source checkout
or source distribution:

```console
$ agentmd-import verify vectors
27/27 vectors passed
```

The vectors are conformance fixtures. They are included in the GitHub source and
source distribution, but not installed inside the wheel; pass your own vector
directory when the package was installed from a wheel.

JSON output, for tooling:

```console
$ agentmd-import resolve examples/project/AGENTS.md --json
{
  "root": "examples/project/AGENTS.md",
  "profile": "strict",
  "order": ["AGENTS.md", "docs/style.md", "docs/conventions.md", "docs/testing.md"],
  "errors": []
}
```

## Commands

| Command | Purpose |
|---|---|
| `agentmd-import resolve ROOT [--profile NAME] [--json]` | Resolve one import tree |
| `agentmd-import verify DIR [--profile NAME] [--json]` | Run a directory of conformance vectors |
| `agentmd-import profiles` | List built-in profiles |

| Exit code | Meaning |
|---|---|
| 0 | Success |
| 1 | A conformance vector failed (including an unreadable `expected.json`) |
| 2 | The import tree has a hard error |
| 3 | Environment, configuration, or usage problem |

## Rules

| ID | Rule | Error |
|---|---|---|
| R1 | Depth-first, document order; each file once | — |
| R2 | Missing file is a hard error | `E_MISSING` |
| R3 | Import cycle is a hard error, with the chain | `E_CYCLE` |
| R4 | Imported files must stay inside the root file's directory | `E_TRAVERSAL` |
| R5 | Symlinks are canonicalised before the containment check | `E_TRAVERSAL` |
| R6 | Absolute, UNC, and home paths are profile-gated | `E_PATH` |
| R7 | Hop count is capped by the profile (`max_depth`) | `E_DEPTH` |
| R8 | UTF-8 only; a BOM is allowed | `E_ENCODING` |
| R9 | Malformed directives are hard errors in `strict` | `E_SYNTAX` |
| R10 | A root with no imports is valid | — |
| R11 | Files above `max_bytes` are rejected before reading | `E_SIZE` |
| R12 | `scheme://` imports are rejected in v0.1 | `E_REMOTE` |

The resolver stops at the first error and reports the order visited before it. That is
a deliberate v0.1 choice: one deterministic failure instead of a partial tree.

## Trust profiles

| Key | `strict` (default) | `claude-4hop` |
|---|---|---|
| `max_depth` | 32 | 4 |
| `max_bytes` | 1 MiB | 1 MiB |
| `allow_absolute` | false | true |
| `allow_unc` | false | false |
| `allow_home` | false | true |
| `allow_remote` | false | false |

`claude-4hop` follows the behaviour documented for Claude Code
([code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory), accessed
2026-10-25): `@path`, relative to the importing file, absolute paths allowed, four hops
maximum. That documentation does not define cycle or missing-file handling, so those
rules here are this proposal's choice, not a description of Claude Code.

Profiles are data. Point `--profile` at a YAML/JSON file to change limits:

```yaml
name: team
max_depth: 8
max_bytes: 65536
allow_absolute: false
```

Unknown keys, non-integer depths, and out-of-range values are rejected with exit code 3
rather than silently ignored.

## Conformance vectors

Each vector is a directory with an input tree, an `expected.json`, and optionally a
vector-local `profile.yaml`:

```json
{
  "profile": "strict",
  "order": ["AGENTS.md", "a.md", "docs/b.md", "c.md"],
  "errors": []
}
```

Conformance compares the exact order and the exact `(rule, path)` sequence; diagnostic
wording is not part of the contract. The 27 shipped vectors cover ordering, nesting,
duplicates, cycles, traversal, symlink escape, absolute/UNC/drive/home/remote paths,
depth limits, malformed directives, fenced code, BOM, invalid UTF-8, size caps, and
empty roots. See [vectors/README.md](vectors/README.md).

## Security posture

Instruction trees are untrusted input. The resolver:

- canonicalises targets before the containment check, so symlink escapes fail;
- caps depth (no unbounded recursion from a self-similar tree);
- caps file size before reading (`max_bytes`);
- decodes strictly as UTF-8 and never guesses an encoding;
- opens files read-only, spawns no processes, and makes no network calls.

Hostile trees — `../` traversal, symlink farms, cycles, depth bombs, oversized files,
invalid UTF-8, UNC and remote paths — are exercised in
`tests/adversarial/` and in the vector suite.

## Honest comparison

- **Claude Code** documents `@path` imports and a four-hop limit; it does not publish
  conformance vectors, and cycle/missing behaviour is unspecified. This proposal adopts
  the documented parts and defines the rest explicitly.
- **OpenAI Codex CLI** was reported by the 2026-10-11 research pass to support imports;
  no conformance suite was found. No Codex profile ships here because behaviour has not
  been recorded — a profile would be a guess.
- **`agentsmd/agentsmd#211`** is the upstream venue for multi-file support. If upstream
  ratifies different syntax, this project's syntax section is superseded; the vectors
  and resolver remain useful as a test corpus.

## Limitations

- Reports one error per run (fail-fast), not a full error list.
- No remote imports; `allow_remote` is reserved for a future profile and still returns
  `E_REMOTE` in v0.1.
- No Codex differential profile yet (see above).
- Markdown is parsed line-by-line for directives; it is not a Markdown renderer.
- Windows and POSIX behaviours are unified deliberately: a leading `\` is treated as an
  absolute path everywhere, and output paths always use `/`.

## Development

```console
python -m pip install -e ".[dev]"
ruff check src tests
ruff format --check src tests
mypy
python -m pytest
agentmd-import verify vectors
```

Local verification (2026-10-26, Python 3.12.10 on Windows): 100 tests pass, 27/27
vectors pass, ruff and strict mypy clean. CI runs the same checks on Ubuntu and Windows
across Python 3.10, 3.12, and 3.13.

## License

MIT. See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
