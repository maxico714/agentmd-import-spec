# Import semantics for AGENTS.md — proposal v0.1

Status: **proposal, not a standard.** This document is offered as input to the
`AGENTS.md` work tracked in `agentsmd/agentsmd#211`. It does not define or claim the
`AGENTS.md` brand, which belongs to the Agentic AI Foundation (AAIF).

The reference resolver in `src/agentmd_import/` implements every rule below, and
`vectors/` contains executable fixtures for each one. Where this document and the
resolver disagree, the resolver plus vectors are the authority and the document is the bug.

## 1. Scope

This specification covers **only** how a root `AGENTS.md` file includes other local
Markdown files. It does not cover:

- the meaning of instruction text,
- which files an implementation should look for (`AGENTS.md` discovery order),
- remote or generated content,
- Markdown rendering.

Implementations that already resolve imports may adopt these rules without adopting
this project's resolver.

## 2. Directive syntax

A **directive** is a line whose first non-whitespace character is `@`, where the
remainder of the line (after trimming leading and trailing whitespace) is a path
containing no whitespace.

```md
# Project instructions

@docs/style.md
@docs/testing.md
```

- The directive occupies the **whole line**. `@path` appearing mid-sentence is plain text.
- There is no `import` keyword: the form is `@path`.
- A UTF-8 byte-order mark at the start of a file is neither part of the first
  directive nor an error.
- Lines inside fenced code blocks (three or more backticks or tildes) are **not**
  directives, so documentation examples are never followed.
- CRLF and LF line endings are equivalent.
- A line beginning with `@` whose remainder is empty or contains whitespace is
  **malformed** (see R9).

Paths are resolved relative to the file that contains the directive, not relative to
the root file or the process working directory.

## 3. Normative rules

Rule identifiers are stable and are reported verbatim by the resolver.

| ID | Rule | Failure |
|---|---|---|
| **R1 Order** | Files are visited depth-first in document order. Each resolved file appears exactly once, at its first occurrence. | — |
| **R2 Missing** | An import that does not resolve to an existing regular file is a hard error. There is no silent skip. | `E_MISSING` |
| **R3 Cycle** | A file that is already on the active import stack is a hard error. The diagnostic names the full chain. | `E_CYCLE` |
| **R4 Containment** | The canonical path of every imported file must stay inside the directory that contains the root file. | `E_TRAVERSAL` |
| **R5 Symlinks** | Containment is evaluated **after** canonicalisation, so a symlink whose target leaves the root fails R4. | `E_TRAVERSAL` |
| **R6 Absolute forms** | Absolute paths (POSIX, Windows drive, UNC) and home-relative paths are profile-gated. | `E_PATH` |
| **R7 Depth** | The number of hops from the root is bounded by the profile. The root is depth 0; importing a file at depth `d` requires `d + 1 <= max_depth`. | `E_DEPTH` |
| **R8 Encoding** | Files are UTF-8, optionally with a BOM. Invalid UTF-8 is a hard error. | `E_ENCODING` |
| **R9 Syntax** | A malformed directive is a hard error in the `strict` profile; implementations must not guess the intended path. | `E_SYNTAX` |
| **R10 Empty** | A root file with no directives is valid and resolves to itself. | — |
| **R11 Size** | Files larger than the profile's `max_bytes` are rejected before they are read into memory. | `E_SIZE` |
| **R12 Remote** | `scheme://` imports are rejected. No profile in v0.1 permits fetching. | `E_REMOTE` |

Additional normative details:

1. **Canonical identity.** Two spellings that canonicalise to the same file
   (`docs/a.md`, `./docs/../docs/a.md`) are one file for R1 and R3.
2. **Fail fast.** The reference resolver stops at the first error and reports one
   structured error. The `order` field then contains the prefix visited before the
   failure. A conformance check compares the rule, the path, and the order.
3. **Determinism.** The same tree resolves to the same order on every run and on every
   platform. Paths in output are relative to the root directory and always use `/`.
