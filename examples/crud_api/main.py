"""Boot the ``examples/crud_api`` notes service.

Run from the repo root:

    python examples/crud_api/main.py

The app listens on ``http://127.0.0.1:5000``. Point curl at
``/api/Application/Notes`` to exercise the CQRS flow — see
``examples/crud_api/README.md`` for sample requests.
"""

import os
import sys

# When invoked as ``python examples/crud_api/main.py`` Python adds
# only the script's own directory to ``sys.path``. Prepend the repo
# root so the absolute imports below (``from examples.crud_api…``)
# resolve the same way they do under ``unittest`` / pytest.
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from pdip.api.app import FlaskAppWrapper  # noqa: E402
from pdip.base import Pdi  # noqa: E402
from pdip.data.base import DatabaseSessionManager  # noqa: E402

from examples.crud_api.domain.base import Base  # noqa: E402


def main() -> None:
    # Pdi() walks the project tree, discovers every ISingleton /
    # IScoped subclass (resource, handler, specification, entity),
    # and registers them in the injector container. See ADR-0015.
    pdi = Pdi()

    # Provision the SQLite schema once. A production app would run
    # migrations (Alembic) or pdip's seed-runner here instead.
    engine = pdi.get(DatabaseSessionManager).engine
    Base.metadata.create_all(engine)

    # FlaskAppWrapper owns the Flask app + Flask-Restx Api. Auto-
    # mounts every ResourceBase found in the project under
    # /api/<package>/<resource> (ADR-0008).
    app = pdi.get(FlaskAppWrapper)
    app.run(host="127.0.0.1", port=5000)


if __name__ == "__main__":
    main()
