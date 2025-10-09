-- Verification script for Phase 1.4 Pilot Expert Seeding
-- Run ID: run_2025_pilot4
-- Expected: 4 experts (conservative_analyzer, momentum_rider, contrarian_rebel, value_hunter)

\echo '================================================================================'
\echo 'PILOT EXPERT STATE SEEDING VERIFICATION (Phase 1.4)'
\echo '================================================================================'
\echo ''

-- 1. Expert Bankroll Verification
\echo '1. EXPERT BANKROLL INITIALIZATION'
\echo '--------------------------------------------------------------------------------'

SELECT
    '✅ Total bankroll records: ' || COUNT(*)::TEXT || ' (expected: 4)' AS status
FROM expert_bankroll
WHERE run_id = 'run_2025_pilot4';

\echo ''
\echo 'Expert bankroll details:'
SELECT
    expert_id,
    current_units,
    starting_units,
    peak_units,
    total_bets,
    active,
    run_id
FROM expert_bankroll
WHERE run_id = 'run_2025_pilot4'
ORDER BY expert_id;

\echo ''
\echo 'Expected experts check:'
SELECT
    expert_id,
    CASE
        WHEN expert_id IN ('conservative_analyzer', 'momentum_rider', 'contrarian_rebel', 'value_hunter')
        THEN '✅ EXPECTED'
        ELSE '❌ UNEXPECTED'
    END AS status,
    CASE
        WHEN current_units = 100.0 AND starting_units = 100.0
        THEN '✅ CORRECT'
        ELSE '❌ WRONG BANKROLL'
    END AS bankroll_status
FROM expert_bankroll
WHERE run_id = 'run_2025_pilot4'
ORDER BY expert_id;

\echo ''
\echo '--------------------------------------------------------------------------------'
\echo ''

-- 2. Category Calibration Verification
\echo '2. CATEGORY CALIBRATION INITIALIZATION'
\echo '--------------------------------------------------------------------------------'

SELECT
    '✅ Total calibration records: ' || COUNT(*)::TEXT || ' (expected: 332 = 4 experts × 83 categories)' AS status
FROM expert_category_calibration
WHERE run_id = 'run_2025_pilot4';

\echo ''
\echo 'Calibrations per expert:'
SELECT
    expert_id,
    COUNT(*) AS category_count,
    CASE
        WHEN COUNT(*) = 83 THEN '✅ COMPLETE (83 categories)'
        ELSE '❌ INCOMPLETE (expected 83)'
    END AS status
FROM expert_category_calibration
WHERE run_id = 'run_2025_pilot4'
GROUP BY expert_id
ORDER BY expert_id;

\echo ''
\echo 'Beta prior verification (sample - binary categories):'
SELECT
    expert_id,
    category,
    beta_alpha,
    beta_beta,
    CASE
        WHEN beta_alpha = 1.0 AND beta_beta = 1.0
        THEN '✅ CORRECT Beta(1,1)'
        ELSE '❌ INCORRECT'
    END AS status
FROM expert_category_calibration
WHERE run_id = 'run_2025_pilot4'
  AND category IN ('game_winner', 'spread_full_game', 'will_overtime')
ORDER BY expert_id, category
LIMIT 12;

\echo ''
\echo 'EMA prior verification (sample - numeric categories):'
SELECT
    expert_id,
    category,
    ema_mu,
    ema_sigma,
    CASE
        WHEN ema_mu IS NOT NULL AND ema_sigma IS NOT NULL
        THEN '✅ PRIORS SET'
        ELSE '❌ MISSING'
    END AS status
FROM expert_category_calibration
WHERE run_id = 'run_2025_pilot4'
  AND category IN ('home_score_exact', 'qb_passing_yards', 'total_full_game')
ORDER BY expert_id, category
LIMIT 12;

\echo ''
\echo 'Unique categories count:'
SELECT
    '📊 Unique categories: ' || COUNT(DISTINCT category)::TEXT || ' (expected: 83)' AS status
FROM expert_category_calibration
WHERE run_id = 'run_2025_pilot4';

\echo ''
\echo '--------------------------------------------------------------------------------'
\echo ''

-- 3. Expert Eligibility Gates Verification
\echo '3. EXPERT ELIGIBILITY GATES'
\echo '--------------------------------------------------------------------------------'

