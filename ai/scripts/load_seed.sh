#!/usr/bin/env bash
# Load the PAA demo seed into the ai/ database (Docker Postgres).
#
# Prerequisites:
#   - `docker compose up` is running (postgres on localhost:5433).
#   - The PAA schema exists. Apply it once from the host venv (the container's
#     baked Alembic may be older than migration 002):
#       cd ai
#       ALEMBIC_DB_URL="postgresql://shb:shb-password@localhost:5433/shb" \
#         .venv/Scripts/python.exe -c "import sys,os; \
#           sys.path=[p for p in sys.path if p not in ('', os.getcwd())]; \
#           from alembic.config import main; sys.argv=['alembic','upgrade','head']; main()"
#
# Then run this script from the ai/ directory:  bash scripts/load_seed.sh
set -euo pipefail

SRC="../apps/datasource/paa_seed_data.sql"
OUT="scripts/paa_seed_data.ai.sql"
PY=".venv/Scripts/python.exe"

echo "1/3  Transforming seed (paa. -> public, ARRAY[] -> array_to_json) ..."
"$PY" scripts/transform_seed.py "$SRC" "$OUT"

echo "2/3  Adding server defaults for UUID id columns (preamble) ..."
docker compose exec -T postgres psql -U shb -d shb -v ON_ERROR_STOP=1 < scripts/seed_preamble.sql

echo "3/3  Loading seed (atomic BEGIN/COMMIT) ..."
docker compose exec -T -e PGCLIENTENCODING=UTF8 postgres psql -U shb -d shb -v ON_ERROR_STOP=1 < "$OUT"

echo "Done. Verifying counts:"
docker compose exec -T postgres psql -U shb -d shb -c \
  "SELECT 'lookup_finding' t, count(*) FROM lookup_finding
   UNION ALL SELECT 'market_comparable', count(*) FROM market_comparable
   UNION ALL SELECT 'appraisal_case', count(*) FROM appraisal_case;"
