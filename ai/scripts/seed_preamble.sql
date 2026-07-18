-- Preamble run once before loading paa_seed_data.ai.sql into the ai/ database.
--
-- The ai/ models give UUID-string `id` primary keys a *Python-side* default
-- (models_paa: default=_uuid), which only fires through the ORM. The raw-SQL
-- demo seed omits `id`, so those columns need a *server* default to load.
-- This adds `gen_random_uuid()::text` as the server default for every public
-- table whose text `id` column currently has no default. Harmless for tables
-- the ORM already populates (it keeps sending its own id).

CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- provides gen_random_uuid()

DO $$
DECLARE tbl text;
BEGIN
  FOR tbl IN
    SELECT table_name
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND column_name = 'id'
      AND data_type IN ('character varying', 'text')
      AND column_default IS NULL
  LOOP
    EXECUTE format(
      'ALTER TABLE %I ALTER COLUMN id SET DEFAULT gen_random_uuid()::text', tbl
    );
  END LOOP;
END $$;
