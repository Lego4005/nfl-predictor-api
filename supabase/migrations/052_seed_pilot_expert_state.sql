-- Seed pilot state for 4 experts with comprehensive calibration and eligibility gates
-- Migration: 052_seed_pilot_expert_state.sql

-- ========================================
-- 1. Enhanced expert initialization with all 83 categories
-- ========================================

-- Drop and recreate enhanced initialization function
DROP FUNCTION IF EXISTS initialize_pilot_experts(TEXT, TEXT[]);

CREATE OR REPLACE FUNCTION initialize_pilot_experts(
    p_run_id TEXT DEFAULT 'run_2025_pilot4',
    p_expert_ids TEXT[] DEFAULT ARRAY['conservative_analyzer', 'risk_taking_gambler', 'contrarian_rebel', 'value_hunter']
)
RETURNS JSONB AS $$
DECLARE
    expert_id TEXT;
    category_name TEXT;
    result JSONB := jsonb_build_object('run_id', p_run_id, 'experts_initialized', 0);
    expert_count INTEGER := 0;
    category_count INTEGER := 0;

    -- All 83 prediction categories with their calibration parameters
    categories TEXT[] := ARRAY[
        'game_winner', 'home_score_exact', 'away_score_exact', 'margin_of_victory',
        'spread_full_game', 'total_full_game', 'winner_moneyline', 'first_half_winner',
        'first_half_spread', 'first_half_total', 'q1_winner', 'q2_winner', 'q3_winner',
        'q4_winner', 'q1_total', 'q2_total', 'q3_total', 'q4_total', 'first_half_total_points',
        'second_half_total_points', 'highest_scoring_quarter', 'lowest_scoring_quarter',
        'team_total_points_home', 'team_total_points_away', 'first_team_to_score',
        'last_team_to_score', 'team_with_longest_td', 'team_with_most_turnovers',
        'team_with_most_sacks', 'team_with_most_penalties', 'largest_lead_of_game',
        'number_of_lead_changes', 'will_overtime', 'will_safety', 'will_pick_six',
        'will_fumble_return_td', 'will_defensive_td', 'will_special_teams_td',
        'will_punt_return_td', 'will_kickoff_return_td', 'total_turnovers', 'total_sacks',
        'total_penalties', 'longest_touchdown', 'longest_field_goal', 'total_field_goals_made',
        'missed_extra_points', 'qb_passing_yards', 'qb_passing_tds', 'qb_interceptions'
    ];

    -- Additional categories (continuing to 83)
    more_categories TEXT[] := ARRAY[
        'qb_rushing_yards', 'rb_rushing_yards', 'rb_rushing_tds', 'wr_receiving_yards',
        'wr_receptions', 'te_receiving_yards', 'kicker_total_points', 'anytime_td_scorer',
        'first_td_scorer', 'last_td_scorer', 'qb_longest_completion', 'rb_longest_rush',
        'wr_longest_reception', 'kicker_longest_fg', 'defense_interceptions', 'defense_sacks',
        'defense_forced_fumbles', 'qb_fantasy_points', 'top_skill_player_fantasy',
        'live_win_probability', 'next_score_type', 'current_drive_outcome', 'fourth_down_decision',
        'next_team_to_score', 'time_to_next_score_min', 'weather_impact_score',
        'injury_impact_score', 'travel_rest_factor', 'divisional_rivalry_factor',
        'coaching_advantage', 'home_field_advantage_pts', 'momentum_factor', 'public_betting_bias'
    ];

    all_categories TEXT[];
