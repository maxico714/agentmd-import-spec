# Security policy

## Supported versions

The latest `0.1.x` release receives security fixes. The import syntax remains a
proposal, not a ratified standard; a future upstream specification may replace
it.

## Reporting a vulnerability

Do not publish exploit details or private repository contents in an issue. Open
a minimal issue asking for a private channel, or use the repository's
**Security → Report a vulnerability** form when private vulnerability reporting
is enabled.

## Security model

- Imported files are untrusted repository content. Resolution is read-only and
  never executes imported text.
- Paths are canonicalised before containment checks; traversal and symlink
  escapes fail closed. Absolute, UNC, drive-letter and home paths are gated by
  the selected trust profile. Remote imports are rejected in v0.1.
- Only regular files are opened. The resolver caps read size and rejects import
  cycles and excessive depth.
- The tool makes no network calls and spawns no subprocesses.
- Conformance vectors are test data. Review third-party vectors before running
  them, and never point the tool at a directory you do not trust.

## Limitations

The conformance vectors are a source-checkout fixture suite, not an official
standard or certification. This is an MIT-licensed, best-effort project with no
response-time SLA.
