#!/bin/bash
# Run the Alembic demonstration with PostgreSQL

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "========================================"
echo "Starting PostgreSQL..."
echo "========================================"
docker compose up -d postgres
sleep 3  # Wait for PostgreSQL to be ready

echo ""
echo "========================================"
echo "Setting up virtual environment..."
echo "========================================"
if [ ! -d ".venv" ]; then
    python -m venv .venv
fi
source .venv/bin/activate

pip install -q -e packages/models
pip install -q -e packages/consumer

echo ""
echo "========================================"
echo "Running Alembic with BROKEN env.py..."
echo "(Notice the table keys don't include schema)"
echo "========================================"
cd packages/consumer
TARGET_SCHEMA=tenant_a alembic revision --autogenerate -m "test broken" --rev-id broken001 2>/dev/null || true

echo ""
echo "========================================"
echo "Running Alembic with FIXED env.py..."
echo "(Notice the table keys now include schema)"
echo "========================================"

# Backup the original and use the fixed version
cp alembic/env.py alembic/env_broken.py
cp alembic/env_fixed.py alembic/env.py

TARGET_SCHEMA=tenant_a alembic revision --autogenerate -m "test fixed" --rev-id fixed001 2>/dev/null || true

# Restore original
mv alembic/env_broken.py alembic/env.py

echo ""
echo "========================================"
echo "Checking generated migrations..."
echo "========================================"
echo ""
echo "--- Broken migration (no schema or wrong schema): ---"
if [ -f alembic/versions/broken001_test_broken.py ]; then
    cat alembic/versions/broken001_test_broken.py
else
    echo "(Migration file not created or failed)"
fi

echo ""
echo "--- Fixed migration (with correct schema): ---"
if [ -f alembic/versions/fixed001_test_fixed.py ]; then
    cat alembic/versions/fixed001_test_fixed.py
else
    echo "(Migration file not created or failed)"
fi

cd "$PROJECT_ROOT"

echo ""
echo "========================================"
echo "Cleaning up..."
echo "========================================"
docker compose down -v 2>/dev/null || true

echo ""
echo "Demo complete!"
