# BUILD CHECKLIST — agentmd-import-spec

Status: v0.1 complete 2026-10-26. Each gate records the command run and its observed
result. Circuit breaker: 3 failures per gate → stop, re-research, log in STATE.md.

## Gate 0 — Upstream live-read (FIRST, before any code)

- [x] Upstream state checked at build time (access date 2026-10-25):
      `agentsmd/agentsmd#211` was open with no ratified import syntax.
- [x] Claude Code documentation read: whole-line `@path`, relative to the importing
      file, absolute paths allowed, four hops maximum; cycle and missing behaviour
      unspecified. Encoded in `src/agentmd_import/profiles/claude-4hop.yaml` with the
      source URL.
- [x] Syntax frozen in `docs/SPEC.md` §2 as `@path`, the documented upstream form,
      rather than an invented `@import` keyword.
- [x] Codex CLI import support remains a research claim from 2026-10-11
      (`docs/EVIDENCE.md`), not re-verified here; no Codex profile ships.

## Gate 1 — L0 static (every commit)

- [x] `ruff check .` → All checks passed.
- [x] `ruff format --check .` → 20 files already formatted.
- [x] `mypy` (strict, `src`) → Success: no issues found in 7 source files.
- [x] `pytest --collect-only -q` → 97 tests collected.

## Gate 2 — L1 units (rules R1–R12)

- [x] Positive and negative tests per rule: order, missing, cycle, traversal, symlink
      escape, absolute/UNC/drive/home, remote, depth, encoding, syntax, empty root,
      size cap.
- [x] Profile loader tests: strict defaults, claude-4hop limits, unknown keys, wrong
      types, boolean-as-integer, negative depth, zero byte cap, invalid YAML.
- [x] **Mutation sanity:** fail-open on a missing import → `test_missing_import_is_a_hard_error`
      and three vector tests fail; restored.
- [x] **Mutation sanity:** containment check disabled → five traversal/symlink tests fail;
      restored.
- [x] **Mutation sanity:** cycle detection disabled → four cycle tests fail; restored.
- [x] **Mutation sanity:** depth comparison flipped → depth tests and the claude vector fail;
      restored.

## Gate 3 — L2 conformance vectors

- [x] 27 vectors committed; `agentmd-import verify vectors` → `27/27 vectors passed`.
- [x] Adversarial vectors produce the specified rule-ids: UNC/drive/home/absolute →
      `E_PATH`, remote → `E_REMOTE`, depth → `E_DEPTH`, invalid UTF-8 → `E_ENCODING`,
      size → `E_SIZE`, traversal fixtures → `E_TRAVERSAL`.
- [x] JSON output schema validated in `tests/integration/test_cli.py`.
- [x] Determinism: `verify` run twice produces identical results; `pytest` reruns are
      stable.

## Gate 4 — L3 e2e

- [x] `examples/project` resolves to `AGENTS.md, docs/style.md, docs/conventions.md,
      docs/testing.md`.
- [x] Exit codes verified: 0 (success), 1 (tampered vector), 2 (missing import and
      cycle), 3 (unknown profile, missing vectors directory, usage error).

## Gate 5 — L5 adversarial

- [x] `tests/adversarial/test_limits.py`: 80-file depth chain, 300-file fan-out, long
      cycle, traversal that leaves and returns, `@..`, fragment suffix, Unicode path,
      nested BOM, symlink cycle, symlinked-directory escape.
- [x] Symlink tests skip cleanly where the host cannot create symlinks; they ran on
      this Windows host.
- [x] Performance: 100-file fan-out (101 files) resolves in 102 ms; vector suite in
      125 ms — inside the 1 s / 5 s budgets.

## Gate 6 — Differential harness (v0.5 gate)

- [ ] Record real-harness behaviour (Codex CLI fixtures; OpenCode if support exists).
- [ ] `agentmd-import diff-behavior` compares reference vs recorded output.

Not started. A Codex profile without recordings would be a guess.

## Gate 7 — AAIF contribution package (human-gated)

- [ ] Spec + vectors + resolver zipped; contribution letter **drafted only**.
- [ ] MIT vs AAIF CLA compatibility confirmed.
- [ ] Competing-brand language review (README and SPEC state "proposal, not a standard").

Not started; requires owner action to contact upstream.

## Gate 8 — L4 clean env

- [x] Wheel built (13,852 bytes) and sdist (15,490 bytes); `twine check` PASSED.
- [x] Clean venv + wheel install: `--version`, `profiles`, `resolve`, `verify` all
      succeed.
- [x] Fresh clone → `pip install -e ".[dev]"` → pytest and vector suite (see
      `docs/EVIDENCE.md`).

## Gate 9 — Pre-M8 honesty audit

- [x] No bare `except` in `src/`; no TODO/FIXME/XXX in `src`, `tests`, or `docs`.
- [x] Research-only claims are labeled with their dates in `docs/EVIDENCE.md`.
- [x] Secret-shape grep over `src`, `tests`, `docs`, `examples`, `vectors` → no
      findings.
- [x] `AGENTS.md` and `.agent/` excluded from the repository via `.gitignore`.

## Definition of done (v0.1)

Gates 0–5 + 8 + 9 green with evidence above. Gate 6 = v0.5. Gate 7 = human-gated
contribution step.