BEGIN
    -- Combine all categories
    all_categories := categories || more_categories;

    -- Initialize bankroll for each expert
    FOREACH expert_id IN ARRAY p_expert_ids
    LOOP
        INSERT INTO expert_bankroll (expert_id, run_id, current_units, starting_units, peak_units)
        VALUES (expert_id, p_run_id, 100.0000, 100.0000, 100.0000)
        ON CONFLICT (expert_id, run_id) DO NOTHING;

        expert_count := expert_count + 1;
    END LOOP;

    -- Initialize category calibration for all 83 categories
    FOREACH expert_id IN ARRAY p_expert_ids
    LOOP
        FOREACH category_name IN ARRAY all_categories
        LOOP
            INSERT INTO expert_category_calibration (
                expert_id,
                run_id,
                category,
                beta_alpha,
                beta_beta,
                ema_mu,
                ema_sigma,
                factor_weight
            )
            VALUES (
                expert_id,
                p_run_id,
                category_name,
                get_category_beta_alpha(category_name),
                get_category_beta_beta(category_name),
                get_category_ema_mu(category_name),
                get_category_ema_sigma(category_name),
                get_category_factor_weight(category_name, expert_id)
            )
            ON CONFLICT (expert_id, run_id, category) DO NOTHING;

            category_count := category_count + 1;
        END LOOP;
    END LOOP;

    result := jsonb_set(result, '{experts_initialized}', to_jsonb(expert_count));
    result := jsonb_set(result, '{categories_initialized}', to_jsonb(category_count));
    result := jsonb_set(result, '{expert_ids}', to_jsonb(p_expert_ids));
    result := jsonb_set(result, '{total_categories}', to_jsonb(array_length(all_categories, 1)));

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 2. Category-specific calibration parameter functions
-- ========================================

-- Function to get Beta alpha parameter by category
CREATE OR REPLACE FUNCTION get_category_beta_alpha(category TEXT)
RETURNS DECIMAL AS $$
BEGIN
    -- Binary/enum categories start with Beta(1,1) - uniform prior
    CASE
        WHEN category IN ('game_winner', 'spread_full_game', 'total_full_game', 'first_half_winner',
                         'will_overtime', 'will_safety', 'will_pick_six', 'will_fumble_return_td',
                         'will_defensive_td', 'will_special_teams_td') THEN
            RETURN 1.0;
        ELSE
            RETURN 1.0; -- Default uniform prior
    END CASE;
END;
$$ LANGUAGE plpgsql;

-- Function to get Beta beta parameter by category
CREATE OR REPLACE FUNCTION get_category_beta_beta(category TEXT)
RETURNS DECIMAL AS $$
BEGIN
    -- Binary/enum categories start with Beta(1,1) - uniform prior
    CASE
        WHEN category IN ('game_winner', 'spread_full_game', 'total_full_game', 'first_half_winner',
                         'will_overtime', 'will_safety', 'will_pick_six', 'will_fumble_return_td',
                         'will_defensive_td', 'will_special_teams_td') THEN
            RETURN 1.0;
        ELSE
            RETURN 1.0; -- Default uniform prior
    END CASE;
END;
$$ LANGUAGE plpgsql;
-- Function to get EMA mu (mean) parameter by category
CREATE OR REPLACE FUNCTION get_category_ema_mu(category TEXT)
RETURNS DECIMAL AS $$
BEGIN
    -- Numeric categories have domain-specific priors
    CASE
        WHEN category IN ('home_score_exact', 'away_score_exact') THEN
            RETURN 21.0; -- Average NFL score
        WHEN category = 'margin_of_victory' THEN
            RETURN 7.0; -- Average margin
        WHEN category LIKE '%total%' THEN
            RETURN 45.0; -- Average total points
        WHEN category = 'qb_passing_yards' THEN
            RETURN 250.0; -- Average QB passing yards
        WHEN category = 'qb_passing_tds' THEN
            RETURN 1.8; -- Average QB TDs
        WHEN category = 'qb_interceptions' THEN
            RETURN 0.8; -- Average QB INTs
        WHEN category = 'rb_rushing_yards' THEN
            RETURN 85.0; -- Average RB rushing yards
        WHEN category = 'wr_receiving_yards' THEN
            RETURN 65.0; -- Average WR receiving yards
        WHEN category = 'wr_receptions' THEN
            RETURN 5.5; -- Average WR receptions
        WHEN category = 'total_turnovers' THEN
            RETURN 2.5; -- Average turnovers per game
        WHEN category = 'total_sacks' THEN
            RETURN 4.5; -- Average sacks per game
        WHEN category LIKE '%impact%' OR category LIKE '%factor%' THEN
            RETURN 0.0; -- Impact factors centered at 0
        ELSE
            RETURN 0.0; -- Default neutral prior
    END CASE;
