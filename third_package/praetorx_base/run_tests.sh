#!/bin/bash
# Copyright 2025 Lars Weiler
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).
#
# Test runner for praetorx_base module
# Usage: ./run_tests.sh [test_file] [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default configuration
DB_NAME="${DB_NAME:-hausverwaltung}"
CONFIG_FILE="${CONFIG_FILE:-config/odoo.conf}"
ODOO_BIN="${ODOO_BIN:-odoo-bin}"
MODULE="praetorx_base"

# Navigate to project root
cd "$(dirname "$0")/../../.." || exit 1

echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}Praetorx Base - Test Suite${NC}"
echo -e "${GREEN}====================================${NC}"
echo ""

# Check if specific test file requested
if [ -n "$1" ] && [ "$1" != "--help" ] && [ "$1" != "-h" ]; then
    TEST_FILE="$1"
    echo -e "${YELLOW}Running specific test:${NC} $TEST_FILE"
    echo ""

    $ODOO_BIN \
        -c "$CONFIG_FILE" \
        -d "$DB_NAME" \
        --test-tags praetorx \
        --test-file "addons/$MODULE/tests/$TEST_FILE" \
        --log-level test:INFO \
        --stop-after-init
elif [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage: $0 [test_file] [options]"
    echo ""
    echo "Options:"
    echo "  --help, -h           Show this help message"
    echo "  --verbose, -v        Run with verbose output"
    echo "  --debug, -d          Run with debug output"
    echo ""
    echo "Test Files:"
    echo "  test_queue_job.py              Run queue job tests"
    echo "  test_validation_mixin.py       Run validation mixin tests"
    echo "  test_batch_processing_mixin.py Run batch processing tests"
    echo ""
    echo "Examples:"
    echo "  $0                             # Run all tests"
    echo "  $0 test_queue_job.py           # Run specific test file"
    echo "  $0 --verbose                   # Run all with verbose output"
    echo ""
    echo "Environment Variables:"
    echo "  DB_NAME      Database name (default: hausverwaltung)"
    echo "  CONFIG_FILE  Odoo config file (default: config/odoo.conf)"
    echo "  ODOO_BIN     Odoo binary path (default: odoo-bin)"
    exit 0
elif [ "$1" == "--verbose" ] || [ "$1" == "-v" ]; then
    echo -e "${YELLOW}Running all tests with VERBOSE output${NC}"
    echo ""

    $ODOO_BIN \
        -c "$CONFIG_FILE" \
        -d "$DB_NAME" \
        --test-tags praetorx \
        --log-level test:DEBUG \
        --stop-after-init \
        -u "$MODULE"
elif [ "$1" == "--debug" ] || [ "$1" == "-d" ]; then
    echo -e "${YELLOW}Running all tests with DEBUG output${NC}"
    echo ""

    $ODOO_BIN \
        -c "$CONFIG_FILE" \
        -d "$DB_NAME" \
        --test-tags praetorx \
        --log-level debug \
        --stop-after-init \
        -u "$MODULE"
else
    echo -e "${YELLOW}Running ALL praetorx_base tests${NC}"
    echo ""

    $ODOO_BIN \
        -c "$CONFIG_FILE" \
        -d "$DB_NAME" \
        --test-tags praetorx \
        --log-level test:INFO \
        --stop-after-init \
        -u "$MODULE"
fi

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}====================================${NC}"
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo -e "${GREEN}====================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}====================================${NC}"
    echo -e "${RED}✗ Tests failed!${NC}"
    echo -e "${RED}====================================${NC}"
    exit 1
fi
