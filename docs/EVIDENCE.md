# EVIDENCE — agentmd-import-spec (verified research summary)

Source: round-3 M2 verifier V-P + skeptic-r3 + gap-evidence-r3. Ledger row 36. ADR-003. Access dates 2026-10-11.

## Gap class: F (exists but incomplete in a specific, nameable way)

- **agentsmd/agentsmd#211** (open): multi-file / import tracking issue, **24.9k★** repo, Gemini-labelled maintainer active. No merged spec + conformance vectors as of access date.
- **6+ interop bugs** document independent resolver implementations diverging (path resolution, cycles, depth, failure) — the exact vacuum a normative spec + vectors fills.
- **OpenAI Codex CLI** supports @import (no public conformance suite).
- **Claude Code**: documented 4-hop limit + escape behaviors (limit is Claude's, not a spec).

## Ownership reality (load-bearing)

- **AAIF (Linux Foundation) owns the AGENTS.md brand** — verified LF press release 2025-12-09 (round-3 lead spot-check).
- Consequence (skeptic-r3, binding): a competing "new standard" is DOA. Correct posture = contribute spec + vectors to AAIF / upstream #211. This is why the project is framed as a **contribution vehicle**, not a brand.

## Demand hook: 5/5 (capped honestly per D-006)

- 24.9k★ upstream repo with active maintainer + open multi-file issue = strong, recent, independent demand signal.
- 6+ divergence bugs = concrete pain, not hypothetical.
- Hook sentence: "AGENTS.md @import is already shipping in real harnesses with 6+ interop bugs and no normative spec — here is the security-aware spec + conformance vectors, offered to AAIF."

## Host feasibility: VERIFIED

- Python 3.12 on host; no Docker needed (L4-lite fallback, D-001).
- Differential harness against real harnesses = recorded fixtures, not live network calls (host-safe).
- Name: `agentmd-import-spec` descriptive; brand-confusion risk with AAIF mitigated by contribution posture (not a competing mark).

## Correction ledger

| Claim | Verified fact |
|---|---|
| "No import support anywhere" | FALSE — Codex CLI supports it; others diverge (hence class F, not A) |
| "We can own the AGENTS.md standard" | FALSE — AAIF owns brand; contribution posture mandatory |

## Skeptic failure scenarios → binding mitigations

1. AAIF/upstream ignores or rejects → vectors + resolver still standalone-useful; README states "proposal, not standard".
2. Syntax mismatch with upstream lands → Gate 0 live-read before freeze; track #211.
3. Trust model wrong vs real harnesses → differential profiles; default strict; escape knobs.
4. Claude 4-hop semantics wrong → [ASSUMED] until Anthropic-docs verification at build time.

## Pre-mortem: "2027-04 agentmd-import-spec failed"

AAIF accepted nothing / upstream shipped their own and ours is orphaned / syntax mismatch wasted the resolver / trust model rejected by harness authors → mitigation: contribution-first framing, Gate 0 live-read, profiles-as-data so syntax swap is cheap, vectors are the durable artifact.

## Score: 75/105 (round-3 #2, SURVIVE-with-changes)

Demand 5×5 | Gap 3×4 | Feas 4×4 | Value 3×3 | Maint 3×2 | Dist 3×2 | Fit 4×1. **Changes mandatory:** AAIF posture + trust model as first-class + reconcile Claude 4-hop + per-harness profiles.

## Build-time verification (2026-10-25 / 2026-10-26)

| Item | Status | Evidence |
|---|---|---|
| Syntax form | Verified against Claude Code docs | `@path`, relative to the importing file, absolute allowed, four hops; source URL recorded in `claude-4hop.yaml` |
| Cycle / missing semantics | Not specified upstream | This proposal defines `E_CYCLE` and `E_MISSING`; labeled as a proposal, not upstream behaviour |
| Upstream import spec | Still absent at build time | `agentsmd/agentsmd#211` open; no ratified syntax found (access 2026-10-25) |
| Codex CLI behaviour | Research-only, not re-verified | Claim dated 2026-10-11 in this file; no Codex profile shipped |
| AAIF ownership | Research-only | LF press release dated 2025-12-09; not re-checked during build |

## v0.1 verification results (2026-10-26, Windows, Python 3.12.10)

- `pytest` → 97 passed.
- `agentmd-import verify vectors` → 27/27 passed.
- `ruff check`, `ruff format --check`, strict `mypy` → clean.
- Mutation checks (containment, cycle detection, depth bound, missing-file fail-open)
  each produced failing tests before restoration.
- Wheel 13,852 bytes / sdist 15,490 bytes; `twine check` PASSED; clean-venv wheel
  install ran the documented commands with exit code 0.
- Performance: 101-file tree 102 ms; 27-vector suite 125 ms.

## Structural corrections made at build time

| Scaffold claim | Implemented reality |
|---|---|
| Placeholder syntax `@import ./relative/path.md` | Frozen as `@path` (whole line), matching the documented upstream form |
| `profiles/strict.yaml` keys `on_missing`, `on_cycle` | Removed: v0.1 is fail-closed by rule, with no per-profile on-missing/on-cycle switches |
| Rule set R1–R10 | Extended to R1–R12 (size cap, remote rejection) and implemented as vector-backed rules |
| Differential harness in v0.1 | Deferred to v0.5; without recordings a profile would be invented |
