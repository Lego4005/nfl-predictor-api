#!/bin/bash

# Memory-Enhanced Prediction System - Test Runner
# Comprehensive test execution script with multiple run modes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_MODE="all"
VERBOSE=false
COVERAGE=false
PARALLEL=false

# Function to print colored output
print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  Memory-Enhanced Prediction System - Test Suite              ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 is not installed"
        exit 1
    fi

    # Check pytest
    if ! python3 -m pytest --version &> /dev/null; then
        print_error "pytest is not installed. Run: pip install pytest pytest-asyncio"
        exit 1
    fi

    # Check database connection
    if [ -z "$DB_HOST" ]; then
        print_info "DB_HOST not set, using localhost"
        export DB_HOST=localhost
    fi

    print_success "Prerequisites check passed"
    echo ""
}

# Function to run tests
run_tests() {
    local test_path=$1
    local test_name=$2

    print_info "Running $test_name..."

    # Build pytest command
    local pytest_cmd="python3 -m pytest $test_path"

    if [ "$VERBOSE" = true ]; then
        pytest_cmd="$pytest_cmd -v -s"
    fi

    if [ "$COVERAGE" = true ]; then
        pytest_cmd="$pytest_cmd --cov=src.ml --cov-report=html --cov-report=term"
    fi

    if [ "$PARALLEL" = true ]; then
        pytest_cmd="$pytest_cmd -n auto"
    fi

    pytest_cmd="$pytest_cmd --asyncio-mode=auto"

    echo "Command: $pytest_cmd"
    echo ""

    if eval $pytest_cmd; then
        print_success "$test_name completed successfully"
        return 0
    else
        print_error "$test_name failed"
        return 1
    fi
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --mode)
                TEST_MODE="$2"
                shift 2
                ;;
            --verbose|-v)
                VERBOSE=true
                shift
                ;;
            --coverage|-c)
                COVERAGE=true
                shift
                ;;
            --parallel|-p)
                PARALLEL=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Show help
show_help() {
    echo "Usage: ./run_memory_tests.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --mode <mode>      Test mode: all, unit, integration, performance, comparison, edge"
    echo "  --verbose, -v      Verbose output"
    echo "  --coverage, -c     Generate coverage report"
    echo "  --parallel, -p     Run tests in parallel"
    echo "  --help, -h         Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_memory_tests.sh --mode all --verbose"
    echo "  ./run_memory_tests.sh --mode unit --coverage"
    echo "  ./run_memory_tests.sh --mode performance --parallel"
}

# Main execution
main() {
    print_header
    parse_args "$@"
    check_prerequisites

    local test_file="tests/test_memory_enhanced_predictions.py"
    local failed=0

    case $TEST_MODE in
        all)
            print_info "Running ALL tests (16 tests)"
            echo ""
            run_tests "$test_file" "Complete Test Suite" || failed=1
            ;;

        unit)
            print_info "Running UNIT tests (4 tests)"
            echo ""
            run_tests "$test_file::TestMemoryRetrievalIntegration" "Unit Tests" || failed=1
            ;;

        integration)
            print_info "Running INTEGRATION tests (4 tests)"
            echo ""
            run_tests "$test_file::TestMemoryEnhancedPredictionFlow" "Integration Tests" || failed=1
            ;;

        performance)
            print_info "Running PERFORMANCE tests (3 tests)"
            echo ""
            run_tests "$test_file::TestMemoryPerformance" "Performance Tests" || failed=1
            ;;

        comparison)
            print_info "Running COMPARISON tests (2 tests)"
            echo ""
            run_tests "$test_file::TestBaselineVsMemoryEnhanced" "Comparison Tests" || failed=1
            ;;

        edge)
            print_info "Running EDGE CASE tests (3 tests)"
            echo ""
            run_tests "$test_file::TestMemoryEdgeCases" "Edge Case Tests" || failed=1
            ;;

        *)
            print_error "Invalid test mode: $TEST_MODE"
            show_help
            exit 1
            ;;
    esac

    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"

    if [ $failed -eq 0 ]; then
        print_success "All tests passed! 🎉"

        if [ "$COVERAGE" = true ]; then
            echo ""
            print_info "Coverage report generated: htmlcov/index.html"
        fi
    else
        print_error "Some tests failed"
        exit 1
    fi

    echo -e "${BLUE}════════════════════════════════════════════════════════════════${NC}"
}

# Run main function
main "$@"