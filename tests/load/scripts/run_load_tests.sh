#!/bin/bash
# NFL Predictor Load Testing Runner Script
#
# This script provides a comprehensive interface for running all types of load tests
# against the NFL Predictor Platform.
#
# Usage: ./run_load_tests.sh [test_type] [options]
#

set -e  # Exit on any error

# Configuration
DEFAULT_HOST="http://localhost:8000"
DEFAULT_USERS=100
DEFAULT_SPAWN_RATE=10
DEFAULT_DURATION="5m"
REPORTS_DIR="tests/load/reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Help function
show_help() {
    cat << EOF
NFL Predictor Load Testing Suite

Usage: $0 [TEST_TYPE] [OPTIONS]

TEST TYPES:
  api-load       High-volume API load testing (default: 1000 users)
  websocket      WebSocket stress testing (default: 500 connections)
  ml-performance ML model performance testing
  spike-sudden   Sudden traffic spike simulation
  spike-gradual  Gradual traffic ramp-up testing
  spike-gameday  NFL game day traffic simulation
  endurance      Long-running stability test (30 minutes)
  comprehensive  Run all test types sequentially

OPTIONS:
  -h, --host HOST        Target host (default: $DEFAULT_HOST)
  -u, --users USERS      Number of concurrent users (default: $DEFAULT_USERS)
  -r, --spawn-rate RATE  User spawn rate per second (default: $DEFAULT_SPAWN_RATE)
  -d, --duration TIME    Test duration (e.g., 5m, 300s) (default: $DEFAULT_DURATION)
  -w, --web              Start with web UI instead of headless mode
  -m, --monitoring       Start monitoring dashboard
  --distributed          Run in distributed mode (requires setup)
  --report-only          Generate reports from existing data
  --help                 Show this help message

EXAMPLES:
  # Basic API load test
  $0 api-load --host http://localhost:8000 --users 500

  # WebSocket stress test with monitoring
  $0 websocket --users 1000 --monitoring

  # Game day spike simulation
  $0 spike-gameday --host https://api.example.com

  # Comprehensive testing suite
  $0 comprehensive --duration 10m

  # Web UI mode for interactive testing
  $0 api-load --web --users 200

REPORTS:
  All test reports are saved to: $REPORTS_DIR/
  - HTML reports: locust_report_[timestamp].html
  - CSV data: locust_stats_[timestamp]_*.csv
  - JSON summaries: load_test_report_[timestamp].json

EOF
}

