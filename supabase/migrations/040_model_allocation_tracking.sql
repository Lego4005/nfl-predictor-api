-- Model Allocation Tracking for Orchestrator Model Switching
-- Supports multi-armed bandit approach with performance metrics

-- Model allocations table
CREATE TABLE IF NOT EXISTS model_allocations (
    id BIGSERIAL PRIMARY KEY,
    expert_id TEXT NOT NULL,
    family TEXT NOT NULL, -- betting category family (markets, totals, props, etc.)
    model_provider TEXT NOT NULL, -- anthropic/claude-sonnet-4.5, etc.
    allocation_pct DECIMAL(5,4) NOT NULL CHECK (allocation_pct >= 0 AND allocation_pct <= 1),
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    last_switch TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(expert_id, family, model_provider)
);

-- Model performance log for tracking metrics
CREATE TABLE IF NOT EXISTS model_performance_log (
    id BIGSERIAL PRIMARY KEY,
    expert_id TEXT NOT NULL,
    family TEXT NOT NULL,
    model_provider TEXT NOT NULL,
    game_id TEXT NOT NULL,

    -- Performance metrics
    json_valid BOOLEAN NOT NULL,
    latency_ms INTEGER NOT NULL,
    brier_score DECIMAL(6,4), -- For binary/enum predictions
    mae_score DECIMAL(6,4),   -- For numeric predictions
    roi DECIMAL(8,4),         -- Return on investment
    coherence_delta DECIMAL(6,4), -- Projection coherence impact

    -- Metadata
    reasoning_mode TEXT, -- deliberate, one_shot, degraded
    tool_calls_count INTEGER DEFAULT 0,
    tokens_used INTEGER,
    recorded_at TIMESTAMPTZ DEFAULT NOW(),

    INDEX idx_model_perf_expert_family (expert_id, family),
    INDEX idx_model_perf_recorded_at (recorded_at),
    INDEX idx_model_perf_model (model_provider)
);

-- Model switching audit log
CREATE TABLE IF NOT EXISTS model_switching_log (
    id BIGSERIAL PRIMARY KEY,
    expert_id TEXT NOT NULL,
    family TEXT NOT NULL,

    -- Switch details
    old_primary_model TEXT,
    new_primary_model TEXT NOT NULL,
    switch_reason TEXT NOT NULL, -- performance, eligibility, manual

    -- Metrics that triggered switch
    old_score DECIMAL(6,4),
    new_score DECIMAL(6,4),
    performance_delta DECIMAL(6,4),

    -- Switch metadata
    games_evaluated INTEGER,
    dwell_time_hours DECIMAL(6,2),
    switched_at TIMESTAMPTZ DEFAULT NOW(),
    switched_by TEXT DEFAULT 'orchestrator'
);

-- Expert predictions table updates for model tracking
ALTER TABLE expert_predictions
ADD COLUMN IF NOT EXISTS model_used TEXT,
ADD COLUMN IF NOT EXISTS reasoning_mode TEXT,
ADD COLUMN IF NOT EXISTS latency_ms INTEGER,
ADD COLUMN IF NOT EXISTS tool_calls_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS tokens_used INTEGER;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_expert_predictions_model_used ON expert_predictions(model_used);
CREATE INDEX IF NOT EXISTS idx_expert_predictions_reasoning_mode ON expert_predictions(reasoning_mode);
CREATE INDEX IF NOT EXISTS idx_expert_predictions_latency ON expert_predictions(latency_ms);

-- View for current model allocations
CREATE OR REPLACE VIEW current_model_allocations AS
SELECT
    expert_id,
    family,
    model_provider,
    allocation_pct,
    is_primary,
    last_switch,
    updated_at,
    CASE
        WHEN last_switch IS NULL THEN 'initial'
        WHEN last_switch > NOW() - INTERVAL '24 hours' THEN 'recent'
        ELSE 'stable'
    END as switch_status
FROM model_allocations
ORDER BY expert_id, family, allocation_pct DESC;

-- View for model performance summary
CREATE OR REPLACE VIEW model_performance_summary AS
SELECT
    expert_id,
    family,
    model_provider,
    COUNT(*) as games_count,
    AVG(CASE WHEN json_valid THEN 1.0 ELSE 0.0 END) as validity_rate,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as latency_p95,
    AVG(brier_score) as avg_brier,
    AVG(mae_score) as avg_mae,
    AVG(roi) as avg_roi,
    AVG(ABS(coherence_delta)) as avg_coherence_delta,
    MIN(recorded_at) as first_game,
    MAX(recorded_at) as last_game
