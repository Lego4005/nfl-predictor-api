
# Self-Healing System Schema

<cite>
**Referenced Files in This Document**   
- [023_self_healing_system_schema.sql](file://supabase/migrations/023_self_healing_system_schema.sql)
- [performance_decline_detector.py](file://src/ml/self_healing/performance_decline_detector.py)
- [adaptation_engine.py](file://src/ml/self_healing/adaptation_engine.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Performance Decline Detection](#performance-decline-detection)
3. [Adaptation Engine Configuration](#adaptation-engine-configuration)
4. [Adaptation Execution Tracking](#adaptation-execution-tracking)
5. [Recovery Protocol Management](#recovery-protocol-management)
6. [Cross-Expert Learning System](#cross-expert-learning-system)
7. [Bias Detection and Correction](#bias-detection-and-correction)
8. [Self-Healing System Views](#self-healing-system-views)
9. [System Integration and Workflow](#system-integration-and-workflow)
10. [Example Queries](#example-queries)
11. [Integration with CI Pipeline and Model Validation](#integration-with-ci-pipeline-and-model-validation)

## Introduction

The Self-Healing System Schema is designed to enable autonomous improvement of prediction accuracy in the NFL predictor system by detecting performance decline, implementing corrective actions, and learning from mistakes. This schema captures learning events, model adaptation records, feedback loops from prediction outcomes, and performance decline detection events. The system autonomously improves prediction accuracy over time by analyzing expert performance, detecting decline patterns, and triggering adaptation processes that adjust model parameters and methodologies.

The schema consists of several interconnected components that work together to create a self-improving system. These components include performance decline detection, adaptation engine configuration, adaptation execution tracking, recovery protocol management, cross-expert learning, and bias detection and correction. The system integrates with continuous integration pipelines and model validation processes to ensure that adaptations improve rather than degrade overall system performance.

**Section sources**
- [023_self_healing_system_schema.sql](file://supabase/migrations/023_self_healing_system_schema.sql#L1-L50)

## Performance Decline Detection

The `performance_decline_detection` table is the primary mechanism for identifying when expert models are underperforming. This table captures various types of performance decline including accuracy drops, rank drops, consistency issues, and confidence miscalibration. Each detection record includes detailed metrics comparing current performance to historical baselines, peer group averages, and percentile rankings.

The detection system uses multiple trigger types including threshold breaches, streak detection, trend analysis, and peer comparison to identify performance issues. For each detection, the system records the decline severity (minor, moderate, severe, or critical), duration in days, and specific metrics such as current and previous accuracy, rank changes, and confidence calibration errors.

The detection algorithm includes built-in safety mechanisms such as false positive probability estimation and escalation levels to ensure appropriate response to detected issues. Detected declines can trigger automatic actions or require manual review depending on the severity and context.

```mermaid
erDiagram
performance_decline_detection {
UUID id PK
VARCHAR(100) detection_id UK
VARCHAR(50) expert_id FK
TIMESTAMP detection_timestamp
VARCHAR(50) decline_type
VARCHAR(20) decline_severity
INTEGER decline_duration_days
VARCHAR(50) trigger_type
JSONB trigger_details
DECIMAL(6,5) trigger_threshold_breached
DECIMAL(6,5) current_accuracy
DECIMAL(6,5) previous_accuracy
DECIMAL(6,5) accuracy_drop
INTEGER current_rank
INTEGER previous_rank
INTEGER rank_drop
INTEGER recent_predictions
INTEGER recent_correct
DECIMAL(6,5) confidence_calibration_error
DECIMAL(6,5) peer_average_accuracy
DECIMAL(6,5) performance_gap
DECIMAL(5,2) percentile_rank
VARCHAR(50) detection_algorithm
DECIMAL(4,3) algorithm_sensitivity
DECIMAL(5,4) false_positive_probability
JSONB automatic_actions_triggered
BOOLEAN manual_review_required
INTEGER escalation_level
VARCHAR(20) detection_status
TIMESTAMP resolved_at
VARCHAR(100) resolution_method
TIMESTAMP created_at
TIMESTAMP updated_at
}
```

**Diagram sources**
- [023_self_healing_system_schema.sql](file://supabase/migrations/023_self_healing_system_schema.sql#L1-L75)

**Section sources**
- [023_self_healing_system_schema.sql](file://supabase/migrations/023_self_healing_system_schema.sql#L1-L75)
- [performance_decline_detector.py](file://src/ml/self_healing/performance_decline_detector.py#L1-L295)

## Adaptation Engine Configuration

The `adaptation_engine_config` table stores configuration parameters that govern how expert models adapt to performance changes. This configuration includes sensitivity, aggressiveness, and conservatism settings that determine how