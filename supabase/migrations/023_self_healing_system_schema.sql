-- Self-Healing and Adaptation System Database Schema
-- Schema for autonomous expert improvement and recovery mechanisms
-- Migration: 023_self_healing_system_schema.sql

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================
-- 1. Performance Decline Detection
-- ========================================
CREATE TABLE performance_decline_detection (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    detection_id VARCHAR(100) UNIQUE NOT NULL,
    expert_id VARCHAR(50) NOT NULL,
    detection_timestamp TIMESTAMP DEFAULT NOW(),
    
    -- Decline Type Classification
    decline_type VARCHAR(50) NOT NULL,         -- accuracy_drop, rank_drop, consistency_issue, confidence_miscalibration
    decline_severity VARCHAR(20) NOT NULL,     -- minor, moderate, severe, critical
    decline_duration_days INTEGER NOT NULL,    -- How long decline has persisted
    
    -- Detection Triggers
    trigger_type VARCHAR(50) NOT NULL,         -- threshold_breach, streak_detection, trend_analysis, peer_comparison
    trigger_details JSONB NOT NULL DEFAULT '{}',
    trigger_threshold_breached DECIMAL(6,5),
    
    -- Performance Metrics at Detection
    current_accuracy DECIMAL(6,5),
    previous_accuracy DECIMAL(6,5),
    accuracy_drop DECIMAL(6,5),
    current_rank INTEGER,
    previous_rank INTEGER,
    rank_drop INTEGER,
    
    -- Context Information
    recent_predictions INTEGER,               -- Predictions in decline window
    recent_correct INTEGER,                   -- Correct predictions in decline window
    confidence_calibration_error DECIMAL(6,5), -- Calibration error during decline
    
    -- Comparison to Peers
    peer_average_accuracy DECIMAL(6,5),      -- Peer group average during same period
    performance_gap DECIMAL(6,5),            -- Gap vs peer average
    percentile_rank DECIMAL(5,2),            -- Current percentile vs peers
    
    -- Detection Algorithm Information
    detection_algorithm VARCHAR(50) DEFAULT 'multi_threshold_v1',
    algorithm_sensitivity DECIMAL(4,3) DEFAULT 0.8,
    false_positive_probability DECIMAL(5,4),
    
    -- Auto-Triggered Actions
    automatic_actions_triggered JSONB DEFAULT '{}',
    manual_review_required BOOLEAN DEFAULT FALSE,
    escalation_level INTEGER DEFAULT 1,      -- 1=low, 2=medium, 3=high, 4=critical
    
    -- Status and Resolution
    detection_status VARCHAR(20) DEFAULT 'active', -- active, investigating, resolved, false_positive
    resolved_at TIMESTAMP,
    resolution_method VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for decline detection
CREATE INDEX idx_decline_detection_expert ON performance_decline_detection(expert_id);
CREATE INDEX idx_decline_detection_type ON performance_decline_detection(decline_type);
CREATE INDEX idx_decline_detection_severity ON performance_decline_detection(decline_severity);
CREATE INDEX idx_decline_detection_status ON performance_decline_detection(detection_status);
CREATE INDEX idx_decline_detection_timestamp ON performance_decline_detection(detection_timestamp DESC);

-- ========================================
-- 2. Adaptation Engine Configuration
-- ========================================
CREATE TABLE adaptation_engine_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    config_id VARCHAR(100) UNIQUE NOT NULL,
    expert_id VARCHAR(50) NOT NULL,
    config_version VARCHAR(20) NOT NULL,
    
    -- Adaptation Parameters
    adaptation_sensitivity DECIMAL(4,3) DEFAULT 0.7,    -- How quickly to adapt
    adaptation_aggressiveness DECIMAL(4,3) DEFAULT 0.5, -- How much to change
    adaptation_conservatism DECIMAL(4,3) DEFAULT 0.3,   -- Resistance to change
    
    -- Parameter Tuning Configuration
    tunable_parameters JSONB NOT NULL DEFAULT '{}',      -- Which parameters can be tuned
    parameter_bounds JSONB NOT NULL DEFAULT '{}',        -- Min/max values for parameters
    parameter_step_sizes JSONB DEFAULT '{}',             -- Step sizes for adjustments
    
    -- Algorithm Modification Settings
    algorithm_flexibility VARCHAR(20) DEFAULT 'moderate', -- conservative, moderate, aggressive
    methodology_change_threshold DECIMAL(4,3) DEFAULT 0.8, -- Threshold for methodology changes
    weight_adjustment_range DECIMAL(4,3) DEFAULT 0.2,    -- Max weight adjustment per adaptation
    
    -- Learning Configuration
    learning_rate DECIMAL(5,4) DEFAULT 0.05,             -- Base learning rate
    momentum_factor DECIMAL(4,3) DEFAULT 0.1,            -- Momentum in learning
    memory_decay_rate DECIMAL(5,4) DEFAULT 0.01,         -- Memory decay rate
    
    -- Safety Mechanisms
    max_adaptations_per_week INTEGER DEFAULT 2,          -- Adaptation frequency limit
    rollback_threshold DECIMAL(4,3) DEFAULT 0.9,         -- Threshold for rolling back changes
    performance_monitoring_window_days INTEGER DEFAULT 7, -- Monitoring window post-adaptation
    
    -- Cross-Expert Learning
    peer_learning_enabled BOOLEAN DEFAULT TRUE,
    peer_learning_weight DECIMAL(4,3) DEFAULT 0.2,
    knowledge_transfer_threshold DECIMAL(4,3) DEFAULT 0.7,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for adaptation config
CREATE INDEX idx_adaptation_config_expert ON adaptation_engine_config(expert_id);
CREATE INDEX idx_adaptation_config_version ON adaptation_engine_config(config_version);

-- ========================================
-- 3. Adaptation Execution Tracking
-- ========================================
CREATE TABLE adaptation_execution_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id VARCHAR(100) UNIQUE NOT NULL,
    expert_id VARCHAR(50) NOT NULL,
    decline_detection_id VARCHAR(100), -- Links to decline detection if triggered by detection
    execution_timestamp TIMESTAMP DEFAULT NOW(),
    
    -- Adaptation Type and Details
    adaptation_type VARCHAR(50) NOT NULL,    -- parameter_tuning, weight_adjustment, algorithm_update, methodology_change
    adaptation_category VARCHAR(50),         -- performance_improvement, bias_correction, specialization_enhancement
    adaptation_description TEXT NOT NULL,
    
    -- Pre-Adaptation State
    pre_adaptation_state JSONB NOT NULL DEFAULT '{}',
    pre_adaptation_performance JSONB NOT NULL DEFAULT '{}',
    baseline_metrics JSONB NOT NULL DEFAULT '{}',
    
    -- Adaptation Changes
    parameter_changes JSONB DEFAULT '{}',
    algorithm_changes JSONB DEFAULT '{}',
    weight_changes JSONB DEFAULT '{}',
    methodology_changes JSONB DEFAULT '{}',
    
    -- Adaptation Reasoning
    adaptation_reasoning TEXT NOT NULL,
    data_sources_used TEXT[] DEFAULT '{}',
    peer_insights_applied JSONB DEFAULT '{}',
    confidence_in_adaptation DECIMAL(5,4),
    
    -- Expected Outcomes
    expected_improvements JSONB DEFAULT '{}',
    success_criteria JSONB NOT NULL DEFAULT '{}',
    monitoring_metrics TEXT[] DEFAULT '{}',
    expected_timeline_days INTEGER DEFAULT 7,
    
    -- Risk Assessment
    adaptation_risk_level VARCHAR(20) DEFAULT 'medium', -- low, medium, high
    potential_side_effects JSONB DEFAULT '{}',
    rollback_plan JSONB DEFAULT '{}',
    safety_checks_performed JSONB DEFAULT '{}',
    
    -- Execution Status
    execution_status VARCHAR(20) DEFAULT 'planning',    -- planning, executing, monitoring, completed, failed, rolled_back
    execution_progress DECIMAL(4,3) DEFAULT 0,
    execution_notes TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for adaptation execution
CREATE INDEX idx_adaptation_execution_expert ON adaptation_execution_log(expert_id);
CREATE INDEX idx_adaptation_execution_type ON adaptation_execution_log(adaptation_type);
CREATE INDEX idx_adaptation_execution_status ON adaptation_execution_log(execution_status);
CREATE INDEX idx_adaptation_execution_timestamp ON adaptation_execution_log(execution_timestamp DESC);

-- ========================================
-- 4. Recovery Protocol Management
-- ========================================
CREATE TABLE recovery_protocols (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    protocol_id VARCHAR(100) UNIQUE NOT NULL,
    protocol_name VARCHAR(200) NOT NULL,
    protocol_version VARCHAR(20) NOT NULL,
    
    -- Protocol Classification
    protocol_type VARCHAR(50) NOT NULL,      -- performance_recovery, bias_correction, specialization_recovery
    severity_level VARCHAR(20) NOT NULL,     -- minor, moderate, severe, critical
    applicable_decline_types TEXT[] DEFAULT '{}',
    
    -- Protocol Steps
    recovery_steps JSONB NOT NULL DEFAULT '{}',
    step_dependencies JSONB DEFAULT '{}',
    parallel_steps JSONB DEFAULT '{}',
    
    -- Protocol Parameters
    protocol_duration_days INTEGER NOT NULL,
    success_criteria JSONB NOT NULL DEFAULT '{}',
    failure_criteria JSONB DEFAULT '{}',
    intermediate_checkpoints JSONB DEFAULT '{}',
    
    -- Resource Requirements
    computational_resources JSONB DEFAULT '{}',
    data_requirements JSONB DEFAULT '{}',
    expert_involvement_required BOOLEAN DEFAULT FALSE,
    
    -- Protocol Effectiveness
    historical_success_rate DECIMAL(5,4) DEFAULT 0.5,
    average_recovery_time_days DECIMAL(6,2),
    common_failure_modes JSONB DEFAULT '{}',
    
    -- Protocol Conditions
    prerequisite_conditions JSONB DEFAULT '{}',
    contraindications JSONB DEFAULT '{}',
    compatibility_requirements JSONB DEFAULT '{}',
    
    -- Protocol Status
    protocol_status VARCHAR(20) DEFAULT 'active', -- active, deprecated, experimental
    last_updated TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    approved_by VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for recovery protocols
CREATE INDEX idx_recovery_protocols_type ON recovery_protocols(protocol_type);
CREATE INDEX idx_recovery_protocols_severity ON recovery_protocols(severity_level);
CREATE INDEX idx_recovery_protocols_status ON recovery_protocols(protocol_status);

-- ========================================
-- 5. Recovery Execution Tracking
-- ========================================
CREATE TABLE recovery_execution_tracking (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    execution_id VARCHAR(100) UNIQUE NOT NULL,
    expert_id VARCHAR(50) NOT NULL,
    protocol_id VARCHAR(100) REFERENCES recovery_protocols(protocol_id),
    decline_detection_id VARCHAR(100),
    execution_start_timestamp TIMESTAMP DEFAULT NOW(),
    
    -- Recovery Execution State
    current_step INTEGER DEFAULT 1,
    total_steps INTEGER NOT NULL,
    execution_progress DECIMAL(5,4) DEFAULT 0,
    execution_status VARCHAR(20) DEFAULT 'initializing', -- initializing, in_progress, paused, completed, failed, aborted
    
    -- Step-by-Step Progress
    completed_steps JSONB DEFAULT '{}',
    current_step_details JSONB DEFAULT '{}',
    failed_steps JSONB DEFAULT '{}',
    skipped_steps JSONB DEFAULT '{}',
    
    -- Performance Monitoring During Recovery
    baseline_performance JSONB NOT NULL DEFAULT '{}',
    intermediate_performance JSONB DEFAULT '{}',
    current_performance JSONB DEFAULT '{}',
    performance_trend VARCHAR(20),            -- improving, stable, declining
    
    -- Recovery Effectiveness Tracking
    success_criteria_met JSONB DEFAULT '{}',
    improvement_metrics JSONB DEFAULT '{}',
    side_effects_observed JSONB DEFAULT '{}',
    unexpected_outcomes JSONB DEFAULT '{}',
    
    -- Resource Utilization
    computational_time_used INTEGER DEFAULT 0, -- seconds
    data_processed JSONB DEFAULT '{}',
    external_resources_used JSONB DEFAULT '{}',
    
    -- Human Intervention
    manual_interventions JSONB DEFAULT '{}',
    expert_consultations INTEGER DEFAULT 0,
    manual_overrides JSONB DEFAULT '{}',
    
    -- Recovery Results
    recovery_success BOOLEAN,
    final_performance_improvement DECIMAL(6,5),
    recovery_duration_actual_hours DECIMAL(8,2),
    recovery_completion_timestamp TIMESTAMP,
    
    -- Post-Recovery Analysis
    lessons_learned TEXT,
    protocol_effectiveness_rating INTEGER, -- 1-10 scale
    recommendations_for_improvement TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for recovery execution
CREATE INDEX idx_recovery_execution_expert ON recovery_execution_tracking(expert_id);
CREATE INDEX idx_recovery_execution_protocol ON recovery_execution_tracking(protocol_id);
CREATE INDEX idx_recovery_execution_status ON recovery_execution_tracking(execution_status);
CREATE INDEX idx_recovery_execution_timestamp ON recovery_execution_tracking(execution_start_timestamp DESC);

-- ========================================
-- 6. Cross-Expert Learning System
-- ========================================
CREATE TABLE cross_expert_learning (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    learning_session_id VARCHAR(100) UNIQUE NOT NULL,
    learning_timestamp TIMESTAMP DEFAULT NOW(),
    
    -- Learning Participants
    source_expert_id VARCHAR(50) NOT NULL,   -- Expert sharing knowledge
    target_expert_id VARCHAR(50) NOT NULL,   -- Expert receiving knowledge
    facilitator_algorithm VARCHAR(50) DEFAULT 'peer_learning_v1',
    
    -- Knowledge Transfer Type
    knowledge_type VARCHAR(50) NOT NULL,     -- parameter_insights, methodology_tips, specialization_knowledge, bias_corrections
    knowledge_category VARCHAR(50),          -- prediction_accuracy, confidence_calibration, category_specialization
    knowledge_specificity VARCHAR(20),       -- general, category_specific, situation_specific
    
    -- Knowledge Content
    knowledge_description TEXT NOT NULL,
    transferable_insights JSONB NOT NULL DEFAULT '{}',
    adaptation_suggestions JSONB DEFAULT '{}',
    contraindications JSONB DEFAULT '{}',
    
    -- Source Expert Context
    source_expert_performance JSONB NOT NULL DEFAULT '{}',
    source_expert_specializations TEXT[] DEFAULT '{}',
    source_expert_success_factors JSONB DEFAULT '{}',
    
    -- Target Expert Context
    target_expert_current_state JSONB NOT NULL DEFAULT '{}',
    target_expert_needs JSONB DEFAULT '{}',
    compatibility_assessment DECIMAL(5,4),
    
    -- Knowledge Transfer Process
    transfer_method VARCHAR(50) DEFAULT 'parameter_adaptation',
    transfer_confidence DECIMAL(5,4),
    expected_benefit DECIMAL(5,4),
    transfer_risk_assessment JSONB DEFAULT '{}',
    
    -- Transfer Results
    knowledge_applied BOOLEAN DEFAULT FALSE,
    application_timestamp TIMESTAMP,
    application_details JSONB DEFAULT '{}',
    pre_transfer_performance JSONB DEFAULT '{}',
    post_transfer_performance JSONB DEFAULT '{}',
    
    -- Transfer Effectiveness
    transfer_success BOOLEAN,
    performance_improvement DECIMAL(6,5),
    side_effects JSONB DEFAULT '{}',
    adaptation_duration_hours DECIMAL(6,2),
    
    -- Learning Feedback
    effectiveness_rating INTEGER,            -- 1-10 scale
    knowledge_retention DECIMAL(5,4),
    follow_up_required BOOLEAN DEFAULT FALSE,
    lessons_learned TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for cross-expert learning
CREATE INDEX idx_cross_expert_learning_source ON cross_expert_learning(source_expert_id);
CREATE INDEX idx_cross_expert_learning_target ON cross_expert_learning(target_expert_id);
CREATE INDEX idx_cross_expert_learning_type ON cross_expert_learning(knowledge_type);
CREATE INDEX idx_cross_expert_learning_timestamp ON cross_expert_learning(learning_timestamp DESC);

-- ========================================
-- 7. Bias Detection and Correction
-- ========================================
CREATE TABLE bias_detection_correction (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    detection_id VARCHAR(100) UNIQUE NOT NULL,
    expert_id VARCHAR(50) NOT NULL,
    detection_timestamp TIMESTAMP DEFAULT NOW(),
    
    -- Bias Classification
    bias_type VARCHAR(50) NOT NULL,          -- overconfidence, underconfidence, favorite_bias, recency_bias, confirmation_bias
    bias_severity VARCHAR(20) NOT NULL,      -- mild, moderate, severe
    bias_persistence VARCHAR(20),            -- temporary, recurring, systematic
    
    -- Bias Detection Method
    detection_method VARCHAR(50) NOT NULL,   -- statistical_analysis, pattern_recognition, peer_comparison
    detection_confidence DECIMAL(5,4),
    detection_algorithm VARCHAR(50),
    
    -- Bias Evidence
    statistical_evidence JSONB NOT NULL DEFAULT '{}',
    pattern_evidence JSONB DEFAULT '{}',
    historical_evidence JSONB DEFAULT '{}',
    peer_comparison_evidence JSONB DEFAULT '{}',
    
    -- Bias Impact Analysis
    performance_impact DECIMAL(6,5),         -- How much bias affects performance
    affected_categories TEXT[] DEFAULT '{}', -- Which prediction categories are affected
    affected_situations JSONB DEFAULT '{}',  -- Specific situations where bias appears
    
    -- Bias Characteristics
    bias_triggers JSONB DEFAULT '{}',        -- What triggers the bias
    bias_patterns JSONB DEFAULT '{}',        -- Observable patterns
    bias_frequency DECIMAL(5,4),             -- How often bias occurs
    
    -- Correction Strategy
    correction_approach VARCHAR(50),         -- parameter_adjustment, algorithm_modification, training_intervention
    correction_plan JSONB NOT NULL DEFAULT '{}',
    expected_correction_timeline_days INTEGER,
    
    -- Correction Implementation
    correction_applied BOOLEAN DEFAULT FALSE,
    correction_timestamp TIMESTAMP,
    correction_details JSONB DEFAULT '{}',
    correction_effectiveness DECIMAL(5,4),
    
    -- Monitoring and Follow-up
    monitoring_plan JSONB DEFAULT '{}',
    follow_up_schedule JSONB DEFAULT '{}',
    relapse_prevention JSONB DEFAULT '{}',
    
    -- Correction Results
    bias_reduced BOOLEAN,
    residual_bias_level DECIMAL(5,4),
    performance_improvement DECIMAL(6,5),
    correction_side_effects JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for bias detection
CREATE INDEX idx_bias_detection_expert ON bias_detection_correction(expert_id);
CREATE INDEX idx_bias_detection_type ON bias_detection_correction(bias_type);
CREATE INDEX idx_bias_detection_severity ON bias_detection_correction(bias_severity);
CREATE INDEX idx_bias_detection_timestamp ON bias_detection_correction(detection_timestamp DESC);

-- ========================================
-- 8. Self-Healing System Views
-- ========================================

-- Active Issues Dashboard
CREATE OR REPLACE VIEW active_self_healing_issues AS
SELECT 
    'decline_detection' as issue_type,
    pdd.expert_id,
    em.name as expert_name,
    pdd.decline_type as issue_subtype,
    pdd.decline_severity as severity,
    pdd.detection_timestamp as detected_at,
    pdd.detection_status as status,
    NULL as correction_applied
FROM performance_decline_detection pdd
JOIN enhanced_expert_models em ON pdd.expert_id = em.expert_id
WHERE pdd.detection_status = 'active'

UNION ALL

SELECT 
    'bias_detection' as issue_type,
    bdc.expert_id,
    em.name as expert_name,
    bdc.bias_type as issue_subtype,
    bdc.bias_severity as severity,
    bdc.detection_timestamp as detected_at,
    'active' as status,
    bdc.correction_applied
FROM bias_detection_correction bdc
JOIN enhanced_expert_models em ON bdc.expert_id = em.expert_id
WHERE bdc.correction_applied = FALSE OR bdc.residual_bias_level > 0.3

ORDER BY detected_at DESC;

-- Recovery Progress Dashboard
CREATE OR REPLACE VIEW recovery_progress_dashboard AS
SELECT 
    ret.expert_id,
    em.name as expert_name,
    ret.protocol_id,
    rp.protocol_name,
    ret.execution_status,
    ret.execution_progress,
    ret.current_step,
    ret.total_steps,
    ret.execution_start_timestamp,
    ret.recovery_completion_timestamp,
    ret.performance_trend,
    ret.recovery_success
FROM recovery_execution_tracking ret
JOIN enhanced_expert_models em ON ret.expert_id = em.expert_id
JOIN recovery_protocols rp ON ret.protocol_id = rp.protocol_id
WHERE ret.execution_status IN ('initializing', 'in_progress', 'paused')
ORDER BY ret.execution_start_timestamp DESC;

-- ========================================
-- 9. Self-Healing Functions
-- ========================================

-- Function to trigger adaptation for underperforming expert
CREATE OR REPLACE FUNCTION trigger_expert_adaptation(
    p_expert_id VARCHAR(50),
    p_decline_type VARCHAR(50),
    p_severity VARCHAR(20) DEFAULT 'moderate'
)
RETURNS TABLE(
    adaptation_triggered BOOLEAN,
    adaptation_id VARCHAR(100),
    expected_timeline_days INTEGER
) AS $$
DECLARE
    detection_id VARCHAR(100);
    execution_id VARCHAR(100);
    timeline INTEGER;
BEGIN
    -- Generate unique IDs
    detection_id := 'decline_' || p_expert_id || '_' || extract(epoch from now())::text;
    execution_id := 'adapt_' || p_expert_id || '_' || extract(epoch from now())::text;
    
    -- Insert decline detection record
    INSERT INTO performance_decline_detection (
        detection_id, expert_id, decline_type, decline_severity,
        trigger_type, trigger_details, detection_status
    ) VALUES (
        detection_id, p_expert_id, p_decline_type, p_severity,
        'manual_trigger', '{"triggered_by": "system_function"}'::jsonb, 'active'
    );
    
    -- Insert adaptation execution log
    INSERT INTO adaptation_execution_log (
        execution_id, expert_id, decline_detection_id, adaptation_type,
        adaptation_description, pre_adaptation_state, success_criteria,
        execution_status
    ) VALUES (
        execution_id, p_expert_id, detection_id, 'performance_improvement',
        'Automated adaptation triggered for ' || p_decline_type,
        '{}'::jsonb, '{"min_accuracy_improvement": 0.05}'::jsonb, 'planning'
    );
    
    -- Set timeline based on severity
    timeline := CASE p_severity
        WHEN 'minor' THEN 3
        WHEN 'moderate' THEN 7
        WHEN 'severe' THEN 14
        WHEN 'critical' THEN 21
        ELSE 7
    END;
    
    RETURN QUERY SELECT TRUE, execution_id, timeline;
END;
$$ LANGUAGE plpgsql;

-- Function to check system health
CREATE OR REPLACE FUNCTION check_self_healing_system_health()
RETURNS TABLE(
    metric_name TEXT,
    metric_value INTEGER,
    status TEXT,
    details TEXT
) AS $$
BEGIN
    -- Check active decline detections
    RETURN QUERY
    SELECT 
        'active_decline_detections'::TEXT,
        COUNT(*)::INTEGER,
        CASE WHEN COUNT(*) > 5 THEN 'warning'::TEXT 
             WHEN COUNT(*) > 10 THEN 'critical'::TEXT 
             ELSE 'healthy'::TEXT END,
        'Number of experts with active performance decline'::TEXT
    FROM performance_decline_detection 
    WHERE detection_status = 'active';
    
    -- Check active recoveries
    RETURN QUERY
    SELECT 
        'active_recoveries'::TEXT,
        COUNT(*)::INTEGER,
        CASE WHEN COUNT(*) > 3 THEN 'warning'::TEXT ELSE 'healthy'::TEXT END,
        'Number of experts in active recovery'::TEXT
    FROM recovery_execution_tracking 
    WHERE execution_status IN ('initializing', 'in_progress');
    
    -- Check recent adaptations
    RETURN QUERY
    SELECT 
        'recent_adaptations'::TEXT,
        COUNT(*)::INTEGER,
        CASE WHEN COUNT(*) = 0 THEN 'warning'::TEXT ELSE 'healthy'::TEXT END,
        'Adaptations in last 24 hours'::TEXT
    FROM adaptation_execution_log 
    WHERE execution_timestamp > NOW() - INTERVAL '24 hours';
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 10. Sample Recovery Protocols
-- ========================================

-- Insert standard recovery protocols
INSERT INTO recovery_protocols (
    protocol_id, protocol_name, protocol_version, protocol_type, severity_level,
    applicable_decline_types, recovery_steps, protocol_duration_days, success_criteria
) VALUES
('accuracy_recovery_v1', 'Standard Accuracy Recovery Protocol', 'v1.0', 'performance_recovery', 'moderate',
 ARRAY['accuracy_drop', 'consistency_issue'], 
 '{"steps": [{"step": 1, "action": "analyze_recent_predictions"}, {"step": 2, "action": "identify_error_patterns"}, {"step": 3, "action": "adjust_parameters"}, {"step": 4, "action": "monitor_improvement"}]}'::jsonb,
 7, '{"min_accuracy_improvement": 0.05, "consistency_improvement": 0.03}'::jsonb),

('bias_correction_v1', 'Bias Detection and Correction Protocol', 'v1.0', 'bias_correction', 'moderate',
 ARRAY['overconfidence', 'underconfidence', 'favorite_bias'],
 '{"steps": [{"step": 1, "action": "identify_bias_patterns"}, {"step": 2, "action": "calculate_correction_factors"}, {"step": 3, "action": "apply_corrections"}, {"step": 4, "action": "validate_correction"}]}'::jsonb,
 10, '{"bias_reduction": 0.7, "performance_maintenance": 0.95}'::jsonb),

('specialization_recovery_v1', 'Specialization Recovery Protocol', 'v1.0', 'specialization_recovery', 'severe',
 ARRAY['rank_drop', 'specialization_loss'],
 '{"steps": [{"step": 1, "action": "analyze_specialization_areas"}, {"step": 2, "action": "identify_lost_advantages"}, {"step": 3, "action": "retrain_specialized_models"}, {"step": 4, "action": "validate_recovery"}]}'::jsonb,
 14, '{"specialization_strength_recovery": 0.8, "rank_improvement": 5}'::jsonb);

-- ========================================
-- 11. Sample Data for Testing
-- ========================================

-- Insert sample decline detection
INSERT INTO performance_decline_detection (
    detection_id, expert_id, decline_type, decline_severity, trigger_type,
    trigger_details, current_accuracy, previous_accuracy, accuracy_drop,
    current_rank, previous_rank, rank_drop
) VALUES (
    'decline_test_1', 'conservative_analyzer', 'accuracy_drop', 'moderate', 'threshold_breach',
    '{"threshold": 0.05, "monitoring_window": 7}'::jsonb,
    0.52, 0.61, 0.09, 8, 3, 5
);

-- Insert sample adaptation config
INSERT INTO adaptation_engine_config (
    config_id, expert_id, config_version, tunable_parameters, parameter_bounds
) VALUES (
    'config_conservative_v1', 'conservative_analyzer', 'v1.0',
    '{"risk_tolerance": true, "confidence_threshold": true, "weight_adjustments": true}'::jsonb,
    '{"risk_tolerance": {"min": 0.1, "max": 0.5}, "confidence_threshold": {"min": 0.4, "max": 0.9}}'::jsonb
);

-- ========================================
-- 12. Monitoring and Alerting Functions
-- ========================================

-- Function to generate self-healing system report
CREATE OR REPLACE FUNCTION generate_self_healing_report()
RETURNS TABLE(
    report_section TEXT,
    metric_name TEXT,
    metric_value TEXT,
    status TEXT
) AS $$
BEGIN
    -- Active Issues Section
    RETURN QUERY
    SELECT 
        'Active Issues'::TEXT,
        'Performance Decline Detections'::TEXT,
        COUNT(*)::TEXT,
        CASE WHEN COUNT(*) > 5 THEN 'Critical'::TEXT 
             WHEN COUNT(*) > 2 THEN 'Warning'::TEXT 
             ELSE 'Good'::TEXT END
    FROM performance_decline_detection 
    WHERE detection_status = 'active';
    
    RETURN QUERY
    SELECT 
        'Active Issues'::TEXT,
        'Uncorrected Biases'::TEXT,
        COUNT(*)::TEXT,
        CASE WHEN COUNT(*) > 3 THEN 'Warning'::TEXT ELSE 'Good'::TEXT END
    FROM bias_detection_correction 
    WHERE correction_applied = FALSE;
    
    -- Recovery Progress Section
    RETURN QUERY
    SELECT 
        'Recovery Progress'::TEXT,
        'Active Recoveries'::TEXT,
        COUNT(*)::TEXT,
        'Info'::TEXT
    FROM recovery_execution_tracking 
    WHERE execution_status IN ('initializing', 'in_progress');
    
    -- Learning Activity Section
    RETURN QUERY
    SELECT 
        'Learning Activity'::TEXT,
        'Cross-Expert Learning Sessions (24h)'::TEXT,
        COUNT(*)::TEXT,
        CASE WHEN COUNT(*) > 0 THEN 'Active'::TEXT ELSE 'Inactive'::TEXT END
    FROM cross_expert_learning 
    WHERE learning_timestamp > NOW() - INTERVAL '24 hours';
    
    -- System Performance Section
    RETURN QUERY
    SELECT 
        'System Performance'::TEXT,
        'Successful Adaptations (7d)'::TEXT,
        COUNT(*)::TEXT,
        CASE WHEN COUNT(*) > 0 THEN 'Good'::TEXT ELSE 'No Activity'::TEXT END
    FROM adaptation_execution_log 
    WHERE execution_timestamp > NOW() - INTERVAL '7 days'
    AND execution_status = 'completed';
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 13. Cleanup and Maintenance
-- ========================================

-- Function to archive old adaptation logs
CREATE OR REPLACE FUNCTION archive_old_adaptation_logs(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    -- Archive adaptation logs older than specified days
    WITH archived AS (
        DELETE FROM adaptation_execution_log 
        WHERE execution_timestamp < NOW() - INTERVAL '1 day' * days_to_keep
        AND execution_status IN ('completed', 'failed', 'rolled_back')
        RETURNING *
    )
    SELECT COUNT(*) INTO archived_count FROM archived;
    
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;

-- Function to cleanup resolved decline detections
CREATE OR REPLACE FUNCTION cleanup_resolved_detections(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    cleaned_count INTEGER;
BEGIN
    WITH cleaned AS (
        DELETE FROM performance_decline_detection 
        WHERE detection_status = 'resolved'
        AND resolved_at < NOW() - INTERVAL '1 day' * days_to_keep
        RETURNING *
    )
    SELECT COUNT(*) INTO cleaned_count FROM cleaned;
    
    RETURN cleaned_count;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 14. Migration Completion
-- ========================================

-- Create migrations log table if it doesn't exist
CREATE TABLE IF NOT EXISTS migrations_log (
    migration_name VARCHAR(100) PRIMARY KEY,
    completed_at TIMESTAMP DEFAULT NOW()
);

-- Log migration completion
INSERT INTO migrations_log (migration_name, completed_at) 
VALUES ('023_self_healing_system_schema', NOW())
ON CONFLICT (migration_name) DO UPDATE SET completed_at = NOW();

SELECT 'Self-Healing System Schema migration completed successfully' as status;