END;
$$ LANGUAGE plpgsql;

-- Function to get EMA sigma (standard deviation) parameter by category
CREATE OR REPLACE FUNCTION get_category_ema_sigma(category TEXT)
RETURNS DECIMAL AS $$
BEGIN
    -- Numeric categories have domain-specific variance
    CASE
        WHEN category IN ('home_score_exact', 'away_score_exact') THEN
            RETURN 8.0; -- Score variance
        WHEN category = 'margin_of_victory' THEN
            RETURN 10.0; -- Margin variance
        WHEN category LIKE '%total%' THEN
            RETURN 12.0; -- Total points variance
        WHEN category = 'qb_passing_yards' THEN
            RETURN 75.0; -- QB passing variance
        WHEN category = 'qb_passing_tds' THEN
            RETURN 1.2; -- QB TD variance
        WHEN category = 'qb_interceptions' THEN
            RETURN 0.8; -- QB INT variance
        WHEN category = 'rb_rushing_yards' THEN
            RETURN 40.0; -- RB rushing variance
        WHEN category = 'wr_receiving_yards' THEN
            RETURN 35.0; -- WR receiving variance
        WHEN category = 'wr_receptions' THEN
            RETURN 3.0; -- WR reception variance
        WHEN category = 'total_turnovers' THEN
            RETURN 1.5; -- Turnover variance
        WHEN category = 'total_sacks' THEN
            RETURN 2.0; -- Sack variance
        WHEN category LIKE '%impact%' OR category LIKE '%factor%' THEN
            RETURN 0.3; -- Impact factor variance
        ELSE
            RETURN 1.0; -- Default variance
    END CASE;
END;
$$ LANGUAGE plpgsql;
-- Function to get factor weight by category and expert (personality-based priors)
CREATE OR REPLACE FUNCTION get_category_factor_weight(category TEXT, expert_id TEXT)
RETURNS DECIMAL AS $$
BEGIN
    -- Personality-based factor weights based on observed learning patterns
    CASE expert_id
        WHEN 'conservative_analyzer' THEN
            CASE
                WHEN category LIKE '%momentum%' THEN RETURN 0.95; -- Slight down-weight momentum
                WHEN category LIKE '%offensive%' OR category LIKE 'qb_%' OR category LIKE 'rb_%' THEN RETURN 0.90; -- Down-weight offensive efficiency
                WHEN category LIKE '%defensive%' OR category LIKE 'defense_%' THEN RETURN 1.05; -- Slight up-weight defense
                ELSE RETURN 1.00; -- Neutral for other categories
            END CASE;

        WHEN 'risk_taking_gambler' THEN
            CASE
                WHEN category LIKE '%momentum%' THEN RETURN 1.10; -- Up-weight momentum
                WHEN category LIKE '%upset%' OR category = 'margin_of_victory' THEN RETURN 1.05; -- Up-weight upset potential
                WHEN category LIKE '%conservative%' THEN RETURN 0.95; -- Down-weight conservative plays
                ELSE RETURN 1.00;
            END CASE;

        WHEN 'contrarian_rebel' THEN
            CASE
                WHEN category LIKE '%public%' OR category = 'public_betting_bias' THEN RETURN 1.15; -- Strong up-weight public sentiment
                WHEN category LIKE '%consensus%' THEN RETURN 0.85; -- Down-weight consensus plays
                WHEN category LIKE '%narrative%' THEN RETURN 0.90; -- Down-weight popular narratives
                ELSE RETURN 1.00;
            END CASE;

        WHEN 'value_hunter' THEN
            CASE
                WHEN category LIKE '%value%' OR category LIKE '%efficiency%' THEN RETURN 1.10; -- Up-weight value metrics
                WHEN category LIKE '%market%' THEN RETURN 1.05; -- Up-weight market analysis
                WHEN category LIKE '%emotional%' THEN RETURN 0.90; -- Down-weight emotional factors
                ELSE RETURN 1.00;
            END CASE;

        ELSE
            RETURN 1.00; -- Default neutral weight
    END CASE;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 3. Expert eligibility gates and performance tracking
