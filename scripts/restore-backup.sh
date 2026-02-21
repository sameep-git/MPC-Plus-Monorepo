#!/bin/bash
# scripts/restore-backup.sh

# Ensure script is run from project root
cd "$(dirname "$0")/.."

echo "Restoring database from backup..."

if [ ! -f "backups/mpc_backup.sql" ]; then
    echo "Error: backups/mpc_backup.sql not found!"
    exit 1
fi

echo "Stopping database..."
docker-compose stop db
docker-compose rm -f db

echo "Removing old data volume..."
docker volume rm seniordesign_pgdata 2>/dev/null || docker volume rm mpc-plus_pgdata 2>/dev/null || echo "Volume might be named differently, check 'docker volume ls'"

echo "Starting database (this will trigger restore from backup)..."
docker-compose up -d db

echo "Database restoring... check logs with: docker-compose logs -f db"
