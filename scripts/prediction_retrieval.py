#!/usr/bin/env python3
"""
Minimal prediction-time retrieval helper
Combines episodic memories, team knowledge, and matchup patterns
"""
import os
from typing import Dict, List, Optional, Any
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL") or os.environ.get("VITE_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY") or os.environ.get("VITE_SUPABASE_ANON_KEY")

def retrieve_for_prediction(supabase, expert_id: str, query_embedding: list, home: str, away: str) -> Dict[str, Any]:
    """
    Retrieve all relevant context for expert prediction

    Args:
        supabase: Supabase client
        expert_id: Expert identifier
        query_embedding: 1536-dim vector for semantic search
        home: Home team ID
        away: Away team ID

    Returns:
        Dict with episodic memories, team knowledge, and matchup data
    """

    # Episodic: semantic + recency
    episodic = supabase.rpc("search_expert_memories", {
        "p_expert_id": expert_id,
        "p_query_embedding": query_embedding,
        "p_match_threshold": 0.72,
        "p_match_count": 7,
        "p_alpha": 0.8
    }).execute().data

    # Team knowledge for both teams
    home_k = supabase.table("team_knowledge")\
        .select("*")\
        .eq("expert_id", expert_id)\
        .eq("team_id", home)\
        .order("confidence_level", desc=True)\
        .limit(10)\
        .execute().data

    away_k = supabase.table("team_knowledge")\
        .select("*")\
        .eq("expert_id", expert_id)\
        .eq("team_id", away)\
        .order("confidence_level", desc=True)\
        .limit(10)\
        .execute().data

    # Matchup memory (role-aware)
    try:
        matchup = supabase.table("matchup_memories")\
            .select("*")\
            .eq("expert_id", expert_id)\
            .eq("team_a_id", home)\
            .eq("team_b_id", away)\
            .single()\
            .execute()
        matchup_row = matchup.data if hasattr(matchup, "data") and matchup.data else None
    except:
        # Try reverse order
        try:
            matchup = supabase.table("matchup_memories")\
                .select("*")\
                .eq("expert_id", expert_id)\
                .eq("team_a_id", away)\
                .eq("team_b_id", home)\
                .single()\
                .execute()
            matchup_row = matchup.data if hasattr(matchup, "data") and matchup.data else None
        except:
            matchup_row = None

    return {
        "episodic": episodic,
        "home_knowledge": home_k,
        "away_knowledge": away_k,
        "matchup": matchup_row
    }

def format_retrieval_for_prompt(retrieval_data: Dict[str, Any]) -> str:
    """
    Format retrieval data for LLM prompt

    Args:
        retrieval_data: Output from retrieve_for_prediction

    Returns:
        Formatted string for prompt injection
    """

    sections = []

    # Episodic memories
    if retrieval_data["episodic"]:
        sections.append("## Recent Similar Situations")
        for i, mem in enumerate(retrieval_data["episodic"][:5], 1):
            sections.append(f"{i}. Game: {mem.get('home_team', 'Unknown')} vs {mem.get('away_team', 'Unknown')}")
            sections.append(f"   Similarity: {mem.get('similarity_score', 0):.2f}, Recency: {mem.get('recency_score', 0):.2f}")
            sections.append(f"   Memory ID: {mem.get('memory_id', 'Unknown')}")

    # Team knowledge
    if retrieval_data["home_knowledge"]:
        sections.append(f"\n## Home Team Knowledge")
        for knowledge in retrieval_data["home_knowledge"][:3]:
            sections.append(f"- {knowledge.get('knowledge_type', 'General')}: {knowledge.get('knowledge_summary', 'No summary')}")
            sections.append(f"  Confidence: {knowledge.get('confidence_level', 0):.2f}")

    if retrieval_data["away_knowledge"]:
        sections.append(f"\n## Away Team Knowledge")
        for knowledge in retrieval_data["away_knowledge"][:3]:
            sections.append(f"- {knowledge.get('knowledge_type', 'General')}: {knowledge.get('knowledge_summary', 'No summary')}")
            sections.append(f"  Confidence: {knowledge.get('confidence_level', 0):.2f}")

    # Matchup history
    if retrieval_data["matchup"]:
        sections.append(f"\n## Head-to-Head History")
        matchup = retrieval_data["matchup"]
        sections.append(f"Historical outcomes: {matchup.get('historical_outcomes', 'No data')}")
        sections.append(f"Pattern insights: {matchup.get('pattern_insights', 'No insights')}")

    return "\n".join(sections)

# Example usage
if __name__ == "__main__":
    sb = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Get a sample embedding for testing
    sample = sb.table("expert_episodic_memories")\
        .select("combined_embedding,expert_id")\
        .not_.is_("combined_embedding", None)\
        .limit(1)\
        .execute().data

    if sample:
        expert_id = sample[0]["expert_id"]
        query_embedding = sample[0]["combined_embedding"]

        # Test retrieval
        result = retrieve_for_prediction(sb, expert_id, query_embedding, "KC", "BUF")

        print("🔍 Retrieval Test Results:")
        print(f"Episodic memories: {len(result['episodic'])}")
        print(f"Home team knowledge: {len(result['home_knowledge'])}")
        print(f"Away team knowledge: {len(result['away_knowledge'])}")
        print(f"Matchup data: {'Yes' if result['matchup'] else 'No'}")

        # Format for prompt
        formatted = format_retrieval_for_prompt(result)
        print(f"\n📝 Formatted for prompt ({len(formatted)} chars):")
        print(formatted[:500] + "..." if len(formatted) > 500 else formatted)
    else:
        print("❌ No sample data found")
