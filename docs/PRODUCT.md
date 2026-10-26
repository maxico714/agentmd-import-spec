# PRODUCT — agentmd-import-spec

Status: v0.1 built, tested, and published as source 2026-10-26. Research date
2026-10-12. Not submitted to AAIF; no registry release.

## Problem

AI coding harnesses (Claude Code, Codex CLI, OpenCode, Cursor, etc.) read `AGENTS.md` project-instruction files. As projects grow, a single file becomes unmaintainable; several harnesses already implemented `@import`-style multi-file resolution, but **each did it independently with no shared spec** — 6+ interop bugs document divergent path resolution, cycle handling, depth limits, and failure behavior. Teams switching harnesses or mixing tools get silently different instruction sets.

## Target users (personas)

1. **Multi-harness team lead (primary):** runs Codex + Claude + OpenCode across repos. Job: one AGENTS.md tree that resolves identically everywhere.
2. **Harness author (secondary):** implementing @import in a new tool. Job: conformance vectors + normative rules to plug in, not re-derive edge cases.
3. **AAIF working-group participant (tertiary):** needs a concrete proposal + test corpus to standardize import semantics.

## Jobs-to-be-done

- "Write one root AGENTS.md that includes per-directory / per-tool fragments and resolves identically in every compliant harness."
- "Ship a conformance suite my resolver must pass before I claim AGENTS.md compatibility."
- "Understand what happens on cycles, missing files, and hostile paths before I enable imports."

## Value proposition (one sentence)

The first **normative, security-aware** @import semantics for AGENTS.md — delivered as a reference resolver + conformance vectors, intended as an **AAIF contribution**, not a competing standard.

## Non-goals (explicit)

- Not a new instruction-file brand (AGENTS.md is AAIF's).
- Not a harness; does not run agents or interpret instructions.
- Not a full Markdown linter or instruction-quality checker.
- Not a networked resolver (no remote URLs in v0.1 — local files only; remote deferred to a future profile with explicit trust).

## MVP scope (MoSCoW)

**Must (v0.1 walking skeleton):**
- Normative import syntax (one form, frozen in v0.1): a whole-line `@path` directive,
  relative to the importing file. This follows the form documented for Claude Code;
  `agentsmd/agentsmd#211` had no ratified syntax when the spec was frozen, so the
  syntax is marked as a proposal in [SPEC.md](SPEC.md).
- Reference resolver (Python CLI): resolve root → tree; deterministic depth-first order; cycle detection (hard error); missing file = hard error (fail-closed); path traversal + symlink escape = hard error.
- Conformance vectors: Markdown fixtures + expected resolution order / expected error codes.
- Trust profiles as data: e.g. `strict` (current v0.1 default), `claude-4hop` (max-depth 4, documented escape), `codex` (matches observed Codex behavior — differential-tested, not guessed).

**Should (v0.5):**
- Differential harness against at least two real implementations (Codex CLI behavior via recorded fixtures; OpenCode if import support exists — verify at build time, do not assume).
- AAIF contribution package: spec markdown + vectors + resolver as reference implementation.
- Per-harness trust profile registry (YAML/JSON data, versioned).

**Could (v1.0):**
- SARIF output for conformance failures; CI action wrapping vectors.
- Remote-import profile (explicit opt-in, allow-list, integrity hash) — only if AAIF interest exists.

**Won't (this run):** instruction content evaluation; agent execution; new file brand.

## Success criteria (measurable)

| Criterion | Measure | Command/proof |
|---|---|---|
| L1 units | Resolver unit tests green (order, cycles, traversal, depth) | `pytest -q` |
| L2 integration | ≥20 conformance vectors pass reference resolver | `agentmd-import verify vectors` |
| L3 e2e | Real repo tree (this scaffold + nested docs) resolves to documented order | fixture repo: `examples/project` |
| L4 clean env | Fresh clone + `pip install -e .` + vectors green | README steps in CI |
| L5 adversarial | Symlink escape, `../` traversal, UNC path, cycle via symlink, depth bomb → fail-closed errors | tests/adversarial/ |
| Contribution-ready | AAIF-facing spec doc + vectors zipped; no competing-brand language | manual review |

v0.1 result: 97 tests green, 27/27 vectors green, adversarial suite green; the AAIF
contribution package and differential harness remain v0.5 work.

## Honest comparison

- **agentsmd#211 upstream:** owns the brand and the issue; we contribute, we do not compete. Their multi-file work (if it lands) supersedes us — acceptable outcome (protocol M11: project still makes sense as the contribution vehicle).
- **Codex CLI @import:** one implementation, no spec, no vectors.
- **Claude Code:** documented 4-hop limit, no public import spec.
- **Custom scripts:** teams roll their own resolver; same divergence problem.

## Naming & license

- Repo working name `agentmd-import-spec` (descriptive, not a brand claim).
- License: MIT; confirm AAIF CLA/license compatibility before any upstream contribution (G2 checklist).

## Risk register (top)

| Risk | Sev | Mitigation |
|---|---|---|
| AAIF rejects or ignores contribution | High | Vectors + resolver still useful standalone; honest README "proposal, not standard" |
| Syntax mismatch with what upstream lands | High | Track #211 live; freeze syntax only after reading current upstream discussion at build time |
| Trust model too strict / too loose vs real harnesses | Med | Differential profiles; default strict, escape knobs documented |
| Claude 4-hop / escape semantics wrong | Med | Marked [ASSUMED] until verified against Anthropic docs at build time |
