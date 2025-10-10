-- Shadow Storage Contract for A/B Testing and Model Comparison
-- Migration: 053_shadow_storage_contract.sql

-- ========================================
-- 1. Shadow predictions table (separate from hot path)
-- ========================================

CREATE TABLE IF NOT EXISTS expert_prediction_assertions_shadow (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    shadow_run_id TEXT NOT NULL, -- Separate shadow run tracking
    expert_id TEXT NOT NULL,
    game_id TEXT NOT NULL,
    run_id TEXT NOT NULL, -- Links to main run for comparison

    -- Shadow model information
    shadow_model TEXT NOT NULL, -- e.g., 'deepseek/deepseek-chat', 'x-ai/grok-beta'
    primary_model TEXT NOT NULL, -- The model this is shadowing
    shadow_type TEXT DEFAULT 'model_comparison', -- model_comparison, parameter_test, prompt_variant

    -- Prediction bundle (same structure as main)
    overall_prediction JSONB NOT NULL,
    predictions JSONB NOT NULL, -- Array of 83 predictions

    -- Shadow-specific metadata
    shadow_confidence DECIMAL(6,5),
    shadow_processing_time_ms DECIMAL(8,2),
    shadow_schema_valid BOOLEAN DEFAULT FALSE,
    shadow_validation_errors JSONB DEFAULT '[]'::jsonb,

    -- Comparison metrics (filled after both predictions complete)
    prediction_similarity DECIMAL(6,5), -- Cosine similarity of prediction vectors
    confidence_correlation DECIMAL(6,5), -- Correlation of confidence scores
    disagreement_categories TEXT[] DEFAULT '{}', -- Categories where predictions differ significantly

    -- Performance tracking
    shadow_tokens_used INTEGER,
    shadow_api_calls INTEGER DEFAULT 1,
    shadow_memory_retrievals INTEGER DEFAULT 0,

    -- Isolation guarantees
    used_in_council BOOLEAN DEFAULT FALSE, -- MUST always be FALSE
    used_in_coherence BOOLEAN DEFAULT FALSE, -- MUST always be FALSE
    used_in_settlement BOOLEAN DEFAULT FALSE, -- MUST always be FALSE

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints to enforce isolation
    CONSTRAINT shadow_never_used_in_council CHECK (used_in_council = FALSE),
    CONSTRAINT shadow_never_used_in_coherence CHECK (used_in_coherence = FALSE),
    CONSTRAINT shadow_never_used_in_settlement CHECK (used_in_settlement = FALSE),
    CONSTRAINT valid_shadow_confidence CHECK (shadow_confidence >= 0 AND shadow_confidence <= 1)
);

-- Indexes for shadow predictions
CREATE INDEX IF NOT EXISTS idx_shadow_predictions_shadow_run ON expert_prediction_assertions_shadow(shadow_run_id);
CREATE INDEX IF NOT EXISTS idx_shadow_predictions_expert ON expert_prediction_assertions_shadow(expert_id);
CREATE INDEX IF NOT EXISTS idx_shadow_predictions_game ON expert_prediction_assertions_shadow(game_id);
CREATE INDEX IF NOT EXISTS idx_shadow_predictions_main_run ON expert_prediction_assertions_shadow(run_id);
CREATE INDEX IF NOT EXISTS idx_shadow_predictions_model ON expert_prediction_assertions_shadow(shadow_model);
CREATE INDEX IF NOT EXISTS idx_shadow_predictions_created ON expert_prediction_assertions_shadow(created_at DESC);

-- Composite index for shadow analysis
CREATE INDEX IF NOT EXISTS idx_shadow_predictions_comparison
ON expert_prediction_assertions_shadow(run_id, expert_id, shadow_model, created_at DESC);

-- ========================================
-- 2. Shadow run tracking and telemetry
-- ========================================

CREATE TABLE IF NOT EXISTS shadow_run_telemetry (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    shadow_run_id TEXT NOT NULL,
    main_run_id TEXT NOT NULL,

    -- Run configuration
    shadow_models JSONB NOT NULL, -- {expert_id: shadow_model} mapping
    shadow_percentage DECIMAL(4,3) DEFAULT 0.200, -- 20% shadow traffic

    -- Performance metrics
    total_shadow_predictions INTEGER DEFAULT 0,
    successful_shadow_predictions INTEGER DEFAULT 0,
    shadow_success_rate DECIMAL(6,5) DEFAULT 0,

    -- Timing metrics
    avg_shadow_response_time_ms DECIMAL(8,2) DEFAULT 0,
    max_shadow_response_time_ms DECIMAL(8,2) DEFAULT 0,
    min_shadow_response_time_ms DECIMAL(8,2) DEFAULT 999999,

    -- Quality metrics
    avg_prediction_similarity DECIMAL(6,5) DEFAULT 0,
    avg_confidence_correlation DECIMAL(6,5) DEFAULT 0,
    schema_compliance_rate DECIMAL(6,5) DEFAULT 0,

    -- Resource usage
    total_shadow_tokens INTEGER DEFAULT 0,
    total_shadow_api_calls INTEGER DEFAULT 0,
    estimated_shadow_cost DECIMAL(10,6) DEFAULT 0,

    -- Status
    shadow_run_active BOOLEAN DEFAULT TRUE,
    started_at TIMESTAMP DEFAULT NOW(),
    last_prediction_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT unique_shadow_run UNIQUE (shadow_run_id)
);

