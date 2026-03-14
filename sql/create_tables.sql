-- ──────────────────────────────────────────────────────────────────────────────
-- create_tables.sql – One-time setup for the Data Diagnostic Dashboard
-- ──────────────────────────────────────────────────────────────────────────────
-- Run this against your Neon / Supabase PostgreSQL instance:
--     psql $DATABASE_URL -f sql/create_tables.sql
-- ──────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS app_usage_logs (
    id                    SERIAL       PRIMARY KEY,
    logged_at             TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    file_name             VARCHAR(255) NOT NULL,
    total_rows            INTEGER      NOT NULL,
    total_columns         INTEGER      NOT NULL,
    missing_values_count  INTEGER      NOT NULL
);
