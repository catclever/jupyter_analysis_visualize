#!/bin/bash

# Script to run code save tests
# Usage: ./run_code_save_tests.sh [test_name]
#   test_name can be: flow, debug, or all (default)

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEST_DIR="$PROJECT_ROOT/backend/test"

echo "=========================================="
echo "Code Save Functionality Tests"
echo "=========================================="
echo ""
echo "Project root: $PROJECT_ROOT"
echo "Test directory: $TEST_DIR"
echo ""

# Check if backend server is running
echo "Checking if backend server is running on http://localhost:8000..."
if ! curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
    echo "⚠️  Backend server is not running!"
    echo "Please start the backend server first:"
    echo "  cd backend && python app.py"
    echo ""
    exit 1
fi
echo "✓ Backend server is running"
echo ""

# Determine which test to run
TEST_NAME=${1:-all}

case $TEST_NAME in
    flow)
        echo "Running: Code Save Flow Tests"
        echo "=========================================="
        cd "$PROJECT_ROOT"
        uv run python backend/test/test_code_save_flow.py
        ;;
    debug)
        echo "Running: Code Save Debug Tests"
        echo "=========================================="
        cd "$PROJECT_ROOT"
        uv run python backend/test/test_code_save_debug.py
        ;;
    all)
        echo "Running: All Code Save Tests"
        echo "=========================================="
        echo ""
        echo "[1/2] Running Code Save Flow Tests..."
        cd "$PROJECT_ROOT"
        uv run python backend/test/test_code_save_flow.py
        echo ""
        echo "[2/2] Running Code Save Debug Tests..."
        uv run python backend/test/test_code_save_debug.py
        ;;
    *)
        echo "Unknown test: $TEST_NAME"
        echo "Usage: $0 [flow|debug|all]"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "Tests Complete"
echo "=========================================="
