#!/bin/bash
# Monitor the learning test progress

echo "=== Learning Test Monitor ==="
echo ""

# Check if test is running
if pgrep -f "test_2025_sequential_learning.py" > /dev/null; then
    echo "✅ Test is RUNNING"
    echo ""

    # Show progress
    echo "📊 Progress:"
    games_completed=$(grep -c "Game [0-9]*/64" /tmp/fresh_test_run.txt 2>/dev/null || echo "0")
    echo "   Games processed: $games_completed/64"

    predictions=$(grep -c "✅ Logged reasoning chain" /tmp/fresh_test_run.txt 2>/dev/null || echo "0")
    echo "   Predictions logged: $predictions"

    errors=$(grep -c "⚠️" /tmp/fresh_test_run.txt 2>/dev/null || echo "0")
    echo "   Warnings: $errors"

    echo ""
    echo "📝 Latest output:"
    tail -15 /tmp/fresh_test_run.txt 2>/dev/null | grep -E "Game|Consensus|Correct|Expert" || echo "   (waiting for game output...)"

else
    echo "❌ Test is NOT running"
    echo ""

    # Check if it completed
    if grep -q "FINAL RESULTS" /tmp/fresh_test_run.txt 2>/dev/null; then
        echo "✅ Test COMPLETED!"
        echo ""
        echo "📊 Final Results:"
        grep -A 20 "FINAL RESULTS" /tmp/fresh_test_run.txt | head -25
    else
        echo "⚠️  Test may have stopped early"
        echo ""
        echo "Last 10 lines:"
        tail -10 /tmp/fresh_test_run.txt 2>/dev/null
    fi
fi

echo ""
echo "==========================="
echo "Run this script again to check progress: bash scripts/monitor_learning_test.sh"