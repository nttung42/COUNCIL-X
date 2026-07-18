"""Database package.

Importing ``shb.db.models_paa`` here (as a side effect of importing this
package) guarantees the PAA domain tables are always registered on
``Base.metadata`` — whether that metadata is consumed by Alembic
(``alembic/env.py`` does ``from shb.db.models import Base``, which triggers
this ``__init__`` first) or by tests (``tests/conftest.py`` calls
``Base.metadata.create_all`` against an in-memory SQLite engine). No other
module needs to import ``models_paa`` directly.
"""

from shb.db import models_paa  # noqa: F401
from shb.db.models import Base  # noqa: F401

__all__ = ["Base"]
