#!/bin/bash
# Database initialization script
# Runs all migrations after schema

set -e

echo "Applying migrations..."
for migration in /docker-entrypoint-initdb.d/migrations/*.sql; do
    if [ -f "$migration" ]; then
        echo "Applying: $migration"
        psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f "$migration" || true
    fi
done

echo "Database initialization complete!"