-- ========================================

-- Create expert eligibility tracking table
CREATE TABLE IF NOT EXISTS expert_eligibility_gates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expert_id TEXT NOT NULL,
    run_id TEXT NOT NULL,

    -- Eligibility criteria
    schema_validity_rate DECIMAL(6,5) DEFAULT 1.0000,
    avg_response_time_ms DECIMAL(8,2) DEFAULT 0.00,
    total_predictions INTEGER DEFAULT 0,
    successful_predictions INTEGER DEFAULT 0,

    -- SLO tracking
    latency_slo_ms INTEGER DEFAULT 6000, -- 6 second SLO per expert
    validity_slo_rate DECIMAL(4,3) DEFAULT 0.985, -- 98.5% validity SLO

    -- Eligibility status
    eligible BOOLEAN DEFAULT TRUE,
    last_eligibility_check TIMESTAMP DEFAULT NOW(),
    eligibility_notes TEXT,

    -- Performance history
    performance_history JSONB DEFAULT '[]'::jsonb,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_expert_run_eligibility UNIQUE (expert_id, run_id)
);

-- Create indexes for eligibility gates
CREATE INDEX IF NOT EXISTS idx_expert_eligibility_run_id ON expert_eligibility_gates(run_id);
CREATE INDEX IF NOT EXISTS idx_expert_eligibility_expert ON expert_eligibility_gates(expert_id);
CREATE INDEX IF NOT EXISTS idx_expert_eligibility_eligible ON expert_eligibility_gates(run_id, eligible);

-- Function to initialize expert eligibility gates
CREATE OR REPLACE FUNCTION initialize_expert_eligibility_gates(
    p_run_id TEXT DEFAULT 'run_2025_pilot4',
    p_expert_ids TEXT[] DEFAULT ARRAY['conservative_analyzer', 'risk_taking_gambler', 'contrarian_rebel', 'value_hunter']
)
RETURNS JSONB AS $$
DECLARE
    expert_id TEXT;
    gates_created INTEGER := 0;
BEGIN
    FOREACH expert_id IN ARRAY p_expert_ids
    LOOP
        INSERT INTO expert_eligibility_gates (
            expert_id,
            run_id,
            schema_validity_rate,
            avg_response_time_ms,
            latency_slo_ms,
            validity_slo_rate,
            eligible,
            eligibility_notes
        )
        VALUES (
            expert_id,
            p_run_id,
            1.0000, -- Start with perfect validity
            0.00,   -- No response time yet
            6000,   -- 6 second SLO
            0.985,  -- 98.5% validity SLO
            TRUE,   -- Start eligible
            'Initial eligibility - no predictions yet'
        )
        ON CONFLICT (expert_id, run_id) DO UPDATE SET
            updated_at = NOW(),
            eligibility_notes = 'Eligibility gates re-initialized';

        gates_created := gates_created + 1;
    END LOOP;

    RETURN jsonb_build_object(
        'run_id', p_run_id,
        'gates_created', gates_created,
        'expert_ids', p_expert_ids
    );