-- Indexes for shadow run telemetry
CREATE INDEX IF NOT EXISTS idx_shadow_telemetry_shadow_run ON shadow_run_telemetry(shadow_run_id);
CREATE INDEX IF NOT EXISTS idx_shadow_telemetry_main_run ON shadow_run_telemetry(main_run_id);
CREATE INDEX IF NOT EXISTS idx_shadow_telemetry_active ON shadow_run_telemetry(shadow_run_active) WHERE shadow_run_active = TRUE;

-- ========================================
-- 3. Shadow storage and retrieval functions
-- ========================================

-- Function to store shadow prediction
CREATE OR REPLACE FUNCTION store_shadow_prediction(
    p_shadow_run_id TEXT,
    p_expert_id TEXT,
    p_game_id TEXT,
    p_main_run_id TEXT,
    p_shadow_model TEXT,
    p_primary_model TEXT,
    p_prediction_bundle JSONB,
    p_processing_time_ms DECIMAL DEFAULT 0,
    p_tokens_used INTEGER DEFAULT 0
)
RETURNS JSONB AS $$
DECLARE
    shadow_id UUID;
    schema_valid BOOLEAN;
    validation_errors JSONB;
BEGIN
    -- Validate shadow prediction schema (same as main predictions)
    SELECT validate_shadow_prediction_schema(p_prediction_bundle)
    INTO schema_valid, validation_errors;

    -- Insert shadow prediction
    INSERT INTO expert_prediction_assertions_shadow (
        shadow_run_id,
        expert_id,
        game_id,
        run_id,
        shadow_model,
        primary_model,
        overall_prediction,
        predictions,
        shadow_confidence,
        shadow_processing_time_ms,
        shadow_schema_valid,
        shadow_validation_errors,
        shadow_tokens_used,
        shadow_api_calls
    )
    VALUES (
        p_shadow_run_id,
        p_expert_id,
        p_game_id,
        p_main_run_id,
        p_shadow_model,
        p_primary_model,
        p_prediction_bundle->'overall',
        p_prediction_bundle->'predictions',
        (p_prediction_bundle->'overall'->>'overall_confidence')::DECIMAL,
        p_processing_time_ms,
        schema_valid,
        validation_errors,
        p_tokens_used,
        1
    )
    RETURNING id INTO shadow_id;

    -- Update shadow run telemetry
    INSERT INTO shadow_run_telemetry (shadow_run_id, main_run_id, shadow_models)
    VALUES (
        p_shadow_run_id,
        p_main_run_id,
        jsonb_build_object(p_expert_id, p_shadow_model)
    )
    ON CONFLICT (shadow_run_id) DO UPDATE SET
        total_shadow_predictions = shadow_run_telemetry.total_shadow_predictions + 1,
        successful_shadow_predictions = shadow_run_telemetry.successful_shadow_predictions +
            CASE WHEN schema_valid THEN 1 ELSE 0 END,
        shadow_success_rate = (shadow_run_telemetry.successful_shadow_predictions +
            CASE WHEN schema_valid THEN 1 ELSE 0 END)::DECIMAL /
            (shadow_run_telemetry.total_shadow_predictions + 1),
        avg_shadow_response_time_ms = (shadow_run_telemetry.avg_shadow_response_time_ms *
            shadow_run_telemetry.total_shadow_predictions + p_processing_time_ms) /
            (shadow_run_telemetry.total_shadow_predictions + 1),
        max_shadow_response_time_ms = GREATEST(shadow_run_telemetry.max_shadow_response_time_ms, p_processing_time_ms),
        min_shadow_response_time_ms = LEAST(shadow_run_telemetry.min_shadow_response_time_ms, p_processing_time_ms),
        total_shadow_tokens = shadow_run_telemetry.total_shadow_tokens + p_tokens_used,
        total_shadow_api_calls = shadow_run_telemetry.total_shadow_api_calls + 1,
        last_prediction_at = NOW(),
        updated_at = NOW();

    RETURN jsonb_build_object(
        'shadow_id', shadow_id,
        'shadow_run_id', p_shadow_run_id,
        'schema_valid', schema_valid,
        'processing_time_ms', p_processing_time_ms,
        'tokens_used', p_tokens_used
    );
