"""Deterministic validation tooling for Product OS workspaces.

The public names are resolved lazily on first access. Importing them eagerly
would pull PyYAML and jsonschema into every submodule import, including
``product_os.manifest`` — which deliberately depends on nothing beyond the
standard library so that release-manifest verification can run *before* any
dependency is installed from the source being verified. Checking provenance
first and installing second is the point; an eager import here reverses it.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import-time typing only
    from .validator import ValidationReport, validate_workspace

__all__ = ["ValidationReport", "validate_workspace"]
__version__ = "0.1.0"


def __getattr__(name: str) -> object:
    if name in __all__:
        from . import validator

        return getattr(validator, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted([*globals(), *__all__])
