# Adaptation Triggers

<cite>
**Referenced Files in This Document**   
- [continuous_learner.py](file://src/ml/continuous_learner.py)
- [learning_coordinator.py](file://src/ml/learning_coordinator.py)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Concept Drift Detection in ContinuousLearner](#concept-drift-detection-in-continuouslearner)
3. [Drift Score and Response Severity](#drift-score-and-response-severity)
4. [Threshold-Based Adaptation Triggers](#threshold-based-adaptation-triggers)
5. [Decision Logic for Adaptation Types](#decision-logic-for-adaptation-types)
6. [Configuration Options](#configuration-options)
7. [Common Issues and Mitigation Strategies](#common-issues-and-mitigation-strategies)
8. [Conclusion](#conclusion)

## Introduction
The self-healing system in the NFL prediction platform relies on adaptation triggers to detect performance degradation and initiate corrective actions. These triggers are based on concept drift detection, performance monitoring, and threshold-based decision logic. The system uses two primary components: the `ContinuousLearner` class for model-level drift detection and the `LearningCoordinator` class for expert-level performance tracking and adaptation coordination. This document explains how these components work together to maintain prediction accuracy in the face of changing NFL dynamics.

**Section sources**
- [continuous_learner.py](file://src/ml/continuous_learner.py#L1-L50)
- [learning_coordinator.py](file://src/ml/learning_coordinator.py#L1-L50)

## Concept Drift Detection in ContinuousLearner
The `ContinuousLearner` class implements concept drift detection through the `DriftDetector` component, which monitors prediction patterns for significant changes. The system uses a multi-faceted approach to detect drift by analyzing three key aspects: performance degradation, feature distribution changes, and prediction distribution shifts.

The `detect_drift` method in the `DriftDetector` class combines scores from these three detection methods into a single drift score. Performance-based drift detection compares accuracy between historical and recent prediction windows, with the system splitting the prediction buffer into reference and current windows to calculate accuracy differences. Feature distribution drift detection analyzes changes in feature variances and means across windows, identifying features with significant distribution changes (greater than 50% variance change). Prediction distribution drift examines shifts in the mean and standard deviation of predictions over time.

This comprehensive approach ensures that the system can detect different types of drift, including sudden changes (recent error average more than 1.5 times older average), gradual degradation (1.2 times increase), and seasonal patterns. The drift detection process requires a minimum window size of 100 observations to ensure statistical significance before triggering any adaptation responses.

**Section sources**
- [continuous_learner.py](file://src/ml/continuous_learner.py#L100-L281)

## Drift Score and Response Severity
The system uses a severity-based response mechanism triggered by the drift score, which ranges from 0.0 to 1.0. The drift score is calculated as the average of three component scores: performance drift, feature drift, and prediction drift. Each component is normalized and combined to produce the final drift score that determines the appropriate response.

When drift is detected, the system generates recommendations based on the severity level. For drift scores below the threshold (0.1), no action is needed. Scores between 0.1 and 0.2 trigger monitoring recommendations, while scores between 0.2 and 0.3 suggest updating weights through online learning. Severe drift (scores above 0.3) triggers more aggressive responses, including learning rate adjustments and retraining flags.

The `ContinuousLearner` class implements specific response actions based on drift severity. When the drift score exceeds 0.3, the system increases the learning rate by 50% to accelerate model adaptation. For drift scores above 0.5, the system triggers a retraining flag by creating a JSON file in the `data/retrain_flags/` directory, which contains detailed information about the drift event, including the drift score, type, and affected features. This hierarchical response system ensures that the adaptation intensity matches the severity of the detected concept drift.

**Section sources**
- [continuous_learner.py](file://src/ml/continuous_learner.py#L283-L644)

## Threshold-Based Adaptation Triggers
The adaptation system employs a threshold-based mechanism to trigger expert weight updates and belief revisions. The `LearningCoordinator` class contains two key threshold parameters: `weight_update_threshold` (0.1) and `revision_threshold` (0.3). These thresholds determine when different levels of adaptation are initiated based on expert performance metrics.

The `weight_update_threshold` triggers expert weight adjustments when the accuracy change exceeds 10% from the neutral baseline (0.5). Weight updates also occur every 10 predictions as a regular maintenance mechanism. The weight calculation combines multiple performance factors: accuracy (40% weight), confidence-weighted accuracy (30%), recent accuracy (20%), and trend (10%). Improving trends receive a 1.1 multiplier, stable trends 1.0, and declining trends 0.9.

The `revision_threshold` controls belief revision triggers, activating when an expert's recent accuracy (last 10 predictions) falls below 30% and shows a declining trend. This dual condition prevents unnecessary revisions due to temporary performance fluctuations. The belief revision process gathers evidence from the last five incorrect predictions and uses the `BeliefRevisionService` to update the expert's internal belief system, potentially changing how the expert weighs different factors in future predictions.

**Section sources**
- [learning_coordinator.py](file://src/ml/learning_coordinator.py#L99-L468)

## Decision Logic for Adaptation Types
The system employs a sophisticated decision logic to determine the appropriate type of adaptation based on the nature and severity of performance issues. The decision process follows a hierarchy from minor adjustments to major interventions, ensuring that the least disruptive solution is applied first.

For minor performance issues, the system adjusts expert weights through the `_update_expert_weights` method, which recalculates weights based on a weighted combination of accuracy metrics. This adjustment occurs when the accuracy change exceeds the `weight_update_threshold` of 0.1. The system also updates weights periodically every 10 predictions to ensure continuous optimization.

For more significant performance degradation, the system triggers belief revision through the `_trigger_belief_revision` method. This occurs when an expert's recent accuracy falls below the `revision_threshold` of 0.3 and shows a declining trend. Belief revision involves a more fundamental change to the expert's prediction methodology, potentially altering how the expert interprets game situations and weighs different factors.

The most severe cases, indicated by high drift scores (above 0.5), trigger full model retraining rather than incremental adjustments. This distinction ensures that the system can handle both gradual performance degradation and sudden concept shifts appropriately. The decision logic also considers the expert's history, avoiding over-adaptation by limiting the frequency of major changes.

**Section sources**
- [learning_coordinator.py](file://src/ml/learning_coordinator.py#L468-L749)
- [continuous_learner.py](file://src/ml/continuous_learner.py#L386-L416)

## Configuration Options
The adaptation system provides several configurable parameters that control sensitivity, thresholds, and cooldown periods. These configuration options allow fine-tuning of the self-healing behavior to balance responsiveness with stability.

Key configuration parameters include:
- `weight_update_threshold`: Set to 0.1, this controls when expert weights are updated based on accuracy changes
- `revision_threshold`: Set to 0.3, this determines the accuracy level that triggers belief revision
- `memory_update_frequency`: Set to 5, this controls how often episodic memory is updated
- `adaptation_cooldown_hours`: Set to 24, this prevents over-adaptation by limiting how frequently an expert can be adapted
- `max_concurrent_adaptations`: Set to 3, this limits system-wide adaptation load

The system also includes database-stored configuration through the `adaptation_engine_config` table, which allows per-expert tuning of parameters such as adaptation sensitivity, aggressiveness, and conservatism. This granular control enables different experts to have different adaptation profiles based on their stability and specialization.

Additional configuration options include learning rate settings, parameter bounds for tunable parameters, and step sizes for adjustments. These parameters are stored in JSON format, allowing flexible configuration of which parameters can be tuned and their allowable ranges. The system also supports algorithm flexibility settings that determine how aggressively an expert can change its methodology.

**Section sources**
- [learning_coordinator.py](file://src/ml/learning_coordinator.py#L99-L749)
- [continuous_learner.py](file://src/ml/continuous_learner.py#L52-L98)

## Common Issues and Mitigation Strategies
The adaptation system addresses several common issues in self-healing AI systems, particularly false positives in drift detection and over-adaptation. The system employs multiple strategies to ensure reliable and stable adaptation behavior.

To prevent false positives, the system requires multiple conditions to be met before triggering significant adaptations. For belief revision, both low recent accuracy (below 0.3) and a declining trend are required, preventing reactions to temporary performance dips. The drift detection system uses a combination of three different detection methods, reducing the likelihood of false alarms from any single metric.

The system mitigates over-adaptation through several mechanisms. The `adaptation_cooldown_hours` parameter (24 hours) ensures that an expert cannot be adapted too frequently, allowing time to evaluate the impact of previous changes. The `max_concurrent_adaptations` limit (3) prevents system-wide instability from too many simultaneous changes. Additionally, the system uses bounded weight adjustments, constraining new weights between 0.1 and 2.0 to prevent extreme values.

For retraining operations, the system uses a flag-based approach rather than immediate execution, allowing external processes to manage the retraining schedule. This decoupling prevents resource contention and allows for batch processing of retraining requests. The system also logs all adaptation events, providing an audit trail for analyzing adaptation effectiveness and tuning threshold parameters.

**Section sources**
- [learning_coordinator.py](file://src/ml/learning_coordinator.py#L186-L220)
- [continuous_learner.py](file://src/ml/continuous_learner.py#L158-L187)

## Conclusion
The adaptation triggers in the self-healing system provide a robust framework for maintaining prediction accuracy in the dynamic NFL environment. By combining concept drift detection, threshold-based decision making, and hierarchical response mechanisms, the system can effectively respond to changing conditions while avoiding over-reaction to noise. The integration between the `ContinuousLearner` for model-level adaptation and the `LearningCoordinator` for expert-level coordination creates a comprehensive self-healing ecosystem. Configuration options and safeguards against common issues ensure that the system remains stable and reliable over time, making it well-suited for production deployment in a high-stakes prediction environment.