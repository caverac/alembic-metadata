#!/bin/bash
# Run the demonstration scripts

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "========================================"
echo "Setting up virtual environment..."
echo "========================================"
python3.13 -m venv .venv
source .venv/bin/activate

echo ""
echo "========================================"
echo "Installing packages in development mode..."
echo "========================================"
pip install -e packages/models
pip install -e packages/consumer

echo ""
echo "========================================"
echo "Running demonstration scripts..."
echo "========================================"

echo ""
echo "--- demonstrate_problem.py ---"
python scripts/demonstrate_problem.py

echo ""
echo "--- demonstrate_solution.py ---"
python scripts/demonstrate_solution.py

echo ""
echo "========================================"
echo "Demo complete!"
echo "========================================"
