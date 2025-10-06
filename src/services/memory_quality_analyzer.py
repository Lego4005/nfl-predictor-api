"""
Memory Quality Analysis Service

This service tracks memory usage pas, analyzes memory relevance vs prediction accuracy,
and provides insights into memory quality and effectiveness for the expert training loop.
"""

import asyncio
import logging
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter

from supabase import Client as SupabaseClient


@dataclass
class MemoryUsageStats:
    """Statistics about memory usage patterns"""
    memory_id: str
    expert_id: str
    total_retrievals: int
    unique_contexts: int
    avg_similarity_score: float
    avg_relevance_score: float
    last_retrieved: datetime
    first_retrieved: datetime
    retrieval_frequency: float  # retrievals per day
    context_diversity: float  # how diverse the retrieval contexts are


@dataclass
class MemoryQualityMetrics:
    """Quality metrics for a memory"""
    memory_id: str
    expert_id: str
    quality_score: float  # Overall quality score (0-1)
    relevance_accuracy: float  # How often retrieved memories were actually relevant
    prediction_impact: float  # Impact on prediction accuracy when used
    retrieval_efficiency: float  # How efficiently this memory is retrieved
    content_richness: float  # Richness of the memory content
    temporal_stability: float  # How stable the memory's relevance is over time


@dataclass
class ExpertMemoryProfile:
    """Memory usage profile for an expert"""
    expert_id: str
    total_memories: int
    active_memories: int  # Memories retrieved in last 30 days
    avg_memory_quality: float
    memory_diversity: float
    retrieval_patterns: Dict[str, Any]
    top_performing_memories: List[str]
    underperforming_memories: List[str]
    recommendations: List[str]


@dataclass
class MemoryAnalysisReport:
    """Comprehensive memory analysis report"""
    analysis_date: datetime
    total_memories_analyzed: int
    expert_profiles: List[ExpertMemoryProfile]
    system_wide_metrics: Dict[str, Any]
    quality_trends: Dict[str, List[float]]
    recommendations: List[str]


