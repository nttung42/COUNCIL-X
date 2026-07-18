#!/usr/bin/env bash
# Export the CURRENT running Postgres data into ai/'s own self-contained seed
# file (scripts/paa_seed.sql). This is how paa_seed.sql is (re)generated —
# ai/ owns its seed; it no longer derives from apps/datasource.
#
# Snapshots data only (INSERTs) for every table EXCEPT:
#   - alembic_version        (schema version, managed by `alembic upgrade`)
#   - risk_ltv_policy_band    (seeded by migration 002 — reloading would clash)
# JSON columns are already stored as JSON in the DB, so NO transform is needed:
# the dump reloads as-is onto a fresh schema (verify with scripts/load_seed.sh).
#
# Run from ai/ with `docker compose up` running:  bash scripts/dump_seed.sh
set -euo pipefail

OUT="scripts/paa_seed.sql"

echo "Dumping data from running Postgres -> $OUT ..."
docker compose exec -T -e PGCLIENTENCODING=UTF8 postgres pg_dump -U shb -d shb \
  --data-only --column-inserts --no-owner --no-privileges \
  --exclude-table=alembic_version --exclude-table=risk_ltv_policy_band \
  > "$OUT"

echo "Done. $(grep -c '^INSERT INTO' "$OUT") INSERTs written."