4. **Directive classification order.** NUL → UNC → remote scheme → absolute (drive
   letter, leading `/` or `\`) → home (`~`) → relative. A leading `\` is treated as
   absolute on every platform for consistent behaviour.
5. **Regular files only.** Importing a directory (or other non-regular file) fails with
   `E_PATH`.
6. **No fragments or query strings.** `@a.md#section` is a path containing `#`, not a
   fragment selector, and normally fails with `E_MISSING`.

## 4. Trust profiles

A profile is data, not code. The resolver ships two:

| Key | `strict` (default) | `claude-4hop` |
|---|---|---|
| `max_depth` | 32 | 4 |
| `max_bytes` | 1 048 576 | 1 048 576 |
| `allow_absolute` | false | true |
| `allow_unc` | false | false |
| `allow_home` | false | true |
| `allow_remote` | false | false |

```yaml
name: strict
max_depth: 32
max_bytes: 1048576
allow_absolute: false
allow_unc: false
allow_home: false
allow_remote: false
source: "agentmd-import-spec v0.1 proposal: relative paths only, contained in the root directory"
```

`claude-4hop` records the behaviour documented for Claude Code at
<https://code.claude.com/docs/en/memory> (accessed 2026-10-25): imports use `@path`,
are relative to the importing file, absolute paths are allowed, and the maximum depth
is four hops. The same documentation does **not** specify cycle handling or
missing-file handling, so those remain subject to R2 and R3 here.

**This project is deliberately stricter than that documentation** where the
documentation is silent: containment (R4/R5), encoding (R8), size (R11), and explicit
cycle/missing errors always apply. `claude-4hop` relaxes path-form checks only.

Profile files are YAML or JSON with exactly these keys:

- required: `name` (string), `max_depth` (integer ≥ 0), `max_bytes` (integer ≥ 1),
- optional: `allow_absolute`, `allow_unc`, `allow_home`, `allow_remote` (booleans, default false),
- optional: `source` (string describing provenance; default `"project proposal"`).

Unknown keys, booleans supplied for integer fields, and out-of-range values are
configuration errors. A name that is not an existing file is looked up among built-in
profiles; no other resolution is attempted.

## 5. Structured output

The CLI emits, with `--json`:

```json
{
  "root": "examples/project/AGENTS.md",
  "profile": "strict",
  "order": ["AGENTS.md", "docs/style.md", "docs/conventions.md", "docs/testing.md"],
  "errors": []
}
```

Each error object is `{"rule", "path", "detail", "file", "line"}`. `path` is the
offending directive as written (or the canonical relative path for `E_MISSING`,
`E_ENCODING`, `E_SIZE`, and `E_CYCLE`). `file` and `line` are populated when the
location is known.

Exit codes: `0` success, `1` conformance-vector failure, `2` resolver hard error,
`3` environment/configuration/usage error.

## 6. Conformance vectors

A vector is a directory:

```
vectors/001-basic-order/
  input/AGENTS.md        root file (name configurable via expected.json "root")
  input/...              imported files
  expected.json          expected outcome
  profile.yaml           optional vector-local profile
```

```json
{
  "profile": "strict",
  "order": ["AGENTS.md", "a.md", "docs/b.md", "c.md"],
  "errors": []
}
```

Rules for a conforming implementation:

1. Run with the profile named in `expected.json` (or the profile override).
2. Compare the resolved order exactly.
3. Compare the sequence of `(rule, path)` pairs exactly. Diagnostic prose is not part
   of conformance, so wording may differ.

Vectors `001`–`027` shipped here cover R1–R12, including malformed directives, fenced
code, BOM, invalid UTF-8, size caps, symlink escapes, depth limits, and remote paths.

## 7. Security posture

Instruction trees are untrusted input. A resolver must therefore:

- canonicalise before checking containment (R4/R5),
- cap depth so a self-similar tree cannot exhaust the stack (R7),
- cap file size before reading (R11),
- reject remote content by default (R12),
- fail closed on missing files and malformed directives (R2/R9),
- never execute, render, or interpolate imported content.

The reference resolver opens files read-only, performs no network access, and runs no
subprocesses.

## 8. Open questions for upstream discussion

1. Should cycles be an error or a silent stop? This proposal chooses error (R3).
2. Should duplicate imports be skip-on-second-occurrence (R1) or error?
3. Should malformed directives be errors or ignored as prose? This proposal chooses
   error in `strict` (R9) and leaves leniency to future profiles.
4. Should containment be relative to the root file's directory or to the repository
   root? This proposal uses the root file's directory, which nests cleanly.
5. What should a future remote profile require (allow-list, integrity hash, pinning)?

## 9. Compatibility notes

- Claude Code: syntax and four-hop default are reflected in `claude-4hop`; unspecified
  behaviours are fixed here rather than guessed.
- OpenAI Codex CLI: reported by the 2026-10-11 research pass to support imports
  (`docs/EVIDENCE.md`); no conformance suite was found, and this project has not
  re-verified Codex behaviour. A Codex profile therefore ships only after differential
  fixtures exist — inventing it now would be guessing.
- `agentsmd/agentsmd#211`: tracks multi-file support upstream and was open at the time
  of the research pass; this document defers to any syntax upstream later ratifies.
