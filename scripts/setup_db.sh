#!/usr/bin/env bash
# Create the vectorbrain role + database on a local PostgreSQL install.
# Usage: ./scripts/setup_db.sh   (uses peer/trust auth as the current OS user,
# or set PGHOST/PGUSER/PGPASSWORD env vars first)
set -euo pipefail

DB_USER="${DB_USER:-vectorbrain}"
DB_PASS="${DB_PASS:-vectorbrain}"
DB_NAME="${DB_NAME:-vectorbrain}"

psql -v ON_ERROR_STOP=1 -d postgres <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DB_USER}') THEN
    CREATE ROLE ${DB_USER} WITH LOGIN PASSWORD '${DB_PASS}' CREATEDB;
  END IF;
END
\$\$;
SELECT 'role ready' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${DB_NAME}');
SQL

createdb -O "${DB_USER}" "${DB_NAME}" 2>/dev/null || echo "database ${DB_NAME} already exists"
psql -d "${DB_NAME}" -c "CREATE EXTENSION IF NOT EXISTS vector;"
echo "Done. DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@localhost:5432/${DB_NAME}"
