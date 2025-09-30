
# Expert Performance Evaluation

<cite>
**Referenced Files in This Document**   
- [accuracy_tracker.py](file://src/ml/performance_tracking/accuracy_tracker.py)
- [trend_analyzer.py](file://src/ml/performance_tracking/trend_analyzer.py)
- [ranking_system.py](file://src/ml/expert_competition/ranking_system.py)
- [council_selector.py](file://src/ml/expert_competition/council_selector.py)
- [performance_evaluator.py](file://src/ml/expert_competition/performance_evaluator.py)
- [adaptation_engine.py](file://src/ml/self_healing/adaptation_engine.py)
- [performance_decline_detector.py](file://src/ml/self_healing/performance_decline_detector.py)
- [voting_consensus.py](file://src/ml/expert_competition/voting_consensus.py)
- [competition_framework.py](file://src/ml/expert_competition/competition_framework.py)
- [022_performance_analytics_schema.sql](file://supabase/migrations/022_performance_analytics_schema.sql)
- [README.md](file://src/ml/testing/README.md)
</cite>

## Table of Contents
1. [Introduction](#introduction)
2. [Performance Metrics and Scoring](#performance-metrics-and-scoring)
3. [Accuracy Tracking System](#accuracy-tracking-system)
4. [Trend Analysis and Performance Trajectories](#trend-analysis-and-performance-trajectories)
5. [Ranking and Weighting Algorithms](#ranking-and-weighting-algorithms)
6. [AI Council Selection Process](#ai-council-selection-process)
7. [Consensus Weighting and Voting](#consensus-weighting-and-voting)
8. [Self-Healing and Adaptation System](#self-healing-and-adaptation-system)
9. [Configuration and Thresholds](#configuration-and-thresholds)
10. [Troubleshooting Performance Issues](#troubleshooting-performance-issues)
11. [Integration with Expert Lifecycle](#integration-with-expert-lifecycle)

## Introduction
The expert performance tracking system measures and optimizes individual expert effectiveness through a comprehensive framework of accuracy metrics, performance scoring, and ranking algorithms. This system evaluates expert predictions against actual game outcomes to generate multi-dimensional performance assessments that inform the consensus process and self-healing mechanisms. The architecture integrates accuracy tracking, trend analysis, ranking algorithms, and adaptation engines to create a dynamic system where expert weights are continuously adjusted based on performance data. This documentation details the implementation of these components, their integration, and the configuration options available for tuning the performance evaluation system.

## Performance Metrics and Scoring
The performance evaluation system employs a multi-dimensional scoring framework that assesses experts across five key dimensions: overall accuracy, recent performance, consistency, confidence calibration, and specialization strength. Each dimension contributes to a comprehensive performance score that determines expert rankings and weights in the consensus process. The scoring system uses configurable weights to balance these dimensions, with default values of 35% for overall accuracy, 25% for recent performance, 20% for consistency, 10% for confidence calibration, and 10% for specialization strength. Performance levels are categorized as excellent (>75% weighted score), good (65-75%), acceptable (55-65%), or poor (<55%). The system calculates both category-specific accuracy and overall performance metrics, providing granular insights into expert capabilities across different prediction types such as winner prediction, against-the-spread, totals, and player props.

**Section sources**
- [README.md](file://src/ml/testing/README.md#L83-L131)
- [ranking_system.py](file://src