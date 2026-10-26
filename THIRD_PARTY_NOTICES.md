# Third-party notices

This project contains no vendored third-party source code.

## Runtime dependencies

| Package | Version constraint | License | Purpose |
|---|---|---|---|
| [PyYAML](https://pypi.org/project/PyYAML/) | `>=6.0,<7` | MIT | Load trust profiles |

## Development-only dependencies

Installed via the `dev` extra; not required at runtime.

| Package | Version constraint | License | Purpose |
|---|---|---|---|
| [pytest](https://pypi.org/project/pytest/) | `>=8` | MIT | Test runner |
| [ruff](https://pypi.org/project/ruff/) | `>=0.6` | MIT | Linter and formatter |
| [mypy](https://pypi.org/project/mypy/) | `>=1.10` | MIT | Static type checking |
| [types-PyYAML](https://pypi.org/project/types-PyYAML/) | `>=6.0` | Apache-2.0 | Type stubs for PyYAML |
| [setuptools](https://pypi.org/project/setuptools/) | `>=77` | MIT | Build backend and editable installs |

## Specification references

The `claude-4hop` profile records behaviour documented at
<https://code.claude.com/docs/en/memory>. No text or code from that documentation is
copied here; the profile only encodes the documented limits as configuration data.

`AGENTS.md` is a format associated with the Agentic AI Foundation. This project does
not claim that name or brand.
