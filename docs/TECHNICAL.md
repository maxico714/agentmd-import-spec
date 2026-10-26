# TECHNICAL — agentmd-import-spec

Status: v0.1 built and verified 2026-10-26. Python 3.12 reference implementation
(`requires-python >=3.10`), stdlib plus PyYAML. No network in v0.1.

## Architecture (C4-lite)

```
[root AGENTS.md] → Parser (directives) → Resolver (trust profile)
                                              ↓
                          ordered tree, or one hard error
                                              ↓
                    conformance vectors (fixtures + expected outcomes)
                                              ↓
                        CLI: resolve | verify | profiles (--json)
```

Single package `agentmd_import` (console script `agentmd-import`). No services, no
daemon. Vectors are a directory of Markdown fixtures plus JSON expectations.

## Module map

| Module | Responsibility |
|---|---|
| `parser.py` | Line-oriented directive scan; fenced-code suppression; BOM strip |
| `profile.py` | Profile dataclass, YAML/JSON validation, built-in lookup via `importlib.resources` |
| `resolver.py` | DFS traversal, path classification, containment, cycle/depth/size/encoding checks |
| `vectors.py` | Vector discovery and comparison |
| `cli.py` | Argument parsing, JSON output, exit codes |

## Import syntax (frozen v0.1)

A directive is a whole line whose first non-whitespace character is `@`; the trimmed
remainder is the path and must contain no whitespace.

```md
@docs/style.md
```

Rationale: this matches the form documented for Claude Code at
<https://code.claude.com/docs/en/memory> (accessed 2026-10-25) and avoids inventing an
`@import` keyword. If `agentsmd/agentsmd#211` ratifies a different form, only
`parser.py`, the fixtures, and SPEC §2 change.

## Normative semantics (implemented)

- **R1 Order:** depth-first, document order; a canonical file appears once.
- **R2 Missing:** `E_MISSING`, fail-closed.
- **R3 Cycle:** active-stack detection on canonical paths; `E_CYCLE` with chain.
- **R4 Containment:** canonical target must stay under the root file's directory;
  `E_TRAVERSAL`.
- **R5 Symlinks:** containment is checked after `Path.resolve()`, so link escapes fail.
- **R6 Path forms:** UNC, remote scheme, absolute (drive / leading `/` or `\`), home
  (`~`) are classified in that order and rejected unless the profile allows them;
  `E_PATH` except for remote forms.
- **R7 Depth:** root is depth 0; importing at depth `d` requires `d + 1 <= max_depth`;
  `E_DEPTH`.
- **R8 Encoding:** UTF-8 with optional BOM; `E_ENCODING`.
- **R9 Syntax:** malformed directive → `E_SYNTAX`; no lenient guessing in `strict`.
- **R10 Empty list:** a root with zero imports resolves to itself.
- **R11 Size:** `max_bytes` is checked from `stat` before reading; `E_SIZE`.
- **R12 Remote:** `scheme://` → `E_REMOTE`; `allow_remote` never fetches in v0.1.

The resolver fails fast: it reports the first error and the order visited before it.
That keeps output deterministic and the vector comparison exact.

## Trust profiles (data)

```yaml
# src/agentmd_import/profiles/strict.yaml
name: strict
max_depth: 32
max_bytes: 1048576
allow_absolute: false
allow_unc: false
allow_home: false
allow_remote: false
source: "agentmd-import-spec v0.1 proposal: relative paths only, contained in the root directory"
```

```yaml
# src/agentmd_import/profiles/claude-4hop.yaml
name: claude-4hop
max_depth: 4
max_bytes: 1048576
allow_absolute: true
allow_unc: false
allow_home: true
allow_remote: false
source: "https://code.claude.com/docs/en/memory (accessed 2026-10-25): ..."
```

`load()` treats an existing file path as a custom profile and otherwise looks up a
built-in name. Validation rejects unknown keys, wrong types, booleans in integer fields,
negative depth, and zero byte caps. Adding a profile is a data change plus vectors.

## Interfaces

- `agentmd-import resolve ROOT [--profile strict] [--json]`
- `agentmd-import verify DIR [--profile NAME] [--json]`
- `agentmd-import profiles`
- JSON: `{root, profile, order: [paths], errors: [{rule, path, detail, file, line}]}`
- Exit codes: 0 ok; 1 vector failure; 2 resolver hard error; 3 environment/usage.

## Data model

- Vector: `input/` tree + `expected.json` (`profile`, optional `root`, `order`,
  `errors` as `(rule, path)` pairs) + optional `profile.yaml`.
- Conformance compares order and `(rule, path)` only; diagnostic prose is not normative.

## Threat model (STRIDE-lite)

Instruction trees are untrusted input.

| Threat | Mitigation |
|---|---|
| Path traversal (`../`) | Canonicalise, then containment check (R4) |
| Symlink escape | Resolve targets; check canonical path (R5) |
| Depth bomb / stack exhaustion | `max_depth` enforced before recursion (R7) |
| Large-file memory pressure | `stat` size gate before reading (R11) |
| Encoding confusion | Strict UTF-8 decode; BOM only at start (R8) |
| Remote content / SSRF | No network code path; remote rejected (R12) |
| Malformed directives | Explicit `E_SYNTAX`, no inference (R9) |
| Command execution | None: no shell, no subprocess, no imports of user content |

Shipped vectors are trusted fixtures; the adversarial and traversal fixtures contain
hostile paths on purpose and must be rejected, never followed.

## Error model

Stable rule ids. Each error carries `rule`, `path`, `detail`, and location when known.
No silent coercion, no partial success: exit code 2 with the prefix order in `--json`.

## Performance

Measured 2026-10-26 on Windows, Python 3.12.10:

- 100-file fan-out (101 files including the root): 102 ms.
- Vector suite (27 vectors): 125 ms.
- Full 97-test suite: ~6–8 s, including subprocess CLI tests.

Budget from the scaffold: 100-file tree < 1 s, vector suite < 5 s. Both hold with a
wide margin. Files are read once; no unbounded buffers beyond `max_bytes`.

## Testing strategy

- **L0:** `ruff check`, `ruff format --check`, strict `mypy`.
- **L1:** parser, profile, resolver, vector-runner units.
- **L2:** 27 conformance vectors through the same code path as the CLI.
- **L3:** CLI integration via subprocess (stdout, stderr, exit codes, JSON).
- **L4:** wheel/sdist build, `twine check`, clean-venv install, fresh-clone run.
- **L5:** adversarial tests (depth bomb, wide fan-out, symlink escape/cycle, traversal
  that leaves and returns, NUL bytes, invalid UTF-8, huge files, non-regular files).
- **Mutation checks:** disabling containment, cycle detection, or the depth bound each
  kills the relevant tests.

## Packaging

PyPI distribution name `agentmd-import-spec`; console script `agentmd-import`.
Registry publication is owner-gated and has not been performed.

## Repository layout

```
agentmd-import-spec/
  src/agentmd_import/{parser,profile,resolver,vectors,cli}.py
  src/agentmd_import/profiles/{strict,claude-4hop}.yaml
  vectors/{001..027}-*/{input,expected.json[,profile.yaml]}
  examples/{project,broken,cycle}/
  docs/{SPEC,PRODUCT,TECHNICAL,ROADMAP,EVIDENCE}.md
  tests/{unit,integration,adversarial}/
```