SELECT
    '✅ Total eligibility gate records: ' || COUNT(*)::TEXT || ' (expected: 4)' AS status
FROM expert_eligibility_gates
WHERE run_id = 'run_2025_pilot4';

\echo ''
\echo 'Eligibility gate details:'
SELECT
    expert_id,
    eligible,
    schema_validity_rate,
    avg_response_time_ms,
    latency_slo_ms,
    validity_slo_rate,
    CASE
        WHEN latency_slo_ms = 6000 AND validity_slo_rate = 0.985
        THEN '✅ CORRECT SLOs'
        ELSE '❌ INCORRECT SLOs'
    END AS slo_status
FROM expert_eligibility_gates
WHERE run_id = 'run_2025_pilot4'
ORDER BY expert_id;

\echo ''
\echo '--------------------------------------------------------------------------------'
\echo ''

-- 4. Summary Report
\echo '================================================================================'
\echo 'VERIFICATION SUMMARY'
\echo '================================================================================'
\echo ''

-- Count checks
WITH counts AS (
    SELECT
        (SELECT COUNT(*) FROM expert_bankroll WHERE run_id = 'run_2025_pilot4') AS bankroll_count,
        (SELECT COUNT(*) FROM expert_category_calibration WHERE run_id = 'run_2025_pilot4') AS calibration_count,
        (SELECT COUNT(*) FROM expert_eligibility_gates WHERE run_id = 'run_2025_pilot4') AS gates_count,
        (SELECT COUNT(DISTINCT category) FROM expert_category_calibration WHERE run_id = 'run_2025_pilot4') AS unique_categories
)
SELECT
    'Run ID: run_2025_pilot4' AS check_1,
    '' AS check_2,
    CASE WHEN bankroll_count = 4 THEN '✅' ELSE '❌' END || ' Bankroll records: ' || bankroll_count::TEXT || '/4' AS check_3,
    CASE WHEN calibration_count = 332 THEN '✅' ELSE '❌' END || ' Calibration records: ' || calibration_count::TEXT || '/332' AS check_4,
    CASE WHEN gates_count = 4 THEN '✅' ELSE '❌' END || ' Eligibility gates: ' || gates_count::TEXT || '/4' AS check_5,
    CASE WHEN unique_categories = 83 THEN '✅' ELSE '⚠️' END || ' Unique categories: ' || unique_categories::TEXT || '/83' AS check_6
FROM counts;

\echo ''
\echo 'Phase 1.4 Requirements Check:'
\echo '  1. Insert expert_bankroll rows (100 units) for 4 pilot experts .............'
SELECT CASE
    WHEN COUNT(*) = 4 AND MIN(current_units) = 100.0 AND MAX(current_units) = 100.0
    THEN '✅ PASS'
    ELSE '❌ FAIL'
END AS requirement_1
FROM expert_bankroll
WHERE run_id = 'run_2025_pilot4';

\echo '  2. Initialize expert_category_calibration priors (Beta α=1,β=1; EMA μ,σ) ...'
SELECT CASE
    WHEN COUNT(*) = 332
    THEN '✅ PASS'
    ELSE '❌ FAIL'
END AS requirement_2
FROM expert_category_calibration
WHERE run_id = 'run_2025_pilot4';

\echo '  3. Set up expert eligibility gates (validity ≥98.5%, latency SLO) ..........'
SELECT CASE
    WHEN COUNT(*) = 4
     AND MIN(validity_slo_rate) = 0.985
     AND MAX(validity_slo_rate) = 0.985
     AND MIN(latency_slo_ms) = 6000
     AND MAX(latency_slo_ms) = 6000
    THEN '✅ PASS'
    ELSE '❌ FAIL'
END AS requirement_3
FROM expert_eligibility_gates
WHERE run_id = 'run_2025_pilot4';

\echo '  4. Pilot experts: conservative_analyzer, momentum_rider, contrarian_rebel, value_hunter'
SELECT CASE
    WHEN COUNT(DISTINCT expert_id) = 4
     AND bool_and(expert_id IN ('conservative_analyzer', 'momentum_rider', 'contrarian_rebel', 'value_hunter'))
    THEN '✅ PASS'
    ELSE '❌ FAIL'
END AS requirement_4
FROM expert_bankroll
WHERE run_id = 'run_2025_pilot4';

\echo ''
\echo '================================================================================'
\echo 'End of verification report'
\echo '================================================================================'
