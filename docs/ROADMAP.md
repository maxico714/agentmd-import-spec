# ROADMAP — agentmd-import-spec

Status: v0.1 shipped 2026-10-26. SemVer; Keep a Changelog. Posture: **AAIF
contribution vehicle**, not a competing standard.

## v0.1 — Walking skeleton (DONE 2026-10-26)

- [x] Gate 0: upstream read before freezing syntax. `agentsmd/agentsmd#211` was open
      with no ratified import syntax, and Claude Code documents `@path`, relative to
      the importing file, with a four-hop limit. The syntax in
      [SPEC.md](SPEC.md) follows that documented form rather than inventing a keyword.
- [x] Reference resolver with R1–R12, fail-closed errors, and profiles as data
      (`strict` default, `claude-4hop`).
- [x] 27 conformance vectors covering order, missing, cycles, traversal, symlink
      escape, absolute/UNC/drive/home/remote paths, depth, encoding, size, syntax, BOM,
      fenced code, and empty roots.
- [x] CLI: `resolve`, `verify`, `profiles`, `--json`, exit codes 0–3.
- [x] 97 pytest tests (unit, integration, adversarial) plus three mutation checks.
- [x] CI workflow on Ubuntu + Windows × Python 3.10/3.12/3.13.
- [x] Spec includes the security posture; no separate TRUST_MODEL.md was needed because
      the threat model lives in SPEC.md §7 and in `tests/adversarial/`.

**Evidence:** [docs/EVIDENCE.md](EVIDENCE.md), [BUILD_CHECKLIST.md](../BUILD_CHECKLIST.md).

**Open spike:** whether the frozen syntax matches whatever upstream later ratifies.
The mitigation is structural: profiles and vectors are data, so a syntax change is a
parser change plus fixtures, not a redesign. Posting to #211 is human-gated.

## v0.5 — Core value

- [ ] Differential harness: record real-harness behaviour (Codex CLI fixtures;
      OpenCode if import support exists — verify, do not assume) and add
      `diff-behavior`.
- [ ] Codex profile, only after recorded fixtures exist.
- [ ] AAIF contribution package assembled (spec + vectors + resolver zip + contribution
      letter draft — **draft only; a human sends it**).

## v1.0 — Production-ready

- [ ] Vector count ≥40; SARIF output; reusable CI action.
- [ ] Upstream response incorporated (accepted / amended / rejected — README updated
      honestly either way).
- [ ] SBOM; signed releases (G3, owner-gated).
- [ ] AAIF license compatibility confirmed before any upstream contribution.

## Post-1.0 (parked)

- Remote-import profile (allow-list + integrity hash) — only with AAIF interest.
- Instruction-content linting (out of scope per non-goals).

## Maintenance cadence

- Spec + vectors are the stable artifacts; the resolver follows them.
- Rule-id changes require a minor version and migration notes.