END;
$$ LANGUAGE plpgsql;
-- Function to update expert eligibility based on performance
CREATE OR REPLACE FUNCTION update_expert_eligibility(
    p_expert_id TEXT,
    p_run_id TEXT,
    p_response_time_ms DECIMAL,
    p_schema_valid BOOLEAN
)
RETURNS JSONB AS $$
DECLARE
    current_gate RECORD;
    new_validity_rate DECIMAL;
    new_avg_response_time DECIMAL;
    is_eligible BOOLEAN;
    eligibility_reason TEXT;
BEGIN
    -- Get current eligibility gate
    SELECT * INTO current_gate
    FROM expert_eligibility_gates
    WHERE expert_id = p_expert_id AND run_id = p_run_id;

    IF NOT FOUND THEN
        -- Initialize if not exists
        PERFORM initialize_expert_eligibility_gates(p_run_id, ARRAY[p_expert_id]);
        SELECT * INTO current_gate
        FROM expert_eligibility_gates
        WHERE expert_id = p_expert_id AND run_id = p_run_id;
    END IF;

    -- Update prediction counts
    UPDATE expert_eligibility_gates
    SET
        total_predictions = total_predictions + 1,
        successful_predictions = successful_predictions + CASE WHEN p_schema_valid THEN 1 ELSE 0 END
    WHERE expert_id = p_expert_id AND run_id = p_run_id;

    -- Calculate new validity rate
    new_validity_rate := (current_gate.successful_predictions + CASE WHEN p_schema_valid THEN 1 ELSE 0 END)::DECIMAL
                        / (current_gate.total_predictions + 1);

    -- Calculate new average response time (exponential moving average)
    new_avg_response_time := CASE
        WHEN current_gate.total_predictions = 0 THEN p_response_time_ms
        ELSE (current_gate.avg_response_time_ms * 0.9) + (p_response_time_ms * 0.1)
    END;

    -- Determine eligibility
    is_eligible := (new_validity_rate >= current_gate.validity_slo_rate)
                   AND (new_avg_response_time <= current_gate.latency_slo_ms);

    -- Generate eligibility reason
    eligibility_reason := CASE
        WHEN NOT is_eligible AND new_validity_rate < current_gate.validity_slo_rate THEN
            format('Schema validity %.1f%% below SLO %.1f%%', new_validity_rate * 100, current_gate.validity_slo_rate * 100)
        WHEN NOT is_eligible AND new_avg_response_time > current_gate.latency_slo_ms THEN
            format('Avg response time %.0fms above SLO %dms', new_avg_response_time, current_gate.latency_slo_ms)
        WHEN is_eligible THEN
            format('Meeting SLOs: %.1f%% validity, %.0fms avg response', new_validity_rate * 100, new_avg_response_time)
        ELSE
            'Multiple SLO violations'
    END;

    -- Update eligibility gate
    UPDATE expert_eligibility_gates
    SET
        schema_validity_rate = new_validity_rate,
        avg_response_time_ms = new_avg_response_time,
        eligible = is_eligible,
        last_eligibility_check = NOW(),
        eligibility_notes = eligibility_reason,
        performance_history = performance_history || jsonb_build_object(
            'timestamp', NOW(),
            'response_time_ms', p_response_time_ms,
            'schema_valid', p_schema_valid,
            'validity_rate', new_validity_rate,
            'eligible', is_eligible
        ),
        updated_at = NOW()
    WHERE expert_id = p_expert_id AND run_id = p_run_id;

    RETURN jsonb_build_object(
        'expert_id', p_expert_id,
        'run_id', p_run_id,
        'eligible', is_eligible,
        'validity_rate', new_validity_rate,
        'avg_response_time_ms', new_avg_response_time,
        'reason', eligibility_reason
    );
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 4. Initialize the pilot run
-- ========================================

-- Initialize pilot experts with comprehensive state
SELECT initialize_pilot_experts('run_2025_pilot4');

-- Initialize eligibility gates
SELECT initialize_expert_eligibility_gates('run_2025_pilot4');

-- ========================================
-- 5. Monitoring and reporting functions
-- ========================================

