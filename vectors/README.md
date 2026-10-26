# Conformance vectors

Each directory is one vector. `agentmd-import verify vectors` runs them in sorted order.

```
<id>/
  input/AGENTS.md        root file (or the name in expected.json "root")
  input/...              imported files
  expected.json          profile, expected order, expected (rule, path) errors
  profile.yaml           optional vector-local profile, referenced from expected.json
  outside.md             fixtures that must remain outside input/ (traversal tests)
```

`expected.json`:

```json
{
  "profile": "strict",
  "order": ["AGENTS.md", "a.md", "docs/b.md"],
  "errors": [{"rule": "E_TRAVERSAL", "path": "../outside.md"}]
}
```

- `profile` is a built-in profile name, or a path relative to the vector directory.
- `order` is compared exactly. Paths are relative to `input/` and use `/`.
- `errors` is compared as an ordered list of `(rule, path)` pairs; `detail` prose is
  not part of conformance.
- `root` defaults to `AGENTS.md`.

The reference resolver stops at the first error, so vectors with errors list the prefix
visited before the failure in `order` and exactly one error.

| Vector | Covers |
|---|---|
| 001-basic-order | R1 depth-first document order |
| 002-nested-dfs | R1 nested traversal |
| 003-duplicate-import | R1 single occurrence |
| 004-missing-file | R2 |
| 005-cycle-direct | R3 |
| 006-cycle-self | R3 |
| 007-traversal | R4 |
| 008-absolute-path | R6 POSIX absolute |
| 009-unc-path | R6 UNC |
| 010-windows-drive | R6 Windows drive |
| 011-home-path | R6 home-relative |
| 012-remote-https | R12 |
| 013-remote-ssh | R12 |
| 014-claude-depth-limit | R7 with `claude-4hop` |
| 015-strict-depth-ok | R7 within `strict` |
| 016-syntax-trailing-text | R9 |
| 017-syntax-whitespace-path | R9 |
| 018-inline-mention-ignored | §2 whole-line rule |
| 019-fenced-code-ignored | §2 fenced blocks |
| 020-bom-header | R8 BOM |
| 021-empty-root | R10 |
| 022-dotdot-inside | R4 normalisation |
| 023-dedupe-spellings | R1 canonical identity |
| 024-tilde-fence | §2 fenced blocks |
| 025-syntax-bare-at | R9 |
| 026-invalid-utf8 | R8 |
| 027-size-cap | R11 with a vector-local profile |
