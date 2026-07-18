"""Transform the PAA demo seed (apps/datasource/paa_seed_data.sql) into a form
compatible with the ``ai/`` database created by Alembic migration 002.

Two incompatibilities are fixed:

1. **Schema prefix** — the source seed targets a ``paa`` Postgres schema
   (``INSERT INTO paa.lookup_finding`` + ``SET search_path TO paa, public``),
   but the ``ai/`` models/migration create the tables in the default (``public``)
   schema. We drop the ``search_path`` statement and strip the ``paa.`` prefix.

2. **Array literals → JSON** — bullet-list columns (``raw_findings``, ``inputs``)
   are ``sa.JSON`` in ``ai/`` (portable to SQLite), not Postgres ``text[]``. The
   seed writes them as ``ARRAY['a','b']``; we wrap each with
   ``array_to_json(ARRAY['a','b'])`` so Postgres converts them to a JSON value the
   column accepts — deferring all string escaping to Postgres itself.

Usage:
    python scripts/transform_seed.py \
        ../apps/datasource/paa_seed_data.sql \
        scripts/paa_seed_data.ai.sql
"""

from __future__ import annotations

import sys
from pathlib import Path


def wrap_array_literals(sql: str) -> str:
    """Wrap every ``ARRAY[...]`` with ``array_to_json(...)``.

    Scans character by character so a ``]`` or ``[`` appearing *inside* a quoted
    element string does not prematurely end the match. SQL single-quote escaping
    (``''``) is respected.
    """
    out: list[str] = []
    i, n = 0, len(sql)
    while i < n:
        idx = sql.find("ARRAY[", i)
        if idx == -1:
            out.append(sql[i:])
            break
        out.append(sql[i:idx])

        j = idx + len("ARRAY[")  # first char inside the brackets
        depth = 1
        in_str = False
        while j < n and depth > 0:
            c = sql[j]
            if in_str:
                if c == "'":
                    if j + 1 < n and sql[j + 1] == "'":  # escaped quote ''
                        j += 2
                        continue
                    in_str = False
                j += 1
            else:
                if c == "'":
                    in_str = True
                    j += 1
                elif c == "[":
                    depth += 1
                    j += 1
                elif c == "]":
                    depth -= 1
                    if depth == 0:
                        break
                    j += 1
                else:
                    j += 1

        array_literal = sql[idx : j + 1]  # includes the closing ]
        out.append(f"array_to_json({array_literal})")
        i = j + 1
    return "".join(out)


def transform(sql: str) -> str:
    """Apply the schema-prefix and array→JSON fixes to the raw seed SQL."""
    lines = [
        ln for ln in sql.splitlines(keepends=True) if not ln.lstrip().startswith("SET search_path")
    ]
    sql = "".join(lines)
    sql = sql.replace("paa.", "")  # INSERT INTO paa.x -> INSERT INTO x
    sql = wrap_array_literals(sql)
    return sql


def main() -> None:
    if len(sys.argv) != 3:
        print("usage: python scripts/transform_seed.py <src.sql> <dst.sql>", file=sys.stderr)
        raise SystemExit(2)

    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    raw = src.read_text(encoding="utf-8")
    result = transform(raw)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(result, encoding="utf-8")

    arrays = result.count("array_to_json(")
    inserts = result.count("INSERT INTO ")
    print(f"Wrote {dst} — {inserts} INSERTs, {arrays} array_to_json wraps.")


if __name__ == "__main__":
    main()
