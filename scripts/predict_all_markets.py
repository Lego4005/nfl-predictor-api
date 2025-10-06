#!/usr/bin/env python3
"""
Comprehensive Predictions for Tonight's Game: SF @ LA

Predict ALL betting markets:
- Winner (Moneyline)
- Spread
- Total (Over/Under)
- Player Props (passing yards, rushing yards, TDs)
- Game Props (first score, halftime leader, etc.)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

from supabase import create_client
from src.services.openrouter_service import OpenRouterService
from src.ml.supabase_memory_services import SupabaseEpisodicMemoryManager
from dotenv import load_dotenv

load_dotenv()


async def predict_all_markets():
    """Make comprehensive predictions for all betting markets"""

    logger.info("="*80)
    logger.info("🎯 COMPREHENSIVE PREDICTIONS: SF @ LA")
    logger.info("="*80)
    logger.info("Game Time: 8:15 PM ET")
    logger.info("Using 60 accumulated memories (30 SF + 30 LA)")
    logger.info("="*80)
    logger.info("")

    # Initialize
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    memory_service = SupabaseEpisodicMemoryManager(supabase)
    llm_service = OpenRouterService(os.getenv('VITE_OPENROUTER_API_KEY'))

    # Retrieve memories for BOTH teams
    sf_memories = await memory_service.retrieve_memories(
        'conservative_analyzer',
        {'home_team': 'SF', 'away_team': 'SF'},
        limit=30
    )

    la_memories = await memory_service.retrieve_memories(
        'conservative_analyzer',
        {'home_team': 'LA', 'away_team': 'LA'},
        limit=30
    )

    # Combine and prioritize
    all_memories = sf_memories + la_memories
    all_memories.sort(key=lambda x: (x.get('similarity_score', 0), x.get('created_at', '')), reverse=True)

    logger.info(f"📊 Retrieved {len(sf_memories)} SF memories, {len(la_memories)} LA memories")
    logger.info(f"   Total memory bank: {len(all_memories)} games\n")

    # Build comprehensive context from memories
    memory_summary = "HISTORICAL CONTEXT FROM YOUR MEMORIES:\n\n"

    # SF performance summary
    sf_wins = sum(1 for m in sf_memories if m.get('actual_outcome', {}).get('winner') == ('home' if m.get('contextual_factors', [{}])[0].get('value') == 'SF' and m.get('contextual_factors', [{}])[0].get('factor') == 'home_team' else 'away'))
    memory_summary += f"49ERS RECENT PERFORMANCE:\n"
    memory_summary += f"- Record in memories: {sf_wins}/{len(sf_memories)}\n"

    # LA performance summary
    la_wins = sum(1 for m in la_memories if m.get('actual_outcome', {}).get('winner') == ('home' if m.get('contextual_factors', [{}])[0].get('value') == 'LA' and m.get('contextual_factors', [{}])[0].get('factor') == 'home_team' else 'away'))
    memory_summary += f"\nRAMS RECENT PERFORMANCE:\n"
    memory_summary += f"- Record in memories: {la_wins}/{len(la_memories)}\n"

    # Head-to-head
    h2h_memories = [m for m in all_memories if
                    any(f.get('value') == 'SF' for f in m.get('contextual_factors', [])) and
                    any(f.get('value') == 'LA' for f in m.get('contextual_factors', []))]

    if h2h_memories:
        memory_summary += f"\nHEAD-TO-HEAD HISTORY:\n"
        memory_summary += f"- {len(h2h_memories)} recent matchups in memory\n"
        for i, mem in enumerate(h2h_memories[:3], 1):
            outcome = mem.get('actual_outcome', {})
            memory_summary += f"  {i}. Score: {outcome.get('away_score', '?')}-{outcome.get('home_score', '?')}\n"

    memory_summary += "\n"

    # === PREDICTION 1: GAME WINNER ===
    logger.info("="*80)
    logger.info("1️⃣  GAME WINNER (MONEYLINE)")
    logger.info("="*80)

    winner_prompt = f"""{memory_summary}

GAME: San Francisco 49ers @ Los Angeles Rams
VENUE: SoFi Stadium (LA home)
CONDITIONS: Indoor, 72°F, Perfect conditions

Based on your accumulated memories of both teams, predict:
1. Who will WIN this game?
2. What is your confidence level (50-100%)?
3. What is the most likely final score?

Provide your answer in this format:
WINNER: [SF or LA]
CONFIDENCE: [50-100]
SCORE: [SF score]-[LA score]
REASONING: [2-3 sentences based on your memories]"""

    response = llm_service.generate_completion(
        system_message="You are The Conservative Analyzer with 60 games of memory about these teams.",
        user_message=winner_prompt,
        temperature=0.6,
        max_tokens=300,
        model="deepseek/deepseek-chat-v3.1:free"
    )

    logger.info(f"\n{response.content}\n")

    await asyncio.sleep(3)

    # === PREDICTION 2: SPREAD ===
    logger.info("="*80)
    logger.info("2️⃣  SPREAD BETTING")
    logger.info("="*80)
    logger.info("Current Line: LA -3.5")

    spread_prompt = f"""{memory_summary}

SPREAD LINE: LA -3.5 (Rams favored by 3.5 points)

Based on your memories:
- How close will this game be?
- Will the Rams cover the -3.5 spread?
- What is the most likely margin of victory?