END;
$$ LANGUAGE plpgsql;
-- Function to validate shadow prediction schema
CREATE OR REPLACE FUNCTION validate_shadow_prediction_schema(prediction_bundle JSONB)
RETURNS TABLE(is_valid BOOLEAN, errors JSONB) AS $$
DECLARE
    validation_errors TEXT[] := '{}';
    predictions_array JSONB;
    prediction_count INTEGER;
BEGIN
    -- Check overall structure
    IF NOT (prediction_bundle ? 'overall') THEN
        validation_errors := array_append(validation_errors, 'Missing overall field');
    END IF;

    IF NOT (prediction_bundle ? 'predictions') THEN
        validation_errors := array_append(validation_errors, 'Missing predictions field');
        RETURN QUERY SELECT FALSE, to_jsonb(validation_errors);
        RETURN;
    END IF;

    -- Check predictions array
    predictions_array := prediction_bundle->'predictions';
    prediction_count := jsonb_array_length(predictions_array);

    IF prediction_count != 83 THEN
        validation_errors := array_append(validation_errors,
            format('Expected 83 predictions, got %s', prediction_count));
    END IF;

    -- Additional validation could be added here
    -- For now, basic structure validation is sufficient

    RETURN QUERY SELECT array_length(validation_errors, 1) = 0 OR validation_errors = '{}', to_jsonb(validation_errors);
END;
$$ LANGUAGE plpgsql;

-- Function to compare shadow vs primary predictions
CREATE OR REPLACE FUNCTION compare_shadow_predictions(
    p_main_prediction_id UUID,
    p_shadow_prediction_id UUID
)
RETURNS JSONB AS $$
DECLARE
    main_pred RECORD;
    shadow_pred RECORD;
    similarity_score DECIMAL;
    confidence_correlation DECIMAL;
    disagreement_categories TEXT[] := '{}';
    comparison_result JSONB;
BEGIN
    -- Get main prediction
    SELECT * INTO main_pred
    FROM expert_predictions_comprehensive
    WHERE id = p_main_prediction_id;

    -- Get shadow prediction
    SELECT * INTO shadow_pred
    FROM expert_prediction_assertions_shadow
    WHERE id = p_shadow_prediction_id;

    IF NOT FOUND THEN
        RETURN jsonb_build_object('error', 'Predictions not found for comparison');
    END IF;

    -- Calculate similarity metrics (simplified for now)
    similarity_score := calculate_prediction_similarity(
        main_pred.betting_markets->'predictions',
        shadow_pred.predictions
    );

    confidence_correlation := calculate_confidence_correlation(
        main_pred.betting_markets->'predictions',
        shadow_pred.predictions
    );

    -- Identify disagreement categories
    disagreement_categories := find_disagreement_categories(
        main_pred.betting_markets->'predictions',
        shadow_pred.predictions
    );

    -- Update shadow prediction with comparison metrics
    UPDATE expert_prediction_assertions_shadow
    SET
        prediction_similarity = similarity_score,
        confidence_correlation = confidence_correlation,
        disagreement_categories = disagreement_categories,
        updated_at = NOW()
    WHERE id = p_shadow_prediction_id;

    comparison_result := jsonb_build_object(
        'main_prediction_id', p_main_prediction_id,
        'shadow_prediction_id', p_shadow_prediction_id,
        'similarity_score', similarity_score,
        'confidence_correlation', confidence_correlation,
        'disagreement_categories', disagreement_categories,
        'comparison_timestamp', NOW()
    );

    RETURN comparison_result;
END;
$$ LANGUAGE plpgsql;

-- Placeholder functions for similarity calculations (to be enhanced)
CREATE OR REPLACE FUNCTION calculate_prediction_similarity(main_preds JSONB, shadow_preds JSONB)
RETURNS DECIMAL AS $$
BEGIN
    -- Simplified similarity calculation
    -- In production, this would use vector similarity or detailed comparison
    RETURN 0.75 + (random() * 0.25); -- Placeholder: 75-100% similarity
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION calculate_confidence_correlation(main_preds JSONB, shadow_preds JSONB)
RETURNS DECIMAL AS $$
BEGIN
    -- Simplified confidence correlation
    -- In production, this would calculate actual correlation coefficient
    RETURN 0.60 + (random() * 0.35); -- Placeholder: 60-95% correlation
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION find_disagreement_categories(main_preds JSONB, shadow_preds JSONB)
RETURNS TEXT[] AS $$
DECLARE
    disagreements TEXT[] := '{}';
BEGIN
    -- Simplified disagreement detection
    -- In production, this would compare actual prediction values

    -- Add some sample disagreement categories for testing
    IF random() > 0.7 THEN
        disagreements := array_append(disagreements, 'spread_full_game');
    END IF;

    IF random() > 0.8 THEN
        disagreements := array_append(disagreements, 'total_full_game');
    END IF;

    RETURN disagreements;
END;
$$ LANGUAGE plpgsql;
