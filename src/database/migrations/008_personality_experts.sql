-- Migration: Create Personality-Driven Expert System Tables
-- Purpose: Enable autonomous learning experts with historical memory and evolution tracking

-- 1. Expert Profiles Table (The 15 personality experts)
CREATE TABLE IF NOT EXISTS personality_experts (
    expert_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    personality_traits JSONB NOT NULL, -- {risk_taking: 0.8, optimism: 0.3, ...}
    decision_style TEXT NOT NULL,
    learning_rate FLOAT DEFAULT 0.1,
    current_weights JSONB DEFAULT '{}', -- Current algorithm weights
    performance_stats JSONB DEFAULT '{"wins": 0, "losses": 0, "accuracy": 0.5}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 2. Expert Memory Table (Historical decisions for learning)
CREATE TABLE IF NOT EXISTS expert_memory (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    expert_id TEXT REFERENCES personality_experts(expert_id) ON DELETE CASCADE,
    game_id TEXT NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    prediction JSONB NOT NULL, -- Full prediction with all 25 sub-predictions
    actual_result JSONB, -- Actual game outcome for learning
    performance_score FLOAT, -- How well this prediction did
    context_snapshot JSONB, -- Game context at prediction time
    timestamp TIMESTAMP DEFAULT NOW(),

    -- Indexes for fast lookups
    INDEX idx_expert_memory_expert (expert_id),
    INDEX idx_expert_memory_game (game_id),
    INDEX idx_expert_memory_timestamp (timestamp DESC)
);

-- 3. Expert Evolution Table (Track algorithm changes over time)
CREATE TABLE IF NOT EXISTS expert_evolution (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    expert_id TEXT REFERENCES personality_experts(expert_id) ON DELETE CASCADE,
    version INT NOT NULL,
    algorithm_type TEXT NOT NULL, -- 'weights', 'formula', 'threshold'
    previous_state JSONB NOT NULL,
    new_state JSONB NOT NULL,
    trigger_reason TEXT, -- What caused this evolution
    performance_before FLOAT,
    performance_after FLOAT,
    timestamp TIMESTAMP DEFAULT NOW(),

    -- Unique constraint on expert + version
    UNIQUE(expert_id, version)
);

-- 4. Expert Learning Queue (Patterns to learn from)
CREATE TABLE IF NOT EXISTS expert_learning_queue (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    expert_id TEXT REFERENCES personality_experts(expert_id) ON DELETE CASCADE,
    learning_type TEXT NOT NULL, -- 'game_result', 'peer_success', 'pattern_detected'
    data JSONB NOT NULL,
    priority INT DEFAULT 5,
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),

    -- Index for processing queue
    INDEX idx_learning_queue_unprocessed (expert_id, processed, priority DESC)
);

-- 5. Expert Tool Access Log (Track external data gathering)
CREATE TABLE IF NOT EXISTS expert_tool_access (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    expert_id TEXT REFERENCES personality_experts(expert_id) ON DELETE CASCADE,
    tool_type TEXT NOT NULL, -- 'news', 'weather', 'injury_report', 'betting_lines'
    query TEXT NOT NULL,
    response JSONB,
    used_in_prediction BOOLEAN DEFAULT FALSE,
    game_id TEXT,
    timestamp TIMESTAMP DEFAULT NOW(),

    -- Index for tool usage analysis
    INDEX idx_tool_access_expert (expert_id, tool_type)
);

-- 6. Expert Peer Learning (Cross-expert knowledge sharing)
CREATE TABLE IF NOT EXISTS expert_peer_learning (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    learner_expert_id TEXT REFERENCES personality_experts(expert_id) ON DELETE CASCADE,
    teacher_expert_id TEXT REFERENCES personality_experts(expert_id) ON DELETE CASCADE,
    learning_type TEXT NOT NULL, -- 'performance_observation', 'pattern_shared'
    knowledge JSONB NOT NULL, -- What was learned (not HOW)
    applied BOOLEAN DEFAULT FALSE,
    impact_score FLOAT,
    timestamp TIMESTAMP DEFAULT NOW(),

    -- Prevent self-learning
    CHECK (learner_expert_id != teacher_expert_id)
);

-- 7. Add pgvector for similarity search on decisions
CREATE EXTENSION IF NOT EXISTS vector;

