"""Reference resolver for @path imports in AGENTS.md files."""

from .parser import Import, SyntaxIssue, parse
from .profile import Profile, ProfileError, builtin, builtin_names, load
from .resolver import ResolveError, ResolveResult, resolve
from .vectors import VerifyReport, verify

__version__ = "0.1.0"

__all__ = [
    "Import",
    "Profile",
    "ProfileError",
    "ResolveError",
    "ResolveResult",
    "SyntaxIssue",
    "VerifyReport",
    "__version__",
    "builtin",
    "builtin_names",
    "load",
    "parse",
    "resolve",
    "verify",
]