class MemoryQualityAnalyzer:
    """
    Service for analyzing memory quality, usage patterns, and effectiveness
    in the expert training loop system.
    """

    def __init__(self, supabase_client: SupabaseClient):
        self.supabase = supabase_client
        self.logger = logging.getLogger(__name__)

        # Quality scoring weights
        self.quality_weights = {
            'retrieval_frequency': 0.25,
            'relevance_accuracy': 0.30,
            'prediction_impact': 0.25,
            'content_richness': 0.10,
            'temporal_stability': 0.10
        }

        self.logger.info("MemoryQualityAnalyzer initialized")

    async def analyze_memory_usage_patterns(
        self,
        expert_id: Optional[str] = None,
        days_back: int = 30
    ) -> List[MemoryUsageStats]:
        """
        Analyze memory usage patterns for experts.

        Args:
            expert_id: Specific expert to analyze (None for all experts)
            days_back: Number of days to look back for analysis

        Returns:
            List[MemoryUsageStats]: Usage statistics for memories
        """
        try:
            # Get memory retrieval data
            cutoff_date = datetime.now() - timedelta(days=days_back)

            query = """
            SELECT
                em.memory_id,
                em.expert_id,
                COUNT(mrl.id) as total_retrievals,
                COUNT(DISTINCT mrl.retrieval_context) as unique_contexts,
                AVG(CASE WHEN em.game_context_embedding IS NOT NULL THEN 0.8 ELSE 0.5 END) as avg_similarity_score,
                AVG(em.memory_vividness * em.memory_decay) as avg_relevance_score,
                MAX(mrl.retrieved_at) as last_retrieved,
                MIN(mrl.retrieved_at) as first_retrieved
            FROM expert_episodic_memories em
            LEFT JOIN memory_retrieval_log mrl ON em.memory_id = mrl.memory_id
            WHERE mrl.retrieved_at >= %s
            """

            params = [cutoff_date.isoformat()]

            if expert_id:
                query += " AND em.expert_id = %s"
                params.append(expert_id)

            query += """
            GROUP BY em.memory_id, em.expert_id
            HAVING COUNT(mrl.id) > 0
            ORDER BY total_retrievals DESC
            """

            # Execute raw SQL query
            response = self.supabase.rpc('execute_sql', {
                'query': query,
                'params': params
            }).execute()

            usage_stats = []

            for row in response.data or []:
                # Calculate retrieval frequency
                first_retrieved = datetime.fromisoformat(row['first_retrieved'].replace('Z', '+00:00'))
                last_retrieved = datetime.fromisoformat(row['last_retrieved'].replace('Z', '+00:00'))
                days_active = max(1, (last_retrieved - first_retrieved).days)
                retrieval_frequency = row['total_retrievals'] / days_active

                # Calculate context diversity (simplified)
                context_diversity = min(1.0, row['unique_contexts'] / max(1, row['total_retrievals']))

                stats = MemoryUsageStats(
                    memory_id=row['memory_id'],
                    expert_id=row['expert_id'],
                    total_retrievals=row['total_retrievals'],
                    unique_contexts=row['unique_contexts'],
                    avg_similarity_score=float(row['avg_similarity_score'] or 0),
                    avg_relevance_score=float(row['avg_relevance_score'] or 0),
                    last_retrieved=last_retrieved,
                    first_retrieved=first_retrieved,
                    retrieval_frequency=retrieval_frequency,
                    context_diversity=context_diversity
                )
                usage_stats.append(stats)

            self.logger.info(f"Analyzed usage patterns for {len(usage_stats)} memories")
            return usage_stats

        except Exception as e:
            self.logger.error(f"Error analyzing memory usage patterns: {str(e)}")
            return []

    async def calculate_memory_quality_scores(
        self,
        memory_ids: Optional[List[str]] = None,
        expert_id: Optional[str] = None
    ) -> List[MemoryQualityMetrics]:
        """
        Calculate quality scores for memories based on multiple factors.

        Args:
            memory_ids: Specific memory IDs to analyze (None for all)
            expert_id: Specific expert to analyze (None for all)

        Returns:
            List[MemoryQualityMetrics]: Quality metrics for memories
        """
        try:
            # Get memories to analyze
            query = self.supabase.table('expert_episodic_memories').select('*')

            if expert_id:
                query = query.eq('expert_id', expert_id)

            if memory_ids:
                query = query.in_('memory_id', memory_ids)

            response = query.execute()
            memories = response.data or []

            quality_metrics = []

            for memory in memories:
                memory_id = memory['memory_id']

                # Calculate individual quality components
                relevance_accuracy = await self._calculate_relevance_accuracy(memory_id)
                prediction_impact = await self._calculate_prediction_impact(memory_id)
                retrieval_efficiency = await self._calculate_retrieval_efficiency(memory_id)
                content_richness = self._calculate_content_richness(memory)
                temporal_stability = await self._calculate_temporal_stability(memory_id)

                # Calculate overall quality score
                quality_score = (
                    self.quality_weights['relevance_accuracy'] * relevance_accuracy +
                    self.quality_weights['prediction_impact'] * prediction_impact +
                    self.quality_weights['retrieval_efficiency'] * retrieval_efficiency +
                    self.quality_weights['content_richness'] * content_richness +
                    self.quality_weights['temporal_stability'] * temporal_stability
                )

                metrics = MemoryQualityMetrics(
                    memory_id=memory_id,
                    expert_id=memory['expert_id'],
                    quality_score=quality_score,
                    relevance_accuracy=relevance_accuracy,
                    prediction_impact=prediction_impact,
                    retrieval_efficiency=retrieval_efficiency,
                    content_richness=content_richness,
                    temporal_stability=temporal_stability
                )
                quality_metrics.append(metrics)

            self.logger.info(f"Calculated quality scores for {len(quality_metrics)} memories")
            return quality_metrics

        except Exception as e:
            self.logger.error(f"Error calculating memory quality scores: {str(e)}")
            return []

    async def _calculate_relevance_accuracy(self, memory_id: str) -> float:
        """Calculate how often this memory was actually relevant when retrieved"""
        try:
            # Get retrieval logs for this memory
            response = self.supabase.table('memory_retrieval_log').select('*').eq('memory_id', memory_id).execute()
            retrievals = response.data or []

            if not retrievals:
                return 0.5  # Default score for memories never retrieved

            # For now, use a simplified relevance calculation
            # In a full implementation, you'd track whether the retrieved memory
            # actually contributed to better predictions

            # Assume memories retrieved more frequently are more relevant
            retrieval_count = len(retrievals)

            if retrieval_count >= 10:
                return 0.9
            elif retrieval_count >= 5:
                return 0.7
            elif retrieval_count >= 2:
                return 0.6
            else:
                return 0.4

        except Exception as e:
            self.logger.error(f"Error calculating relevance accuracy for {memory_id}: {str(e)}")
            return 0.5

    async def _calculate_prediction_impact(self, memory_id: str) -> float:
        """Calculate the impact of this memory on prediction accuracy"""
        try:
            # This would require tracking which memories were used for which predictions
            # and comparing accuracy with/without those memories

            # For now, use memory characteristics as a proxy
            response = self.supabase.table('expert_episodic_memories').select('*').eq('memory_id', memory_id).execute()

            if not response.data:
                return 0.5

            memory = response.data[0]

            # Use emotional intensity and memory type as proxies for impact
            emotional_intensity = memory.get('emotional_intensity', 0.5)
            memory_type = memory.get('memory_type', '')

            base_impact = emotional_intensity

            # Boost impact for certain memory types
            if memory_type in ['prediction_outcome', 'learning_moment']:
                base_impact *= 1.2
            elif memory_type in ['failure_analysis', 'upset_detection']:
                base_impact *= 1.1

            return min(1.0, base_impact)

        except Exception as e:
            self.logger.error(f"Error calculating prediction impact for {memory_id}: {str(e)}")
            return 0.5

    async def _calculate_retrieval_efficiency(self, memory_id: str) -> float:
        """Calculate how efficiently this memory is retrieved"""
        try:
            # Get retrieval statistics
            response = self.supabase.table('memory_retrieval_log').select('*').eq('memory_id', memory_id).execute()
            retrievals = response.data or []

            if not retrievals:
                return 0.5

            # Calculate retrieval frequency vs memory age
            memory_response = self.supabase.table('expert_episodic_memories').select('created_at').eq('memory_id', memory_id).execute()

            if not memory_response.data:
                return 0.5

            created_at = datetime.fromisoformat(memory_response.data[0]['created_at'].replace('Z', '+00:00'))
            memory_age_days = (datetime.now() - created_at).days

            if memory_age_days == 0:
                return 0.8  # New memory

            retrieval_rate = len(retrievals) / memory_age_days

            # Normalize retrieval rate (assuming 0.1 retrievals/day is good)
            efficiency = min(1.0, retrieval_rate / 0.1)

            return efficiency

        except Exception as e:
            self.logger.error(f"Error calculating retrieval efficiency for {memory_id}: {str(e)}")
            return 0.5

    def _calculate_content_richness(self, memory: Dict[str, Any]) -> float:
        """Calculate the richness of memory content"""
        try:
            richness_score = 0.0

            # Check for prediction data
            prediction_data = memory.get('prediction_data', {})
            if prediction_data:
                richness_score += 0.3

                # Bonus for detailed predictions
                if len(str(prediction_data)) > 200:
                    richness_score += 0.1

            # Check for outcome data
            actual_outcome = memory.get('actual_outcome', {})
            if actual_outcome:
                richness_score += 0.3

            # Check for contextual factors
            contextual_factors = memory.get('contextual_factors', [])
            if contextual_factors:
                richness_score += 0.2

                # Bonus for multiple factors
                if len(contextual_factors) > 3:
                    richness_score += 0.1

            # Check for lessons learned
            lessons_learned = memory.get('lessons_learned', [])
            if lessons_learned:
                richness_score += 0.2

            return min(1.0, richness_score)

        except Exception as e:
            self.logger.error(f"Error calculating content richness: {str(e)}")
            return 0.5

    async def _calculate_temporal_stability(self, memory_id: str) -> float:
        """Calculate how stable the memory's relevance is over time"""
        try:
            # Get retrieval history over time
            response = self.supabase.table('memory_retrieval_log').select('retrieved_at').eq('memory_id', memory_id).order('retrieved_at').execute()
            retrievals = response.data or []

            if len(retrievals) < 3:
                return 0.6  # Default for memories with insufficient history

            # Calculate retrieval frequency over time windows
            retrieval_dates = [datetime.fromisoformat(r['retrieved_at'].replace('Z', '+00:00')) for r in retrievals]

            # Split into time windows and calculate frequency variance
            if len(retrieval_dates) < 6:
                return 0.7  # Not enough data for stability analysis

            # Calculate retrievals per week over the history
            start_date = retrieval_dates[0]
            end_date = retrieval_dates[-1]
            total_weeks = max(1, (end_date - start_date).days / 7)

            if total_weeks < 2:
                return 0.8  # Recent memory, assume stable

            # Simple stability calculation: lower variance = higher stability
            weekly_counts = []
            current_week_start = start_date

            while current_week_start < end_date:
                week_end = current_week_start + timedelta(days=7)
                week_retrievals = sum(1 for d in retrieval_dates if current_week_start <= d < week_end)
                weekly_counts.append(week_retrievals)
                current_week_start = week_end

            if len(weekly_counts) < 2:
                return 0.7

            # Calculate coefficient of variation (lower = more stable)
            mean_retrievals = statistics.mean(weekly_counts)
            if mean_retrievals == 0:
                return 0.3

            std_retrievals = statistics.stdev(weekly_counts) if len(weekly_counts) > 1 else 0
            cv = std_retrievals / mean_retrievals if mean_retrievals > 0 else 1

            # Convert CV to stability score (lower CV = higher stability)
            stability = max(0.0, 1.0 - cv)

            return stability

        except Exception as e:
            self.logger.error(f"Error calculating temporal stability for {memory_id}: {str(e)}")
            return 0.5

    async def generate_expert_memory_profile(self, expert_id: str) -> ExpertMemoryProfile:
        """Generate comprehensive memory profile for an expert"""
        try:
            # Get all memories for the expert
            response = self.supabase.table('expert_episodic_memories').select('*').eq('expert_id', expert_id).execute()
            memories = response.data or []

            total_memories = len(memories)

            if total_memories == 0:
                return ExpertMemoryProfile(
                    expert_id=expert_id,
                    total_memories=0,
                    active_memories=0,
                    avg_memory_quality=0.0,
                    memory_diversity=0.0,
                    retrieval_patterns={},
                    top_performing_memories=[],
                    underperforming_memories=[],
                    recommendations=["No memories found for this expert"]
                )

            # Calculate quality scores for all memories
            memory_ids = [m['memory_id'] for m in memories]
            quality_metrics = await self.calculate_memory_quality_scores(memory_ids=memory_ids)

            # Calculate active memories (retrieved in last 30 days)
            cutoff_date = datetime.now() - timedelta(days=30)
            active_memories = 0

            for memory in memories:
                # Check if memory was retrieved recently
                retrieval_response = self.supabase.table('memory_retrieval_log').select('retrieved_at').eq('memory_id', memory['memory_id']).gte('retrieved_at', cutoff_date.isoformat()).execute()

                if retrieval_response.data:
                    active_memories += 1

            # Calculate average quality
            avg_quality = statistics.mean([m.quality_score for m in quality_metrics]) if quality_metrics else 0.0

            # Calculate memory diversity (variety of memory types)
            memory_types = [m.get('memory_type', 'unknown') for m in memories]
            unique_types = len(set(memory_types))
            memory_diversity = min(1.0, unique_types / 6)  # Assuming 6 possible memory types

            # Analyze retrieval patterns
            retrieval_patterns = await self._analyze_retrieval_patterns(expert_id)

            # Identify top and underperforming memories
            quality_metrics.sort(key=lambda x: x.quality_score, reverse=True)
            top_performing = [m.memory_id for m in quality_metrics[:5]]
            underperforming = [m.memory_id for m in quality_metrics[-3:] if m.quality_score < 0.4]

            # Generate recommendations
            recommendations = self._generate_memory_recommendations(
                total_memories, active_memories, avg_quality, memory_diversity, retrieval_patterns
            )

            return ExpertMemoryProfile(
                expert_id=expert_id,
                total_memories=total_memories,
                active_memories=active_memories,
                avg_memory_quality=avg_quality,
                memory_diversity=memory_diversity,
                retrieval_patterns=retrieval_patterns,
                top_performing_memories=top_performing,
                underperforming_memories=underperforming,
                recommendations=recommendations
            )

        except Exception as e:
            self.logger.error(f"Error generating memory profile for expert {expert_id}: {str(e)}")
            return ExpertMemoryProfile(
                expert_id=expert_id,
                total_memories=0,
                active_memories=0,
                avg_memory_quality=0.0,
                memory_diversity=0.0,
                retrieval_patterns={},
                top_performing_memories=[],
                underperforming_memories=[],
                recommendations=[f"Error generating profile: {str(e)}"]
            )

    async def _analyze_retrieval_patterns(self, expert_id: str) -> Dict[str, Any]:
        """Analyze retrieval patterns for an expert"""
        try:
            # Get retrieval logs for expert's memories
            query = """
            SELECT mrl.*, em.memory_type
            FROM memory_retrieval_log mrl
            JOIN expert_episodic_memories em ON mrl.memory_id = em.memory_id
            WHERE em.expert_id = %s
            ORDER BY mrl.retrieved_at DESC
            LIMIT 1000
            """

            response = self.supabase.rpc('execute_sql', {
                'query': query,
                'params': [expert_id]
            }).execute()

            retrievals = response.data or []

            if not retrievals:
                return {}

            # Analyze patterns
            patterns = {
                'total_retrievals': len(retrievals),
                'retrievals_last_7_days': 0,
                'retrievals_last_30_days': 0,
                'most_retrieved_memory_types': {},
                'retrieval_contexts': {},
                'peak_retrieval_hours': {},
                'avg_retrievals_per_day': 0
            }

            now = datetime.now()
            seven_days_ago = now - timedelta(days=7)
            thirty_days_ago = now - timedelta(days=30)

            memory_type_counts = Counter()
            context_counts = Counter()
            hour_counts = Counter()

            for retrieval in retrievals:
                retrieved_at = datetime.fromisoformat(retrieval['retrieved_at'].replace('Z', '+00:00'))

                # Count recent retrievals
                if retrieved_at >= seven_days_ago:
                    patterns['retrievals_last_7_days'] += 1

                if retrieved_at >= thirty_days_ago:
                    patterns['retrievals_last_30_days'] += 1

                # Count by memory type
                memory_type = retrieval.get('memory_type', 'unknown')
                memory_type_counts[memory_type] += 1

                # Count by context
                context = retrieval.get('retrieval_context', 'unknown')
                context_counts[context] += 1

                # Count by hour
                hour_counts[retrieved_at.hour] += 1

            patterns['most_retrieved_memory_types'] = dict(memory_type_counts.most_common(5))
            patterns['retrieval_contexts'] = dict(context_counts.most_common(5))
            patterns['peak_retrieval_hours'] = dict(hour_counts.most_common(3))

            # Calculate average retrievals per day
            if retrievals:
                oldest_retrieval = datetime.fromisoformat(retrievals[-1]['retrieved_at'].replace('Z', '+00:00'))
                days_span = max(1, (now - oldest_retrieval).days)
                patterns['avg_retrievals_per_day'] = len(retrievals) / days_span

            return patterns

        except Exception as e:
            self.logger.error(f"Error analyzing retrieval patterns for expert {expert_id}: {str(e)}")
            return {}

    def _generate_memory_recommendations(
        self,
        total_memories: int,
        active_memories: int,
        avg_quality: float,
        memory_diversity: float,
        retrieval_patterns: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on memory analysis"""
        recommendations = []

        # Memory quantity recommendations
        if total_memories < 10:
            recommendations.append("Expert needs more memories - consider running more training games")
        elif total_memories > 1000:
            recommendations.append("Consider memory cleanup - expert has very large memory store")

        # Memory activity recommendations
        activity_rate = active_memories / total_memories if total_memories > 0 else 0

        if activity_rate < 0.1:
            recommendations.append("Low memory activity - many memories are not being retrieved")
        elif activity_rate > 0.8:
            recommendations.append("High memory activity - expert is effectively using stored memories")

        # Quality recommendations
        if avg_quality < 0.4:
            recommendations.append("Low average memory quality - consider memory cleanup or retraining")
        elif avg_quality > 0.8:
            recommendations.append("High quality memories - expert has excellent memory formation")

        # Diversity recommendations
        if memory_diversity < 0.3:
            recommendations.append("Low memory diversity - expert may need exposure to more varied game situations")
        elif memory_diversity > 0.8:
            recommendations.append("Good memory diversity - expert has experience with varied situations")

        # Retrieval pattern recommendations
        if retrieval_patterns:
            avg_daily_retrievals = retrieval_patterns.get('avg_retrievals_per_day', 0)

            if avg_daily_retrievals < 1:
                recommendations.append("Low retrieval frequency - expert may not be using memories effectively")
            elif avg_daily_retrievals > 20:
                recommendations.append("Very high retrieval frequency - consider optimizing memory search")

        return recommendations

    async def generate_comprehensive_analysis_report(
        self,
        expert_ids: Optional[List[str]] = None
    ) -> MemoryAnalysisReport:
        """Generate comprehensive memory analysis report"""
        try:
            analysis_date = datetime.now()

            # Get expert IDs if not provided
            if not expert_ids:
                response = self.supabase.table('expert_episodic_memories').select('expert_id').execute()
                expert_ids = list(set(row['expert_id'] for row in response.data or []))

            # Generate profiles for all experts
            expert_profiles = []
            for expert_id in expert_ids:
                profile = await self.generate_expert_memory_profile(expert_id)
                expert_profiles.append(profile)

            # Calculate system-wide metrics
            total_memories = sum(p.total_memories for p in expert_profiles)
            total_active = sum(p.active_memories for p in expert_profiles)
            avg_system_quality = statistics.mean([p.avg_memory_quality for p in expert_profiles if p.avg_memory_quality > 0]) if expert_profiles else 0

            system_metrics = {
                'total_memories': total_memories,
                'total_active_memories': total_active,
                'total_experts': len(expert_profiles),
                'avg_memories_per_expert': total_memories / len(expert_profiles) if expert_profiles else 0,
                'avg_system_quality': avg_system_quality,
                'memory_activity_rate': total_active / total_memories if total_memories > 0 else 0
            }

            # Generate quality trends (simplified - would need historical data)
            quality_trends = {
                'overall_quality': [avg_system_quality],
                'memory_count': [total_memories],
                'activity_rate': [system_metrics['memory_activity_rate']]
            }

            # Generate system-wide recommendations
            system_recommendations = []

            if avg_system_quality < 0.5:
                system_recommendations.append("System-wide memory quality is low - consider retraining or memory cleanup")

            if system_metrics['memory_activity_rate'] < 0.2:
                system_recommendations.append("Low system-wide memory activity - memories may not be effectively utilized")

            if system_metrics['avg_memories_per_expert'] < 20:
                system_recommendations.append("Experts have few memories - consider more training data")

            return MemoryAnalysisReport(
                analysis_date=analysis_date,
                total_memories_analyzed=total_memories,
                expert_profiles=expert_profiles,
                system_wide_metrics=system_metrics,
                quality_trends=quality_trends,
                recommendations=system_recommendations
            )

        except Exception as e:
            self.logger.error(f"Error generating comprehensive analysis report: {str(e)}")
            return MemoryAnalysisReport(
                analysis_date=datetime.now(),
                total_memories_analyzed=0,
                expert_profiles=[],
                system_wide_metrics={},
                quality_trends={},
                recommendations=[f"Error generating report: {str(e)}"]
            )

    async def cleanup_low_quality_memories(
        self,
        expert_id: Optional[str] = None,
        quality_threshold: float = 0.3,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Clean up low-quality memories that are not contributing to expert performance.

        Args:
            expert_id: Specific expert to clean up (None for all)
            quality_threshold: Minimum quality score to keep
            dry_run: If True, only report what would be deleted

        Returns:
            Dict with cleanup results
        """
        try:
            # Get quality metrics for memories
            quality_metrics = await self.calculate_memory_quality_scores(expert_id=expert_id)

            # Identify low-quality memories
            low_quality_memories = [
                m for m in quality_metrics
                if m.quality_score < quality_threshold
            ]

            cleanup_results = {
                'total_memories_analyzed': len(quality_metrics),
                'low_quality_memories_found': len(low_quality_memories),
                'quality_threshold_used': quality_threshold,
                'dry_run': dry_run,
                'memories_to_delete': [m.memory_id for m in low_quality_memories],
                'estimated_space_saved': len(low_quality_memories) * 0.1  # MB estimate
            }

            if not dry_run and low_quality_memories:
                # Actually delete the memories
                memory_ids_to_delete = [m.memory_id for m in low_quality_memories]

                # Delete from database
                self.supabase.table('expert_episodic_memories').delete().in_('memory_id', memory_ids_to_delete).execute()

                cleanup_results['memories_deleted'] = len(memory_ids_to_delete)
                self.logger.info(f"Deleted {len(memory_ids_to_delete)} low-quality memories")

            return cleanup_results

        except Exception as e:
            self.logger.error(f"Error cleaning up low-quality memories: {str(e)}")
            return {
                'error': str(e),
                'total_memories_analyzed': 0,
                'low_quality_memories_found': 0,
                'memories_deleted': 0
            }


# Global instance for easy access
_quality_analyzer = None

def get_quality_analyzer(supabase_client: SupabaseClient) -> MemoryQualityAnalyzer:
    """Get global quality analyzer instance"""
    global _quality_analyzer
    if _quality_analyzer is None:
        _quality_analyzer = MemoryQualityAnalyzer(supabase_client)
    return _quality_analyzer
