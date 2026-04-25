"""Internal helper — verifies the ``pdip[async]`` extra is installed.

ADR-0032 §3 requires the connection adapter factories to raise a
clear ``ImportError`` when ``is_async=True`` is asked for but the
async extra was not installed. We use ``asyncpg`` as the canonical
marker because it is the first dependency listed in the
``pdip[async]`` extra in ``setup.py`` and is the most commonly used
async DB driver in the Python ecosystem; the same extra also pulls
``aiomysql``, ``aioodbc``, and ``aiokafka``, but a single marker
is enough to detect a missing extra at the factory boundary.
"""


ASYNC_EXTRA_INSTALL_HINT = (
    "install ``pdip[async]`` to use async adapters "
    "(missing dependency: asyncpg)"
)


def require_async_extra():
    """Return ``None`` when the async extra is importable; raise
    ``ImportError`` with :data:`ASYNC_EXTRA_INSTALL_HINT` otherwise."""
    try:
        import asyncpg  # noqa: F401 — presence check only
    except ImportError as ex:
        raise ImportError(ASYNC_EXTRA_INSTALL_HINT) from ex
    return None
