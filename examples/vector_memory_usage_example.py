"""
Vector Memory System Uxample

This example demonstrates how to use the vector memory system for expert training:
1. Setting up the services
2. Creating memories with embeddings
3. Retrieving similar memories for predictions
4. Analyzing memory quality
"""

import asyncio
import os
from datetime import datetime
from supabase import create_client


async def vector_memory_example():
    """Example of using the vector memory system"""

    # Setup
    print("🚀 Vector Memory System Example")
    print("=" * 50)

    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL', 'http://localhost:54321')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    openai_api_key = os.getenv('OPENAI_API_KEY')

    if not supabase_key:
        print("❌ Please set SUPABASE_ANON_KEY environment variable")
        return

    supabase = create_client(supabase_url, supabase_key)

    # Import services
    from src.services.memory_embedding_generator import MemoryEmbeddingGenerator
    from src.services.vector_memory_retrieval_service import VectorMemoryRetrievalService
    from src.services.memory_quality_analyzer import MemoryQualityAnalyzer

    # Initialize services
    embedding_generator = MemoryEmbeddingGenerator(supabase, openai_api_key=openai_api_key)
    retrieval_service = VectorMemoryRetrievalService(supabase, embedding_generator)
    quality_analyzer = MemoryQualityAnalyzer(supabase)

    print("✅ Services initialized")

    # Example 1: Create a memory from a game experience
    print("\n📝 Example 1: Creating a memory from game experience")

    expert_id = "the_momentum_rider"
    memory_id = f"memory_{int(datetime.now().timestamp())}"

    # Game context - Chiefs vs Bills in cold weather
    game_context = {
        'home_team': 'BUF',
        'away_team': 'KC',
        'week': 14,
        'season': 2024,
        'weather': {
            'temperature': 22,
            'wind_speed': 18,
            'conditions': 'snow'
        },
        'team_stats': {
            'home': {
                'offensive_yards_per_game': 385,
                'defensive_yards_allowed': 310
            },
            'away': {
                'offensive_yards_per_game': 395,
                'defensive_yards_allowed': 325
            }
        },
        'line_movement': {
            'opening_line': -2.5,
            'current_line': -1.5,
            'public_percentage': 58
        },
        'is_divisional': False,
        'is_primetime': True
    }

    # Expert's prediction
    prediction_data = {
        'predicted_winner': 'BUF',
        'confidence': 0.68,
        'predicted_margin': 3,
        'spread_pick': 'BUF -1.5',
        'total_pick': 'UNDER 47.5',
        'key_factors': [
            'home_field_advantage_in_cold',
            'weather_favors_running_game',
            'buffalo_momentum_at_home'
        ]
    }

    # Actual game outcome
    outcome_data = {
        'winner': 'BUF',
        'home_score': 24,
        'away_score': 17,
        'margin': 7,
        'total_points': 41,
        'spread_result': 'cover',
        'total_result': 'under'
    }

    expert_reasoning = """
    The cold weather and snow conditions heavily favor Buffalo's running game and home field advantage.
    Kansas City's passing attack will be limited by the conditions, while Buffalo's ground game
    should control the tempo. The line movement toward Buffalo confirms sharp money backing the home team.
    """

    # Create memory record first
    memory_record = {
        'memory_id': memory_id,
        'expert_id': expert_id,
        'game_id': f"BUF_KC_2024_W14",
        'memory_type': 'prediction_outcome',
        'emotional_state': 'satisfaction',
        'prediction_data': prediction_data,
        'actual_outcome': outcome_data,
        'contextual_factors': ['cold_weather', 'primetime_game', 'playoff_implications'],
        'lessons_learned': ['weather_impact_on_passing', 'home_field_in_elements'],
        'emotional_intensity': 0.8,
        'memory_vividness': 0.9,
        'memory_decay': 1.0
    }

    supabase.table('expert_episodic_memories').insert(memory_record).execute()
    print(f"✅ Created memory record: {memory_id}")

    # Generate embeddings
    memory_embedding = await embedding_generator.generate_memory_embeddings(
        memory_id=memory_id,
        expert_id=expert_id,
        game_context=game_context,
        prediction_data=prediction_data,
        outcome_data=outcome_data,
        expert_reasoning=expert_reasoning
    )

    print(f"✅ Generated embeddings for memory")
    print(f"   - Embedding types created: {len([e for e in [memory_embedding.game_context_embedding, memory_embedding.prediction_embedding, memory_embedding.outcome_embedding, memory_embedding.combined_embedding] if e])}")

    # Example 2: Retrieve similar memories for a new prediction
    print("\n🔍 Example 2: Retrieving similar memories for new prediction")

    # New game context - Packers vs Bears in cold weather
    new_game_context = {
        'home_team': 'GB',
        'away_team': 'CHI',
        'week': 15,
        'season': 2024,
        'weather': {
            'temperature': 18,
            'wind_speed': 22,
            'conditions': 'snow'
        },
        'team_stats': {
            'home': {
                'offensive_yards_per_game': 365,
                'defensive_yards_allowed': 295
            },
            'away': {
                'offensive_yards_per_game': 310,
                'defensive_yards_allowed': 340
            }
        },
        'is_divisional': True,
        'is_primetime': False
    }

    # Retrieve relevant memories
    retrieval_result = await retrieval_service.retrieve_memories_for_prediction(
        expert_id=expert_id,
        game_context=new_game_context,
        max_memories=5,
        relevance_threshold=0.3,
        strategy='adaptive'
    )

    print(f"✅ Retrieved {len(retrieval_result.retrieved_memories)} relevant memories")
    print(f"   - Retrieval time: {retrieval_result.retrieval_time_ms}ms")
    print(f"   - Strategy used: {retrieval_result.retrieval_strategy}")

    for i, memory in enumerate(retrieval_result.retrieved_memories):
        print(f"   - Memory {i+1}: Similarity {memory.similarity_score:.3f}, Relevance {memory.relevance_score:.3f}")
        print(f"     Reason: {memory.retrieval_reason}")

    # Example 3: Analyze memory quality
    print("\n📊 Example 3: Analyzing memory quality")

    quality_metrics = await quality_analyzer.calculate_memory_quality_scores(
        memory_ids=[memory_id]
    )

    if quality_metrics:
        metrics = quality_metrics[0]
        print(f"✅ Quality analysis for memory {memory_id}:")
        print(f"   - Overall quality: {metrics.quality_score:.3f}")
        print(f"   - Relevance accuracy: {metrics.relevance_accuracy:.3f}")
        print(f"   - Prediction impact: {metrics.prediction_impact:.3f}")
        print(f"   - Retrieval efficiency: {metrics.retrieval_efficiency:.3f}")
        print(f"   - Content richness: {metrics.content_richness:.3f}")
        print(f"   - Temporal stability: {metrics.temporal_stability:.3f}")

    # Example 4: Generate expert profile
    print("\n👤 Example 4: Expert memory profile")

    expert_profile = await quality_analyzer.generate_expert_memory_profile(expert_id)

    print(f"✅ Profile for {expert_id}:")
    print(f"   - Total memories: {expert_profile.total_memories}")
    print(f"   - Active memories: {expert_profile.active_memories}")
    print(f"   - Average quality: {expert_profile.avg_memory_quality:.3f}")
    print(f"   - Memory diversity: {expert_profile.memory_diversity:.3f}")

    if expert_profile.recommendations:
        print("   - Recommendations:")
        for rec in expert_profile.recommendations[:3]:
            print(f"     • {rec}")

    # Example 5: Performance optimization
    print("\n⚡ Example 5: Performance optimization")

    test_contexts = [new_game_context]  # In practice, you'd have multiple contexts

    optimization_result = await retrieval_service.optimize_memory_retrieval_performance(
        expert_id=expert_id,
        test_contexts=test_contexts,
        target_retrieval_time_ms=50
    )

    print(f"✅ Performance optimization completed:")
    print(f"   - Target time: {optimization_result['target_time_ms']}ms")
    print(f"   - Configurations tested: {len(optimization_result['performance_tests'])}")

    if optimization_result['recommendations']:
        print("   - Recommendations:")
        for rec in optimization_result['recommendations']:
            print(f"     • {rec}")

    # Example 6: System-wide analysis
    print("\n🌐 Example 6: System-wide analysis")

    analysis_report = await quality_analyzer.generate_comprehensive_analysis_report([expert_id])

    print(f"✅ System analysis completed:")
    print(f"   - Total memories analyzed: {analysis_report.total_memories_analyzed}")
    print(f"   - Experts analyzed: {len(analysis_report.expert_profiles)}")
    print(f"   - System metrics:")

    for key, value in analysis_report.system_wide_metrics.items():
        if isinstance(value, float):
            print(f"     • {key}: {value:.3f}")
        else:
            print(f"     • {key}: {value}")

    # Cleanup
    print("\n🧹 Cleaning up example data...")
    supabase.table('expert_episodic_memories').delete().eq('memory_id', memory_id).execute()
    print("✅ Cleanup completed")

    print("\n🎉 Vector Memory System example completed successfully!")


def main():
    """Run the example"""
    asyncio.run(vector_memory_example())


if __name__ == "__main__":
    main()
