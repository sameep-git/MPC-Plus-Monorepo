#!/bin/bash
# scripts/setup-db.sh

# Ensure script is run from project root
cd "$(dirname "$0")/.."

echo "Setting up local PostgreSQL database..."

# Check if backup exists
if [ ! -f "backups/mpc_backup.sql" ]; then
    echo "Warning: backups/mpc_backup.sql not found."
    echo "You can place your backup file there to auto-restore on first run."
fi

# Start DB
docker-compose up -d db

echo "Database started on port 5432."
echo "Use 'docker-compose logs -f db' to check status."