-- Function to get pilot run status
CREATE OR REPLACE FUNCTION get_pilot_run_status(p_run_id TEXT DEFAULT 'run_2025_pilot4')
RETURNS JSONB AS $$
DECLARE
    result JSONB := jsonb_build_object('run_id', p_run_id);
    expert_count INTEGER;
    category_count INTEGER;
    eligible_experts INTEGER;
    bankroll_summary JSONB;
    eligibility_summary JSONB;
BEGIN
    -- Count experts and categories
    SELECT COUNT(DISTINCT expert_id) INTO expert_count
    FROM expert_bankroll WHERE run_id = p_run_id;

    SELECT COUNT(*) INTO category_count
    FROM expert_category_calibration WHERE run_id = p_run_id;

    SELECT COUNT(*) INTO eligible_experts
    FROM expert_eligibility_gates WHERE run_id = p_run_id AND eligible = TRUE;

    -- Get bankroll summary
    SELECT jsonb_agg(
        jsonb_build_object(
            'expert_id', expert_id,
            'current_units', current_units,
            'roi_percentage', roi_percentage,
            'total_bets', total_bets,
            'active', active
        )
    ) INTO bankroll_summary
    FROM expert_bankroll WHERE run_id = p_run_id;

    -- Get eligibility summary
    SELECT jsonb_agg(
        jsonb_build_object(
            'expert_id', expert_id,
            'eligible', eligible,
            'validity_rate', schema_validity_rate,
            'avg_response_time_ms', avg_response_time_ms,
            'total_predictions', total_predictions
        )
    ) INTO eligibility_summary
    FROM expert_eligibility_gates WHERE run_id = p_run_id;

    result := jsonb_set(result, '{expert_count}', to_jsonb(expert_count));
    result := jsonb_set(result, '{category_count}', to_jsonb(category_count));
    result := jsonb_set(result, '{eligible_experts}', to_jsonb(eligible_experts));
    result := jsonb_set(result, '{bankroll_summary}', bankroll_summary);
    result := jsonb_set(result, '{eligibility_summary}', eligibility_summary);

    RETURN result;
END;
$$ LANGUAGE plpgsql;
-- ========================================
-- 6. Add comments and documentation
-- ========================================

COMMENT ON FUNCTION initialize_pilot_experts IS 'Initialize pilot run with 4 experts, 100 unit bankrolls, and all 83 category calibrations';
COMMENT ON FUNCTION initialize_expert_eligibility_gates IS 'Set up eligibility gates with 98.5% validity and 6s latency SLOs';
COMMENT ON FUNCTION update_expert_eligibility IS 'Update expert eligibility based on prediction performance';
COMMENT ON FUNCTION get_pilot_run_status IS 'Get comprehensive status of pilot run including bankrolls and eligibility';

COMMENT ON TABLE expert_eligibility_gates IS 'Tracks expert eligibility based on schema validity and response time SLOs';
COMMENT ON COLUMN expert_eligibility_gates.schema_validity_rate IS 'Current schema validation pass rate (target: ≥98.5%)';
COMMENT ON COLUMN expert_eligibility_gates.avg_response_time_ms IS 'Exponential moving average of response times';
COMMENT ON COLUMN expert_eligibility_gates.latency_slo_ms IS 'Service level objective for response time (default: 6000ms)';
COMMENT ON COLUMN expert_eligibility_gates.validity_slo_rate IS 'Service level objective for schema validity (default: 98.5%)';

-- Log completion
RAISE NOTICE 'Pilot expert state seeded successfully';
RAISE NOTICE 'Initialized % experts with comprehensive calibration', (
    SELECT jsonb_extract_path_text(initialize_pilot_experts('run_2025_pilot4'), 'experts_initialized')
);
RAISE NOTICE 'Set up eligibility gates with 98.5%% validity and 6s latency SLOs';
RAISE NOTICE 'All 83 prediction categories calibrated with personality-based priors';