-- Add vector embedding columns for similarity search
ALTER TABLE expert_memory
ADD COLUMN IF NOT EXISTS decision_embedding vector(768),
ADD COLUMN IF NOT EXISTS context_embedding vector(768);

-- Create indexes for vector similarity search
CREATE INDEX IF NOT EXISTS idx_expert_memory_decision_embedding
ON expert_memory USING ivfflat (decision_embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_expert_memory_context_embedding
ON expert_memory USING ivfflat (context_embedding vector_cosine_ops);

-- 8. Insert the 15 personality experts
INSERT INTO personality_experts (expert_id, name, personality_traits, decision_style, learning_rate) VALUES
('conservative_analyzer', 'The Analyst',
 '{"risk_taking": 0.2, "optimism": 0.4, "contrarian": 0.3, "analytical": 0.9, "emotional": 0.1, "momentum_following": 0.3, "value_seeking": 0.7, "system_trust": 0.8}',
 'methodical', 0.05),

('risk_taking_gambler', 'The Gambler',
 '{"risk_taking": 0.9, "optimism": 0.7, "contrarian": 0.4, "analytical": 0.3, "emotional": 0.6, "momentum_following": 0.5, "value_seeking": 0.4, "system_trust": 0.2}',
 'aggressive', 0.15),

('contrarian_rebel', 'The Rebel',
 '{"risk_taking": 0.6, "optimism": 0.3, "contrarian": 0.95, "analytical": 0.5, "emotional": 0.4, "momentum_following": 0.05, "value_seeking": 0.6, "system_trust": 0.1}',
 'contrarian', 0.12),

('value_hunter', 'The Hunter',
 '{"risk_taking": 0.5, "optimism": 0.5, "contrarian": 0.6, "analytical": 0.8, "emotional": 0.2, "momentum_following": 0.2, "value_seeking": 0.95, "system_trust": 0.4}',
 'value-focused', 0.08),

('momentum_rider', 'The Rider',
 '{"risk_taking": 0.4, "optimism": 0.6, "contrarian": 0.1, "analytical": 0.5, "emotional": 0.4, "momentum_following": 0.95, "value_seeking": 0.3, "system_trust": 0.6}',
 'trend-following', 0.10),

('fundamentalist_scholar', 'The Scholar',
 '{"risk_taking": 0.3, "optimism": 0.5, "contrarian": 0.4, "analytical": 0.95, "emotional": 0.05, "momentum_following": 0.4, "value_seeking": 0.8, "system_trust": 0.9}',
 'research-based', 0.06),

('chaos_theory_believer', 'The Chaos',
 '{"risk_taking": 0.7, "optimism": 0.5, "contrarian": 0.7, "analytical": 0.6, "emotional": 0.5, "momentum_following": 0.5, "value_seeking": 0.5, "system_trust": 0.3}',
 'complex-systems', 0.11),

('gut_instinct_expert', 'The Intuition',
 '{"risk_taking": 0.6, "optimism": 0.6, "contrarian": 0.5, "analytical": 0.2, "emotional": 0.9, "momentum_following": 0.6, "value_seeking": 0.4, "system_trust": 0.3}',
 'intuitive', 0.13),

('statistics_purist', 'The Quant',
 '{"risk_taking": 0.4, "optimism": 0.5, "contrarian": 0.3, "analytical": 1.0, "emotional": 0.0, "momentum_following": 0.5, "value_seeking": 0.7, "system_trust": 0.95}',
 'quantitative', 0.04),

('trend_reversal_specialist', 'The Reversal',
 '{"risk_taking": 0.7, "optimism": 0.4, "contrarian": 0.8, "analytical": 0.6, "emotional": 0.3, "momentum_following": 0.0, "value_seeking": 0.8, "system_trust": 0.4}',
 'reversal-seeking', 0.14),

('popular_narrative_fader', 'The Fader',
 '{"risk_taking": 0.5, "optimism": 0.3, "contrarian": 0.85, "analytical": 0.7, "emotional": 0.2, "momentum_following": 0.1, "value_seeking": 0.7, "system_trust": 0.2}',
 'narrative-fading', 0.09),

('sharp_money_follower', 'The Sharp',
 '{"risk_taking": 0.4, "optimism": 0.5, "contrarian": 0.4, "analytical": 0.8, "emotional": 0.1, "momentum_following": 0.7, "value_seeking": 0.6, "system_trust": 0.7}',
 'professional-tracking', 0.07),

('underdog_champion', 'The Underdog',
 '{"risk_taking": 0.8, "optimism": 0.7, "contrarian": 0.7, "analytical": 0.4, "emotional": 0.6, "momentum_following": 0.2, "value_seeking": 0.9, "system_trust": 0.2}',
 'underdog-focused', 0.16),

('consensus_follower', 'The Consensus',
 '{"risk_taking": 0.2, "optimism": 0.5, "contrarian": 0.0, "analytical": 0.6, "emotional": 0.3, "momentum_following": 0.8, "value_seeking": 0.3, "system_trust": 0.85}',
 'consensus-based', 0.05),

('market_inefficiency_exploiter', 'The Exploiter',
 '{"risk_taking": 0.6, "optimism": 0.5, "contrarian": 0.65, "analytical": 0.85, "emotional": 0.15, "momentum_following": 0.3, "value_seeking": 0.9, "system_trust": 0.25}',
 'edge-seeking', 0.11)
ON CONFLICT (expert_id) DO UPDATE
SET updated_at = NOW();

-- 9. Create functions for expert learning

-- Function to record expert prediction
CREATE OR REPLACE FUNCTION record_expert_prediction(
    p_expert_id TEXT,
    p_game_id TEXT,
    p_home_team TEXT,
    p_away_team TEXT,
    p_prediction JSONB,
    p_context JSONB
) RETURNS UUID AS $$
DECLARE
    v_memory_id UUID;
BEGIN
    INSERT INTO expert_memory (
        expert_id, game_id, home_team, away_team,
        prediction, context_snapshot
    ) VALUES (
        p_expert_id, p_game_id, p_home_team, p_away_team,
        p_prediction, p_context
    ) RETURNING id INTO v_memory_id;

    -- Update expert's last activity
    UPDATE personality_experts
    SET updated_at = NOW()
    WHERE expert_id = p_expert_id;

    RETURN v_memory_id;
END;
$$ LANGUAGE plpgsql;

-- Function to process learning from game results
CREATE OR REPLACE FUNCTION process_expert_learning(
    p_game_id TEXT,
    p_actual_result JSONB
) RETURNS VOID AS $$
DECLARE
    v_memory RECORD;
    v_performance_score FLOAT;
BEGIN
    -- For each expert's prediction on this game
    FOR v_memory IN
        SELECT * FROM expert_memory
        WHERE game_id = p_game_id
        AND actual_result IS NULL
    LOOP
        -- Calculate performance score based on actual vs predicted
        v_performance_score := calculate_prediction_score(
            v_memory.prediction,
            p_actual_result
        );

        -- Update memory with results
        UPDATE expert_memory
        SET actual_result = p_actual_result,
            performance_score = v_performance_score
        WHERE id = v_memory.id;

        -- Add to learning queue
        INSERT INTO expert_learning_queue (
            expert_id, learning_type, data, priority
        ) VALUES (
            v_memory.expert_id,
            'game_result',
            jsonb_build_object(
                'memory_id', v_memory.id,
                'score', v_performance_score,
                'prediction', v_memory.prediction,
                'actual', p_actual_result
            ),
            CASE
                WHEN v_performance_score < 0.3 THEN 9  -- Learn from big mistakes
                WHEN v_performance_score > 0.8 THEN 7  -- Reinforce successes
                ELSE 5  -- Normal priority
            END
        );
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate prediction score
CREATE OR REPLACE FUNCTION calculate_prediction_score(
    p_prediction JSONB,
    p_actual JSONB
) RETURNS FLOAT AS $$
DECLARE
    v_score FLOAT := 0;
    v_components INT := 0;
BEGIN
    -- Score winner prediction (40% weight)
    IF p_prediction->>'winner_prediction' = p_actual->>'winner' THEN
        v_score := v_score + 0.4;
    END IF;

    -- Score spread prediction (30% weight)
    IF p_prediction->>'spread_prediction' IS NOT NULL
       AND p_actual->>'actual_spread' IS NOT NULL THEN
        v_score := v_score + 0.3 * (1 - LEAST(
            ABS((p_prediction->>'spread_prediction')::FLOAT -
                (p_actual->>'actual_spread')::FLOAT) / 14.0,
            1.0
        ));
    END IF;

    -- Score total prediction (30% weight)
    IF p_prediction->>'total_prediction' IS NOT NULL
       AND p_actual->>'actual_total' IS NOT NULL THEN
        v_score := v_score + 0.3 * (1 - LEAST(
            ABS((p_prediction->>'total_prediction')::FLOAT -
                (p_actual->>'actual_total')::FLOAT) / 20.0,
            1.0
        ));
    END IF;

    RETURN v_score;
END;
$$ LANGUAGE plpgsql;

-- Function for peer learning
CREATE OR REPLACE FUNCTION share_expert_success(
    p_teacher_id TEXT,
    p_game_id TEXT
) RETURNS VOID AS $$
DECLARE
    v_teacher_memory RECORD;
    v_expert RECORD;
BEGIN
    -- Get the successful prediction
    SELECT * INTO v_teacher_memory
    FROM expert_memory
    WHERE expert_id = p_teacher_id
    AND game_id = p_game_id
    AND performance_score > 0.7;

    IF v_teacher_memory IS NULL THEN
        RETURN;
    END IF;

    -- Share with other experts based on their learning style
    FOR v_expert IN
        SELECT * FROM personality_experts
        WHERE expert_id != p_teacher_id
    LOOP
        -- Check if this expert would learn from this pattern
        IF should_expert_learn_from_peer(v_expert, v_teacher_memory) THEN
            INSERT INTO expert_peer_learning (
                learner_expert_id, teacher_expert_id,
                learning_type, knowledge
            ) VALUES (
                v_expert.expert_id, p_teacher_id,
                'performance_observation',
                jsonb_build_object(
                    'game_context', v_teacher_memory.context_snapshot,
                    'successful_factors', extract_success_factors(v_teacher_memory),
                    'confidence_level', v_teacher_memory.prediction->>'winner_confidence'
                )
            );
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Helper function to determine if expert should learn from peer
CREATE OR REPLACE FUNCTION should_expert_learn_from_peer(
    p_learner RECORD,
    p_teacher_memory RECORD
) RETURNS BOOLEAN AS $$
BEGIN
    -- Consensus followers learn from high-agreement predictions
    IF (p_learner.personality_traits->>'system_trust')::FLOAT > 0.7 THEN
        RETURN TRUE;
    END IF;

    -- Contrarians might learn opposite lessons
    IF (p_learner.personality_traits->>'contrarian')::FLOAT > 0.8
       AND p_teacher_memory.performance_score < 0.3 THEN
        RETURN TRUE;  -- Learn what NOT to do
    END IF;

    -- Value seekers learn from high-value wins
    IF (p_learner.personality_traits->>'value_seeking')::FLOAT > 0.7
       AND (p_teacher_memory.prediction->>'spread_prediction')::FLOAT > 7 THEN
        RETURN TRUE;
    END IF;

    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Helper function to extract success factors
CREATE OR REPLACE FUNCTION extract_success_factors(p_memory RECORD)
RETURNS JSONB AS $$
BEGIN
    RETURN jsonb_build_object(
        'key_factors', p_memory.prediction->'key_factors',
        'confidence', p_memory.prediction->>'winner_confidence',
        'spread_accuracy',
            CASE WHEN p_memory.actual_result IS NOT NULL THEN
                ABS((p_memory.prediction->>'spread_prediction')::FLOAT -
                    (p_memory.actual_result->>'actual_spread')::FLOAT) < 3
            ELSE NULL END
    );
END;
$$ LANGUAGE plpgsql;

-- Create RLS policies
ALTER TABLE personality_experts ENABLE ROW LEVEL SECURITY;
ALTER TABLE expert_memory ENABLE ROW LEVEL SECURITY;
ALTER TABLE expert_evolution ENABLE ROW LEVEL SECURITY;
ALTER TABLE expert_learning_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE expert_tool_access ENABLE ROW LEVEL SECURITY;
ALTER TABLE expert_peer_learning ENABLE ROW LEVEL SECURITY;

-- Allow read access to all, write access through functions only
CREATE POLICY "Allow read access to expert data" ON personality_experts
    FOR SELECT USING (true);

CREATE POLICY "Allow read access to expert memory" ON expert_memory
    FOR SELECT USING (true);

CREATE POLICY "Allow read access to expert evolution" ON expert_evolution
    FOR SELECT USING (true);

-- Grant permissions
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO anon, authenticated;