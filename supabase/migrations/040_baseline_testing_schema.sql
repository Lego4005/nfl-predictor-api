-- 2024 Baselines A/B Testing Schema
-- Supports baseline model comparisons and intelligent model switching

-- Model performance metrics tracking
CREATE TABLE IF NOT EXIS model_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id TEXT NOT NULL,
    model_type TEXT NOT NULL, -- 'expert', 'coin_flip', 'market_only', 'one_shot', 'deliberate'
    run_id TEXT DEFAULT 'run_2025_pilot4',

    -- Performance metrics
    brier_score DECIMAL(6,4) DEFAULT 0.0,
    mae_score DECIMAL(6,2) DEFAULT 0.0,
    roi DECIMAL(6,4) DEFAULT 0.0,
    accuracy DECIMAL(6,4) DEFAULT 0.0,
    json_validity DECIMAL(6,4) DEFAULT 1.0,
    latency_p95 DECIMAL(6,2) DEFAULT 0.0,
    prediction_count INTEGER DEFAULT 0,

    -- Derived metrics
    eligibility_score DECIMAL(6,4) DEFAULT 0.5,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    UNIQUE(expert_id, model_type, run_id)
);

-- Expert model assignments
CREATE TABLE IF NOT EXISTS expert_model_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id TEXT NOT NULL,
    model_type TEXT NOT NULL,
    run_id TEXT DEFAULT 'run_2025_pilot4',

    -- Assignment details
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    reason TEXT,
    status TEXT DEFAULT 'active', -- 'active', 'inactive'

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    UNIQUE(expert_id, run_id, status) -- Only one active assignment per expert per run
);

-- Model switching history
CREATE TABLE IF NOT EXISTS model_switching_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id TEXT NOT NULL,
    run_id TEXT DEFAULT 'run_2025_pilot4',

    -- Switch details
    old_model TEXT NOT NULL,
    new_model TEXT NOT NULL,
    reason TEXT NOT NULL,
    game_id TEXT, -- Game that triggered the switch (if applicable)

    -- Switch metadata
    confidence DECIMAL(4,3), -- Confidence in switch decision
    forced BOOLEAN DEFAULT FALSE, -- Manual override

    -- Timestamps
    timestamp TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    INDEX idx_switching_history_expert_time (expert_id, timestamp DESC),
    INDEX idx_switching_history_run (run_id)
);

-- Baseline prediction results (for comparison)
CREATE TABLE IF NOT EXISTS baseline_prediction_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id TEXT NOT NULL,
    expert_id TEXT NOT NULL, -- For context/comparison
    model_type TEXT NOT NULL, -- 'coin_flip', 'market_only', 'one_shot', 'deliberate'
    run_id TEXT DEFAULT 'run_2025_pilot4',

    -- Prediction data
    predictions JSONB NOT NULL, -- Full prediction bundle
    confidence DECIMAL(4,3),
    execution_time DECIMAL(6,3), -- Seconds

    -- Metadata
    metadata JSONB, -- Model-specific metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    UNIQUE(game_id, expert_id, model_type, run_id)
);

-- Baseline comparison results
CREATE TABLE IF NOT EXISTS baseline_comparison_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    comparison_id TEXT NOT NULL, -- Unique identifier for comparison run
    run_id TEXT DEFAULT 'run_2025_pilot4',

    -- Comparison scope
    game_ids TEXT[] NOT NULL,
    expert_ids TEXT[] NOT NULL,
    baseline_types TEXT[] NOT NULL,

    -- Results
    baseline_metrics JSONB NOT NULL, -- Metrics by baseline type
    expert_metrics JSONB, -- Expert comparison metrics
    summary JSONB NOT NULL, -- Comparison summary

    -- Execution details
    execution_time DECIMAL(8,3),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    INDEX idx_comparison_results_run (run_id),
    INDEX idx_comparison_results_time (created_at DESC)
);

-- Model eligibility tracking
CREATE TABLE IF NOT EXISTS model_eligibility_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id TEXT NOT NULL,
    model_type TEXT NOT NULL,
    run_id TEXT DEFAULT 'run_2025_pilot4',

    -- Eligibility check results
    eligible BOOLEAN NOT NULL,
    reason TEXT NOT NULL,
    eligibility_score DECIMAL(6,4),

    -- Gate results
    json_validity_pass BOOLEAN,
    latency_slo_pass BOOLEAN,
    min_predictions_pass BOOLEAN,

    -- Timestamp
    checked_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    INDEX idx_eligibility_log_expert_time (expert_id, checked_at DESC),
    INDEX idx_eligibility_log_run (run_id)
);

