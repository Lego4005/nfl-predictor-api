#!/bin/bash
# Complete Memory System Test Runner
# Run this after reloading the Supabase schema cache

set -e  # Exit on error

echo "════════════════════════════════════════════════════════════════"
echo "  🧪 EPISODIC MEMORY SYSTEM - COMPLETE TEST SUITE"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0

run_test() {
    local test_name="$1"
    local test_command="$2"

    echo ""
    echo "────────────────────────────────────────────────────────────────"
    echo -e "${BLUE}▶ $test_name${NC}"
    echo "────────────────────────────────────────────────────────────────"

    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASSED: $test_name${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAILED: $test_name${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Step 0: Check schema cache status
echo -e "${YELLOW}⚠️  PREREQUISITE: Schema cache must be reloaded${NC}"
echo ""
echo "Have you reloaded the schema cache? (y/n)"
echo "  SQL: NOTIFY pgrst, 'reload schema';"
echo "  OR: Settings → Database → Restart database"
echo ""
read -p "Continue? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${YELLOW}Please reload the schema cache first, then run this script again.${NC}"
    echo ""
    echo "Instructions:"
    echo "1. Go to Supabase Dashboard SQL Editor"
    echo "2. Run: NOTIFY pgrst, 'reload schema';"
    echo "3. Wait 10 seconds"
    echo "4. Run this script again"
    exit 1
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  STARTING TEST SUITE"
echo "════════════════════════════════════════════════════════════════"

# Step 1: Verify schema
run_test "Schema Verification" "python3 scripts/check_database_schema.py 2>&1 | grep -q 'All tables exist'"

# Step 2: Create test expert (if needed)
echo ""
echo "────────────────────────────────────────────────────────────────"
echo -e "${BLUE}▶ Creating Test Expert (if needed)${NC}"
echo "────────────────────────────────────────────────────────────────"
python3 scripts/create_test_expert.py || true
echo ""

# Step 3: Run comprehensive test suite
run_test "Comprehensive Test Suite (6 tests)" "timeout 120 python3 tests/test_episodic_memory_system.py 2>&1 | tee /tmp/memory_test_results.log | grep -q 'ALL TESTS PASSED'" || true

# Step 4: Run memory journey demonstration
echo ""
echo "────────────────────────────────────────────────────────────────"
echo -e "${BLUE}▶ Memory-Enabled Learning Journey${NC}"
echo "────────────────────────────────────────────────────────────────"
python3 scripts/supabase_memory_journey.py 2>&1 | tee /tmp/memory_journey.log
echo ""

# Check if journey succeeded
if grep -q "SUCCESS! Memory system is fully functional" /tmp/memory_journey.log; then
    echo -e "${GREEN}✅ PASSED: Memory Journey${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${RED}❌ FAILED: Memory Journey${NC}"
    ((TESTS_FAILED++))
fi

# Step 5: Run diagnostics
echo ""
echo "────────────────────────────────────────────────────────────────"
echo -e "${BLUE}▶ System Diagnostics${NC}"
echo "────────────────────────────────────────────────────────────────"
python3 scripts/diagnose_memory_system.py 2>&1 | tee /tmp/diagnostics.log || true
echo ""

# Check diagnostics verdict
if grep -q "HYPOTHESIS 1: GENUINE LEARNING" /tmp/diagnostics.log; then
    echo -e "${GREEN}✅ PASSED: System Diagnostics${NC}"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠️  WARNING: Diagnostics inconclusive${NC}"
fi

# Final summary
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  📊 FINAL TEST SUMMARY"
echo "════════════════════════════════════════════════════════════════"
echo ""

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))

echo "Total Tests Run: $TOTAL_TESTS"
echo -e "${GREEN}✅ Passed: $TESTS_PASSED${NC}"
echo -e "${RED}❌ Failed: $TESTS_FAILED${NC}"

if [ $TESTS_PASSED -eq $TOTAL_TESTS ]; then
    SUCCESS_RATE=100
else
    SUCCESS_RATE=$((TESTS_PASSED * 100 / TOTAL_TESTS))
fi

echo "Success Rate: $SUCCESS_RATE%"
echo ""

# Final verdict
if [ $TESTS_FAILED -eq 0 ]; then
    echo "════════════════════════════════════════════════════════════════"
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "✅ Memory system is fully operational!"
    echo "✅ Experts can learn from experience"
    echo "✅ Memories, lessons, and principles are stored correctly"
    echo ""
    echo "Next steps:"
    echo "  - View stored memories in Supabase Dashboard"
    echo "  - Compare learning curves with baseline"
    echo "  - Deploy to production with confidence"
    echo ""
    exit 0
else
    echo "════════════════════════════════════════════════════════════════"
    echo -e "${YELLOW}⚠️  SOME TESTS FAILED${NC}"
    echo "════════════════════════════════════════════════════════════════"
    echo ""
    echo "Check logs for details:"
    echo "  - /tmp/memory_test_results.log"
    echo "  - /tmp/memory_journey.log"
    echo "  - /tmp/diagnostics.log"
    echo ""
    echo "Common issues:"
    echo "  1. Schema cache not reloaded → Run: NOTIFY pgrst, 'reload schema';"
    echo "  2. Test expert missing → Run: python3 scripts/create_test_expert.py"
    echo "  3. Wrong credentials → Check .env file"
    echo ""
    exit 1
fi