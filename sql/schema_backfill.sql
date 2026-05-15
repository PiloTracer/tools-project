-- tools-project — data backfill / corrective updates for existing rows.
-- Runs after bootstrap (local superuser may exist). Keep statements idempotent.
-- Example patterns:
--   UPDATE ... WHERE ... AND old_column IS NULL;
--   INSERT ... SELECT ... WHERE NOT EXISTS (...);

-- (no mandatory backfills yet — extend when migrating live data forward)