-- Performance degradation alerts
CREATE TABLE IF NOT EXISTS performance_degradation_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id TEXT NOT NULL,
    model_type TEXT NOT NULL,
    run_id TEXT DEFAULT 'run_2025_pilot4',

    -- Degradation details
    metric_type TEXT NOT NULL, -- 'brier_score', 'roi', 'consecutive_failures'
    degradation_amount DECIMAL(6,4),
    threshold_exceeded DECIMAL(6,4),

    -- Alert status
    status TEXT DEFAULT 'active', -- 'active', 'resolved', 'ignored'
    resolved_at TIMESTAMPTZ,
    resolution_action TEXT,

    -- Timestamps
    detected_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    INDEX idx_degradation_alerts_expert (expert_id, status),
    INDEX idx_degradation_alerts_run (run_id)
);

-- Bandit exploration tracking
CREATE TABLE IF NOT EXISTS bandit_exploration_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id TEXT NOT NULL,
    run_id TEXT DEFAULT 'run_2025_pilot4',

    -- Exploration details
    current_model TEXT NOT NULL,
    exploration_model TEXT,
    exploration_rate DECIMAL(4,3),
    exploration_decision BOOLEAN,

    -- Bandit state
    exploration_count INTEGER DEFAULT 0,
    exploitation_count INTEGER DEFAULT 0,

    -- Timestamp
    evaluated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    INDEX idx_bandit_log_expert_time (expert_id, evaluated_at DESC),
    INDEX idx_bandit_log_run (run_id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_model_performance_expert_model ON model_performance_metrics(expert_id, model_type);
CREATE INDEX IF NOT EXISTS idx_model_performance_run ON model_performance_metrics(run_id);
CREATE INDEX IF NOT EXISTS idx_model_performance_updated ON model_performance_metrics(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_expert_assignments_expert ON expert_model_assignments(expert_id, status);
CREATE INDEX IF NOT EXISTS idx_expert_assignments_run ON expert_model_assignments(run_id);

CREATE INDEX IF NOT EXISTS idx_baseline_results_game_model ON baseline_prediction_results(game_id, model_type);
CREATE INDEX IF NOT EXISTS idx_baseline_results_run ON baseline_prediction_results(run_id);

-- Create RLS policies
ALTER TABLE model_performance_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE expert_model_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_switching_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE baseline_prediction_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE baseline_comparison_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_eligibility_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_degradation_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE bandit_exploration_log ENABLE ROW LEVEL SECURITY;

-- Allow authenticated users to read/write their data
CREATE POLICY "Users can manage model performance metrics" ON model_performance_metrics
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Users can manage expert assignments" ON expert_model_assignments
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Users can manage switching history" ON model_switching_history
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Users can manage baseline results" ON baseline_prediction_results
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Users can manage comparison results" ON baseline_comparison_results
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Users can manage eligibility log" ON model_eligibility_log
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Users can manage degradation alerts" ON performance_degradation_alerts
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Users can manage bandit exploration log" ON bandit_exploration_log
    FOR ALL USING (auth.role() = 'authenticated');

-- Create functions for common operations

-- Function to get current model assignment
CREATE OR REPLACE FUNCTION get_current_model_assignment(p_expert_id TEXT, p_run_id TEXT DEFAULT 'run_2025_pilot4')
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    current_model TEXT;
BEGIN
    SELECT model_type INTO current_model
    FROM expert_model_assignments
    WHERE expert_id = p_expert_id
      AND run_id = p_run_id
      AND status = 'active'
    ORDER BY assigned_at DESC
    LIMIT 1;

    RETURN COALESCE(current_model, 'expert');
END;
$$;

-- Function to check eligibility gates
CREATE OR REPLACE FUNCTION check_model_eligibility(
    p_expert_id TEXT,
    p_model_type TEXT,
    p_run_id TEXT DEFAULT 'run_2025_pilot4'
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    performance_record RECORD;
    result JSONB;
BEGIN
    -- Get latest performance metrics
    SELECT * INTO performance_record
    FROM model_performance_metrics
    WHERE expert_id = p_expert_id
      AND model_type = p_model_type
      AND run_id = p_run_id
    ORDER BY updated_at DESC
    LIMIT 1;

    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'eligible', false,
            'reason', 'No performance data available'
        );
    END IF;

    -- Check eligibility gates
    IF performance_record.json_validity < 0.985 THEN
        result := jsonb_build_object(
            'eligible', false,
            'reason', 'JSON validity below 98.5%',
            'json_validity', performance_record.json_validity
        );
    ELSIF performance_record.latency_p95 > 6.0 THEN
        result := jsonb_build_object(
            'eligible', false,
            'reason', 'Latency p95 exceeds 6s SLO',
            'latency_p95', performance_record.latency_p95
        );
    ELSIF performance_record.prediction_count < 10 THEN
        result := jsonb_build_object(
            'eligible', false,
            'reason', 'Insufficient predictions for evaluation',
            'prediction_count', performance_record.prediction_count
        );
    ELSE
        result := jsonb_build_object(
            'eligible', true,
            'reason', 'All eligibility gates passed',
            'eligibility_score', performance_record.eligibility_score
        );
    END IF;

    -- Log the check
    INSERT INTO model_eligibility_log (
        expert_id, model_type, run_id, eligible, reason, eligibility_score,
        json_validity_pass, latency_slo_pass, min_predictions_pass
    ) VALUES (
        p_expert_id, p_model_type, p_run_id,
        (result->>'eligible')::BOOLEAN,
        result->>'reason',
        performance_record.eligibility_score,
        performance_record.json_validity >= 0.985,
        performance_record.latency_p95 <= 6.0,
        performance_record.prediction_count >= 10
    );

    RETURN result;
END;
$$;

-- Function to update model performance
CREATE OR REPLACE FUNCTION update_model_performance(
    p_expert_id TEXT,
    p_model_type TEXT,
    p_metrics JSONB,
    p_run_id TEXT DEFAULT 'run_2025_pilot4'
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
DECLARE
    eligibility_score DECIMAL(6,4);
BEGIN
    -- Calculate eligibility score
    eligibility_score := (
        0.35 * GREATEST(0, 1 - COALESCE((p_metrics->>'brier_score')::DECIMAL, 0.25) / 0.5) +
        0.35 * GREATEST(0, 1 - COALESCE((p_metrics->>'mae_score')::DECIMAL, 5.0) / 10.0) +
        0.20 * GREATEST(0, LEAST(1, (COALESCE((p_metrics->>'roi')::DECIMAL, 0.0) + 0.2) / 0.4)) +
        0.10 * COALESCE((p_metrics->>'json_validity')::DECIMAL, 1.0)
    );

    -- Upsert performance record
    INSERT INTO model_performance_metrics (
        expert_id, model_type, run_id,
        brier_score, mae_score, roi, accuracy,
        json_validity, latency_p95, prediction_count,
        eligibility_score, updated_at
    ) VALUES (
        p_expert_id, p_model_type, p_run_id,
        COALESCE((p_metrics->>'brier_score')::DECIMAL, 0.0),
        COALESCE((p_metrics->>'mae_score')::DECIMAL, 0.0),
        COALESCE((p_metrics->>'roi')::DECIMAL, 0.0),
        COALESCE((p_metrics->>'accuracy')::DECIMAL, 0.0),
        COALESCE((p_metrics->>'json_validity')::DECIMAL, 1.0),
        COALESCE((p_metrics->>'latency_p95')::DECIMAL, 0.0),
        COALESCE((p_metrics->>'prediction_count')::INTEGER, 0),
        eligibility_score,
        NOW()
    )
    ON CONFLICT (expert_id, model_type, run_id)
    DO UPDATE SET
        brier_score = EXCLUDED.brier_score,
        mae_score = EXCLUDED.mae_score,
        roi = EXCLUDED.roi,
        accuracy = EXCLUDED.accuracy,
        json_validity = EXCLUDED.json_validity,
        latency_p95 = EXCLUDED.latency_p95,
        prediction_count = EXCLUDED.prediction_count,
        eligibility_score = EXCLUDED.eligibility_score,
        updated_at = NOW();
END;
$$;

-- Grant permissions
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;
