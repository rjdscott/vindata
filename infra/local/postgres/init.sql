-- Bootstrap extensions for the local PoC database, and create Dagster's
-- own DB so it does not collide on the shared alembic_version table.
-- Idempotent so re-runs (and CI test DBs) are safe.

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Dagster keeps its run / event / schedule storage in a separate database
-- so it does not contend with the application's alembic_version table.
-- This script runs once at first postgres volume creation; subsequent
-- `make up` runs skip it. `\gexec` makes it idempotent in case it ever
-- runs twice (e.g. against a clean test DB).
SELECT 'CREATE DATABASE dagster OWNER vindata'
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'dagster')
\gexec

-- One health-check row to confirm extensions resolved.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
        RAISE EXCEPTION 'timescaledb extension failed to install';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'postgis') THEN
        RAISE EXCEPTION 'postgis extension failed to install';
    END IF;
END
$$;