FROM model_performance_log
WHERE recorded_at > NOW() - INTERVAL '7 days' -- Last 7 days
GROUP BY expert_id, family, model_provider
HAVING COUNT(*) >= 3 -- Minimum sample size
ORDER BY expert_id, family, avg_roi DESC;

-- Function to calculate model score
CREATE OR REPLACE FUNCTION calculate_model_score(
    p_brier DECIMAL,
    p_mae DECIMAL,
    p_roi DECIMAL,
    p_coherence_delta DECIMAL,
    p_family_brier_norm DECIMAL DEFAULT 0.5,
    p_family_mae_norm DECIMAL DEFAULT 1.0,
    p_family_roi_norm DECIMAL DEFAULT 0.01,
    p_family_coherence_norm DECIMAL DEFAULT 0.01
) RETURNS DECIMAL AS $$
BEGIN
    -- Score = 0.35*(1-brier_norm) + 0.35*(1-mae_norm) + 0.20*roi_norm - 0.10*coherence_norm
    RETURN (
        0.35 * (1 - LEAST(COALESCE(p_brier, 0.5) / p_family_brier_norm, 2.0)) +
        0.35 * (1 - LEAST(COALESCE(p_mae, 1.0) / p_family_mae_norm, 2.0)) +
        0.20 * LEAST(COALESCE(p_roi, 0.0) / GREATEST(p_family_roi_norm, 0.01), 3.0) -
        0.10 * LEAST(ABS(COALESCE(p_coherence_delta, 0.0)) / GREATEST(p_family_coherence_norm, 0.01), 2.0)
    );
END;
$$ LANGUAGE plpgsql;

-- Function to check model eligibility
CREATE OR REPLACE FUNCTION is_model_eligible(
    p_validity_rate DECIMAL,
    p_latency_p95 INTEGER,
    p_games_count INTEGER
) RETURNS BOOLEAN AS $$
BEGIN
    RETURN (
        p_validity_rate >= 0.985 AND
        p_latency_p95 <= 6000 AND
        p_games_count >= 3
    );
END;
$$ LANGUAGE plpgsql;

-- Insert initial model allocations for 4 pilot experts
INSERT INTO model_allocations (expert_id, family, model_provider, allocation_pct, is_primary) VALUES
-- Conservative Analyzer - Claude Sonnet primary
('conservative_analyzer', 'markets', 'anthropic/claude-sonnet-4.5', 0.70, true),
('conservative_analyzer', 'markets', 'google/gemini-2.5-flash-preview-09-2025', 0.20, false),
('conservative_analyzer', 'markets', 'deepseek/deepseek-chat-v3.1:free', 0.10, false),

-- Momentum Rider - DeepSeek primary
('momentum_rider', 'markets', 'deepseek/deepseek-chat-v3.1:free', 0.70, true),
('momentum_rider', 'markets', 'google/gemini-2.5-flash-preview-09-2025', 0.30, false),

-- Contrarian Rebel - Grok primary
('contrarian_rebel', 'markets', 'x-ai/grok-4-fast:free', 0.70, true),
('contrarian_rebel', 'markets', 'deepseek/deepseek-chat-v3.1:free', 0.30, false),

-- Value Hunter - Claude Sonnet primary
('value_hunter', 'markets', 'anthropic/claude-sonnet-4.5', 0.70, true),
('value_hunter', 'markets', 'google/gemini-2.5-flash-preview-09-2025', 0.30, false)

ON CONFLICT (expert_id, family, model_provider) DO NOTHING;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON model_allocations TO authenticated;
GRANT SELECT, INSERT ON model_performance_log TO authenticated;
GRANT SELECT, INSERT ON model_switching_log TO authenticated;
GRANT SELECT ON current_model_allocations TO authenticated;
GRANT SELECT ON model_performance_summary TO authenticated;

-- RLS policies
ALTER TABLE model_allocations ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_performance_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_switching_log ENABLE ROW LEVEL SECURITY;

-- Allow all operations for authenticated users (can be restricted further)
CREATE POLICY "Allow all for authenticated users" ON model_allocations FOR ALL TO authenticated USING (true);
CREATE POLICY "Allow all for authenticated users" ON model_performance_log FOR ALL TO authenticated USING (true);
CREATE POLICY "Allow all for authenticated users" ON model_switching_log FOR ALL TO authenticated USING (true);
