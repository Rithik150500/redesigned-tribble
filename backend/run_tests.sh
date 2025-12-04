#!/bin/bash
# Test Runner Script for Legal Risk Analysis System
# Provides convenient commands for running different test suites

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored message
print_message() {
    color=$1
    message=$2
    echo -e "${color}${message}${NC}"
}

# Check if virtual environment is activated
check_venv() {
    if [[ -z "$VIRTUAL_ENV" ]]; then
        print_message "$YELLOW" "⚠️  Virtual environment not activated"
        print_message "$YELLOW" "   Run: source venv/bin/activate"
        exit 1
    fi
}

# Show usage
show_usage() {
    cat << EOF
Legal Risk Analysis System - Test Runner

Usage: ./run_tests.sh [COMMAND]

Commands:
  all              Run all tests (default)
  layer1           Run Layer 1 tests (Document Processing)
  layer2           Run Layer 2 tests (MCP Server)
  layer3           Run Layer 3 tests (Agent System)
  layer4           Run Layer 4 tests (Web Interface)
  integration      Run integration tests
  fast             Run all tests except slow ones
  coverage         Run with coverage report
  watch            Watch mode - rerun on file changes
  help             Show this help message

Examples:
  ./run_tests.sh                 # Run all tests
  ./run_tests.sh layer1          # Run only Layer 1 tests
  ./run_tests.sh coverage        # Run with coverage
  ./run_tests.sh fast            # Skip slow tests

EOF
}

# Run all tests
run_all() {
    print_message "$BLUE" "▶ Running All Tests"
    pytest tests/ -v --tb=short
}

# Run Layer 1 tests
run_layer1() {
    print_message "$BLUE" "▶ Running Layer 1: Document Processing & Database"
    pytest tests/test_layer1_document_processing.py -v
}

# Run Layer 2 tests
run_layer2() {
    print_message "$BLUE" "▶ Running Layer 2: MCP Document Analysis Server"
    pytest tests/test_layer2_mcp_server.py -v
}

# Run Layer 3 tests
run_layer3() {
    print_message "$BLUE" "▶ Running Layer 3: Deep Agent Orchestration"
    pytest tests/test_layer3_agent_system.py -v
}

# Run Layer 4 tests
run_layer4() {
    print_message "$BLUE" "▶ Running Layer 4: Web Interface"
    pytest tests/test_layer4_web_interface.py -v
}

# Run integration tests
run_integration() {
    print_message "$BLUE" "▶ Running Integration Tests"
    pytest tests/test_integration.py -v
}

# Run fast tests (skip slow ones)
run_fast() {
    print_message "$BLUE" "▶ Running Fast Tests (excluding slow tests)"
    pytest tests/ -v -m "not slow"
}

# Run with coverage
run_coverage() {
    print_message "$BLUE" "▶ Running Tests with Coverage"

    # Check if pytest-cov is installed
    if ! python -c "import pytest_cov" 2>/dev/null; then
        print_message "$YELLOW" "⚠️  pytest-cov not installed"
        print_message "$YELLOW" "   Installing: pip install pytest-cov"
        pip install pytest-cov
    fi

    pytest tests/ -v \
        --cov=. \
        --cov-report=term-missing \
        --cov-report=html \
        --cov-config=.coveragerc

    print_message "$GREEN" "✓ Coverage report generated in htmlcov/"
    print_message "$GREEN" "  Open htmlcov/index.html to view"
}

# Watch mode - rerun tests on file changes
run_watch() {
    print_message "$BLUE" "▶ Running in Watch Mode"
    print_message "$BLUE" "  Tests will rerun when files change"
    print_message "$BLUE" "  Press Ctrl+C to exit"

    # Check if pytest-watch is installed
    if ! command -v pytest-watch &> /dev/null; then
        print_message "$YELLOW" "⚠️  pytest-watch not installed"
        print_message "$YELLOW" "   Installing: pip install pytest-watch"
        pip install pytest-watch
    fi

    pytest-watch tests/ -- -v
}

# Main script logic
main() {
    # Check virtual environment
    check_venv

    # Get command (default to "all")
    command="${1:-all}"

    print_message "$GREEN" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    print_message "$GREEN" "  Legal Risk Analysis System - Tests"
    print_message "$GREEN" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    case "$command" in
        all)
            run_all
            ;;
        layer1)
            run_layer1
            ;;
        layer2)
            run_layer2
            ;;
        layer3)
            run_layer3
            ;;
        layer4)
            run_layer4
            ;;
        integration)
            run_integration
            ;;
        fast)
            run_fast
            ;;
        coverage)
            run_coverage
            ;;
        watch)
            run_watch
            ;;
        help|--help|-h)
            show_usage
            exit 0
            ;;
        *)
            print_message "$RED" "❌ Unknown command: $command"
            echo ""
            show_usage
            exit 1
            ;;
    esac

    # Print results
    if [ $? -eq 0 ]; then
        echo ""
        print_message "$GREEN" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        print_message "$GREEN" "✓ Tests Passed"
        print_message "$GREEN" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    else
        echo ""
        print_message "$RED" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        print_message "$RED" "❌ Tests Failed"
        print_message "$RED" "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        exit 1
    fi
}

# Run main function
main "$@"
