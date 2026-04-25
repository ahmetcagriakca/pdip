"""pdip — Python Data Integrator infrastructures package.

The single source of truth for the package version at runtime is the
:data:`__version__` constant below; it is also part of the documented
public surface (ADR-0034 §1) and therefore the
:class:`RuleADR0036RemovalRespectsDeprecationCycle` quality_guard rule
reads it to decide whether a removed public symbol may be retired in
the current release.

The string is bumped in lockstep with ``setup.py``'s ``env_version``
default — the release process documented in ADR-0024 keeps the two in
sync.
"""

__version__ = "0.8.0"

__all__ = (
    "__version__",
)
