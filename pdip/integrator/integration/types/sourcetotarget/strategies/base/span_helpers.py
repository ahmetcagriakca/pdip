"""Shared helpers for emitting ADR-0033 §3 adapter-call-site spans
from source-to-target execution strategies.

Both ``singleprocess`` and ``parallelthread`` strategies wrap their
``ConnectionSourceAdapter`` / ``ConnectionTargetAdapter`` call sites
in ``pdip.integrator.source.read`` / ``pdip.integrator.target.write``
spans with the documented ``pdip.connection.type``,
``pdip.connection.driver``, ``pdip.batch.size`` (and on writes
``pdip.rows.written``) attributes. The two helpers below pin the
attribute-resolution logic so the strategies stay consistent.
"""


def attr_name(value):
    """Best-effort stringification for the OTel ``pdip.connection.type``
    attribute — accepts both real enums (``ConnectionTypes.Sql``)
    and the bare strings used by some unit-test stubs."""
    return getattr(value, "name", value if isinstance(value, str) else "")


def resolve_driver(connections):
    """Best-effort ``pdip.connection.driver`` resolution per ADR-0033 §3.

    Looks at the connection-type-specific sub-payload (``Sql`` /
    ``BigData`` / ``WebService``) and reads its
    ``Connection.ConnectorType.name``. Returns ``""`` when the chain
    is incomplete — OTel's ``set_attribute`` rejects ``None`` and the
    span should still emit even when the driver is unresolved (e.g.
    in unit-test stubs that mock the upper layers).
    """
    if connections is None:
        return ""
    for sub_attr in ("Sql", "BigData", "WebService"):
        sub = getattr(connections, sub_attr, None)
        if sub is None:
            continue
        connection = getattr(sub, "Connection", None)
        if connection is None:
            continue
        connector_type = getattr(connection, "ConnectorType", None)
        if connector_type is None:
            continue
        name = getattr(connector_type, "name", None)
        if isinstance(name, str):
            return name
    return ""