# Check dependencies
check_dependencies() {
    log "Checking dependencies..."

    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed"
    fi

    # Check if Locust is available
    if ! python3 -c "import locust" 2>/dev/null; then
        warn "Locust not found. Installing..."
        pip install -r tests/load/requirements.txt
    fi

    # Check if target host is reachable
    if [[ "$HOST" =~ ^https?:// ]]; then
        log "Checking if target host is reachable: $HOST"
        if ! curl -s --connect-timeout 5 "$HOST/v1/health" > /dev/null; then
            warn "Target host $HOST may not be reachable"
        fi
    fi

    log "Dependencies check completed"
}

# Create reports directory
setup_reports_dir() {
    mkdir -p "$REPORTS_DIR"
    log "Reports will be saved to: $REPORTS_DIR"
}

# Start monitoring dashboard if requested
start_monitoring() {
    if [[ "$MONITORING" == "true" ]]; then
        log "Starting monitoring dashboard..."
        python3 tests/load/monitoring_dashboard.py --host 0.0.0.0 --port 5000 &
        MONITORING_PID=$!
        log "Monitoring dashboard started at http://localhost:5000"
        log "Dashboard PID: $MONITORING_PID"
        sleep 3  # Give dashboard time to start
    fi
}

# Stop monitoring dashboard
stop_monitoring() {
    if [[ -n "$MONITORING_PID" ]]; then
        log "Stopping monitoring dashboard..."
        kill $MONITORING_PID 2>/dev/null || true
    fi
}

# Generate test report
generate_report() {
    local test_type=$1
    local report_file="$REPORTS_DIR/test_summary_${test_type}_${TIMESTAMP}.md"

    log "Generating test summary report..."

    cat > "$report_file" << EOF
# NFL Predictor Load Test Report

## Test Information
- **Test Type**: $test_type
- **Timestamp**: $(date)
- **Target Host**: $HOST
- **Test Configuration**:
  - Users: $USERS
  - Spawn Rate: $SPAWN_RATE users/sec
  - Duration: $DURATION
- **Test Environment**:
  - OS: $(uname -s)
  - CPU Cores: $(nproc)
  - Memory: $(free -h | grep '^Mem' | awk '{print $2}')

## Test Results

Results are available in the following files:
- HTML Report: \`locust_report_${TIMESTAMP}.html\`
- CSV Data: \`locust_stats_${TIMESTAMP}_*.csv\`
- JSON Summary: \`load_test_report_${TIMESTAMP}.json\`

## Performance Analysis

### Key Metrics
- Response Times (avg, p95, p99)
- Request Rate (requests/second)
- Error Rate (percentage)
- Resource Utilization (CPU, Memory)

### Recommendations
1. Review response time trends for performance degradation
2. Check error logs for failed requests
3. Monitor resource usage during peak load
4. Validate cache effectiveness if applicable

## Next Steps
1. Analyze detailed reports for bottlenecks
2. Compare results with previous test runs
3. Implement performance improvements if needed
4. Schedule regular load testing

---
Generated by NFL Predictor Load Testing Suite
EOF

    log "Test summary saved to: $report_file"
}

# Run API load test
run_api_load_test() {
    log "Starting API load test..."

    local locust_file="tests/load/test_api_load.py"
    local html_report="$REPORTS_DIR/locust_report_api_${TIMESTAMP}.html"
    local csv_prefix="$REPORTS_DIR/locust_stats_api_${TIMESTAMP}"

    local cmd="locust -f $locust_file --host $HOST --html $html_report --csv $csv_prefix"

    if [[ "$WEB_MODE" == "true" ]]; then
        cmd="$cmd --web-host 0.0.0.0 --web-port 8089"
        log "Starting Locust web UI at http://localhost:8089"
    else
        cmd="$cmd --headless --users $USERS --spawn-rate $SPAWN_RATE --run-time $DURATION"
    fi

    log "Executing: $cmd"
    eval $cmd

    generate_report "api-load"
}

# Run WebSocket stress test
run_websocket_test() {
    log "Starting WebSocket stress test..."

    # Convert HTTP host to WebSocket
    local ws_host=${HOST/http/ws}

    log "Running WebSocket test against: $ws_host"
    python3 tests/load/test_websocket_load.py --host "$ws_host" --max-connections "$USERS" --test-duration 300

    generate_report "websocket"
}

# Run ML performance test
run_ml_performance_test() {
    log "Starting ML performance test..."

    python3 tests/load/test_ml_performance.py --host "$HOST" --concurrent-requests "$USERS" --test-duration 180

    generate_report "ml-performance"
}

# Run spike tests
run_spike_test() {
    local spike_type=$1
    log "Starting spike test: $spike_type"

    local locust_file="tests/load/test_spike_scenarios.py"
    local html_report="$REPORTS_DIR/locust_report_${spike_type}_${TIMESTAMP}.html"
    local csv_prefix="$REPORTS_DIR/locust_stats_${spike_type}_${TIMESTAMP}"

    local shape_class=""
    case $spike_type in
        "spike-sudden")
            shape_class="SuddenSpikeShape"
            ;;
        "spike-gradual")
            shape_class="GradualRampShape"
            ;;
        "spike-gameday")
            shape_class="GameTimeSpikesShape"
            ;;
    esac

    local cmd="locust -f $locust_file $shape_class --host $HOST --html $html_report --csv $csv_prefix"

    if [[ "$WEB_MODE" == "true" ]]; then
        cmd="$cmd --web-host 0.0.0.0 --web-port 8089"
    else
        cmd="$cmd --headless"
    fi

    log "Executing: $cmd"
    eval $cmd

    generate_report "$spike_type"
}

# Run endurance test
run_endurance_test() {
    log "Starting endurance test (30 minutes)..."

    local locust_file="tests/load/locustfile.py"
    local html_report="$REPORTS_DIR/locust_report_endurance_${TIMESTAMP}.html"
    local csv_prefix="$REPORTS_DIR/locust_stats_endurance_${TIMESTAMP}"

    local cmd="locust -f $locust_file --host $HOST --html $html_report --csv $csv_prefix"

    if [[ "$WEB_MODE" == "true" ]]; then
        cmd="$cmd --web-host 0.0.0.0 --web-port 8089"
    else
        cmd="$cmd --headless --users 300 --spawn-rate 5 --run-time 30m"
    fi

    log "Executing: $cmd"
    eval $cmd

    generate_report "endurance"
}

# Run comprehensive test suite
run_comprehensive_tests() {
    log "Starting comprehensive test suite..."

    # Sequential execution of all test types
    local tests=("api-load" "websocket" "ml-performance" "spike-sudden" "endurance")

    for test in "${tests[@]}"; do
        log "Running $test test..."
        case $test in
            "api-load")
                run_api_load_test
                ;;
            "websocket")
                run_websocket_test
                ;;
            "ml-performance")
                run_ml_performance_test
                ;;
            "spike-sudden")
                run_spike_test "spike-sudden"
                ;;
            "endurance")
                run_endurance_test
                ;;
        esac

        log "$test test completed"
        sleep 30  # Brief pause between tests
    done

    log "Comprehensive test suite completed"
}

# Cleanup function
cleanup() {
    log "Cleaning up..."
    stop_monitoring
}

# Set trap for cleanup
trap cleanup EXIT

# Parse command line arguments
HOST="$DEFAULT_HOST"
USERS="$DEFAULT_USERS"
SPAWN_RATE="$DEFAULT_SPAWN_RATE"
DURATION="$DEFAULT_DURATION"
WEB_MODE="false"
MONITORING="false"
DISTRIBUTED="false"
REPORT_ONLY="false"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        -u|--users)
            USERS="$2"
            shift 2
            ;;
        -r|--spawn-rate)
            SPAWN_RATE="$2"
            shift 2
            ;;
        -d|--duration)
            DURATION="$2"
            shift 2
            ;;
        -w|--web)
            WEB_MODE="true"
            shift
            ;;
        -m|--monitoring)
            MONITORING="true"
            shift
            ;;
        --distributed)
            DISTRIBUTED="true"
            shift
            ;;
        --report-only)
            REPORT_ONLY="true"
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            if [[ -z "$TEST_TYPE" ]]; then
                TEST_TYPE="$1"
            else
                error "Unknown option: $1"
            fi
            shift
            ;;
    esac
done

# Default test type
if [[ -z "$TEST_TYPE" ]]; then
    TEST_TYPE="api-load"
fi

# Main execution
main() {
    log "NFL Predictor Load Testing Suite"
    log "==============================="
    log "Test Type: $TEST_TYPE"
    log "Target Host: $HOST"
    log "Configuration: $USERS users, $SPAWN_RATE spawn rate, $DURATION duration"

    if [[ "$REPORT_ONLY" == "true" ]]; then
        log "Report-only mode - skipping test execution"
        generate_report "$TEST_TYPE"
        exit 0
    fi

    check_dependencies
    setup_reports_dir
    start_monitoring

    case $TEST_TYPE in
        "api-load")
            run_api_load_test
            ;;
        "websocket")
            run_websocket_test
            ;;
        "ml-performance")
            run_ml_performance_test
            ;;
        "spike-sudden"|"spike-gradual"|"spike-gameday")
            run_spike_test "$TEST_TYPE"
            ;;
        "endurance")
            run_endurance_test
            ;;
        "comprehensive")
            run_comprehensive_tests
            ;;
        *)
            error "Unknown test type: $TEST_TYPE"
            ;;
    esac

    log "Load testing completed successfully!"
    log "Check reports in: $REPORTS_DIR"
}

# Run main function
main