Format:
SPREAD PICK: [LA -3.5 or SF +3.5]
CONFIDENCE: [50-100]
PREDICTED MARGIN: [X points]
REASONING: [Based on your memories of close games between these teams]"""

    response = llm_service.generate_completion(
        system_message="You are The Conservative Analyzer. Use your memories of past SF-LA games.",
        user_message=spread_prompt,
        temperature=0.6,
        max_tokens=300,
        model="deepseek/deepseek-chat-v3.1:free"
    )

    logger.info(f"\n{response.content}\n")

    await asyncio.sleep(3)

    # === PREDICTION 3: TOTAL (OVER/UNDER) ===
    logger.info("="*80)
    logger.info("3️⃣  TOTAL POINTS (OVER/UNDER)")
    logger.info("="*80)
    logger.info("Current Line: 47.5")

    total_prompt = f"""{memory_summary}

TOTAL LINE: 47.5 points

Based on your memories of both teams' scoring:
- Will this be a high-scoring or low-scoring game?
- Over or Under 47.5 total points?
- What is your predicted total score?

Format:
TOTAL PICK: [OVER 47.5 or UNDER 47.5]
CONFIDENCE: [50-100]
PREDICTED TOTAL: [X points]
REASONING: [Based on offensive/defensive trends in your memories]"""

    response = llm_service.generate_completion(
        system_message="You are The Conservative Analyzer. Reference scoring patterns from your memories.",
        user_message=total_prompt,
        temperature=0.6,
        max_tokens=300,
        model="deepseek/deepseek-chat-v3.1:free"
    )

    logger.info(f"\n{response.content}\n")

    await asyncio.sleep(3)

    # === PREDICTION 4: FIRST HALF ===
    logger.info("="*80)
    logger.info("4️⃣  FIRST HALF WINNER")
    logger.info("="*80)

    half_prompt = f"""{memory_summary}

Based on your memories:
- Which team typically starts games stronger?
- Who will be leading at halftime?
- What will the halftime score be?

Format:
HALFTIME LEADER: [SF or LA]
CONFIDENCE: [50-100]
HALFTIME SCORE: [SF]-[LA]
REASONING: [Based on first half performance in your memories]"""

    response = llm_service.generate_completion(
        system_message="You are The Conservative Analyzer. Use your memories of how these teams start games.",
        user_message=half_prompt,
        temperature=0.6,
        max_tokens=300,
        model="deepseek/deepseek-chat-v3.1:free"
    )

    logger.info(f"\n{response.content}\n")

    await asyncio.sleep(3)

    # === PREDICTION 5: PLAYER PROPS ===
    logger.info("="*80)
    logger.info("5️⃣  KEY PLAYER PROPS")
    logger.info("="*80)

    props_prompt = f"""{memory_summary}

KEY PLAYERS:
- Brock Purdy (SF QB)
- Matthew Stafford (LA QB)
- Christian McCaffrey (SF RB) - if healthy
- Puka Nacua (LA WR)

Based on your memories, predict:
1. Which QB will have more passing yards?
2. Will either QB throw 2+ TDs?
3. Will the game have 3+ total TDs?
4. Which team will score first?

Format:
PASSING LEADER: [Purdy or Stafford]
QB WITH 2+ TDs: [Purdy, Stafford, Both, or Neither]
TOTAL TDs: [Over 3 or Under 3]
FIRST SCORE: [SF or LA]
REASONING: [Based on offensive patterns in your memories]"""

    response = llm_service.generate_completion(
        system_message="You are The Conservative Analyzer. Use your memories of these teams' offensive patterns.",
        user_message=props_prompt,
        temperature=0.6,
        max_tokens=400,
        model="deepseek/deepseek-chat-v3.1:free"
    )

    logger.info(f"\n{response.content}\n")

    await asyncio.sleep(3)

    # === PREDICTION 6: GAME SCRIPT ===
    logger.info("="*80)
    logger.info("6️⃣  GAME SCRIPT PREDICTION")
    logger.info("="*80)

    script_prompt = f"""{memory_summary}

Based on ALL your memories of these teams, describe:
1. How will this game unfold?
2. What will be the key turning point?
3. Which team's strategy will prevail?
4. What is the most likely game narrative?

Provide a 3-4 sentence game script prediction."""

    response = llm_service.generate_completion(
        system_message="You are The Conservative Analyzer. Synthesize all 60 games of memory into a game prediction.",
        user_message=script_prompt,
        temperature=0.7,
        max_tokens=400,
        model="deepseek/deepseek-chat-v3.1:free"
    )

    logger.info(f"\n{response.content}\n")

    # === SUMMARY ===
    logger.info("\n" + "="*80)
    logger.info("📊 PREDICTION SUMMARY")
    logger.info("="*80)
    logger.info("All predictions based on 60 accumulated memories:")
    logger.info("- 30 San Francisco 49ers games (2023-2024)")
    logger.info("- 30 Los Angeles Rams games (2023-2024)")
    logger.info("- Including head-to-head matchups")
    logger.info("")
    logger.info("🎯 The Conservative Analyzer has spoken!")
    logger.info("   Let's see how the AI's memory-based predictions perform!")
    logger.info("="*80)


if __name__ == "__main__":
    asyncio.run(predict_all_markets())
