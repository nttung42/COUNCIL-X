#!/usr/bin/env bash
# Load ai/'s self-contained PAA demo seed (scripts/paa_seed.sql) into the
# ai/ database (Docker Postgres). The seed is a plain pg_dump snapshot — no
# transform, no dependency on apps/. Regenerate it with scripts/dump_seed.sh.
#
# Prerequisites:
#   - `docker compose up` is running.
#   - The PAA schema exists. Apply it once from the host venv (the container's
#     baked Alembic may be older than migration 002):
#       cd ai
#       ALEMBIC_DB_URL="postgresql://shb:shb-password@localhost:5433/shb" \
#         .venv/Scripts/python.exe -c "import sys,os; \
#           sys.path=[p for p in sys.path if p not in ('', os.getcwd())]; \
#           from alembic.config import main; sys.argv=['alembic','upgrade','head']; main()"
#     (migration 002 also seeds the 4 risk_ltv_policy_band rows.)
#
# Then run from ai/ :  bash scripts/load_seed.sh
set -euo pipefail

SEED="scripts/paa_seed.sql"

echo "Loading $SEED into Postgres (ON_ERROR_STOP) ..."
docker compose exec -T -e PGCLIENTENCODING=UTF8 postgres \
  psql -U shb -d shb -q -v ON_ERROR_STOP=1 < "$SEED"

echo "Done. Verifying counts:"
docker compose exec -T postgres psql -U shb -d shb -c \
  "SELECT 'appraisal_case' t, count(*) FROM appraisal_case
   UNION ALL SELECT 'lookup_finding', count(*) FROM lookup_finding
   UNION ALL SELECT 'market_comparable', count(*) FROM market_comparable
   UNION ALL SELECT 'valuation_result', count(*) FROM valuation_result
   UNION ALL SELECT 'risk_assessment_result', count(*) FROM risk_assessment_result
   UNION ALL SELECT 'dashboard_step_summary', count(*) FROM dashboard_step_summary;"
