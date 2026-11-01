-- Required for the booking engine's overlap-prevention EXCLUDE constraint
-- (see apps/api/alembic/versions/0001_initial_schema.py). The migration
-- also creates this extension defensively, so this init script matters
-- mainly for a totally fresh container where you'd rather see it exist
-- before Alembic even runs.
CREATE EXTENSION IF NOT EXISTS btree_gist;
