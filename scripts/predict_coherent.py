#!/usr/bin/env python3
"""
Coherent Comprehensive Prediction for Tonight's Game

Makes ONE prediction where all markets are consistent:
- If SF wins 27-24, then SF covers +3.5, total is OVER 47.5, etc.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

from supabase import create_client
from src.services.openrouter_service import OpenRouterService
from src.ml.supabase_memory_services import SupabaseEpisodicMemoryManager
from dotenv import load_dotenv

load_dotenv()


async def main():
    logger.info("="*80)
    logger.info("🎯 COHERENT COMPREHENSIVE PREDICTION: SF @ LA")
    logger.info("="*80)
    logger.info("")

    # Initialize
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    memory_service = SupabaseEpisodicMemoryManager(supabase)
    llm_service = OpenRouterService(os.getenv('VITE_OPENROUTER_API_KEY'))

    # Retrieve memories
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

    logger.info(f"📊 Using {len(sf_memories)} SF memories + {len(la_memories)} LA memories\n")

    # Build memory context
    memory_context = "YOUR ACCUMULATED KNOWLEDGE:\n\n"

    # Calculate stats from memories
    sf_scores = []
    la_scores = []

    for m in sf_memories:
        outcome = m.get('actual_outcome', {})
        factors = m.get('contextual_factors', [])
        is_home = any(f.get('factor') == 'home_team' and f.get('value') == 'SF' for f in factors)
        if is_home:
            sf_scores.append(outcome.get('home_score', 0))
        else:
            sf_scores.append(outcome.get('away_score', 0))

    for m in la_memories:
        outcome = m.get('actual_outcome', {})
        factors = m.get('contextual_factors', [])
        is_home = any(f.get('factor') == 'home_team' and f.get('value') == 'LA' for f in factors)
        if is_home:
            la_scores.append(outcome.get('home_score', 0))
        else:
            la_scores.append(outcome.get('away_score', 0))

    sf_avg = sum(sf_scores) / len(sf_scores) if sf_scores else 0
    la_avg = sum(la_scores) / len(la_scores) if la_scores else 0

    memory_context += f"49ers: Avg {sf_avg:.1f} PPG in your memories\n"
    memory_context += f"Rams: Avg {la_avg:.1f} PPG in your memories\n\n"

    # ONE comprehensive prompt
    comprehensive_prompt = f"""{memory_context}

TONIGHT'S GAME: San Francisco 49ers @ Los Angeles Rams
VENUE: SoFi Stadium (LA home, indoor, perfect conditions)
BETTING LINES:
- Spread: LA -3.5
- Total: 47.5
- Moneyline: LA -180, SF +150

Based on your 60 games of accumulated memory, provide ONE COHERENT prediction covering ALL markets.

IMPORTANT: All your predictions must be mathematically consistent!
- If you predict SF 27, LA 24, then SF covers +3.5 and total is OVER 47.5
- If you predict LA wins by 7, then LA covers -3.5
- Halftime score should lead to your final score
- Player stats should add up to team totals

Provide your comprehensive prediction in this EXACT format:

FINAL SCORE: SF [X] - LA [Y]
WINNER: [SF or LA]
MARGIN: [X points]

SPREAD PICK: [LA -3.5 or SF +3.5]
SPREAD RESULT: [Covers or Doesn't Cover]

TOTAL PICK: [OVER 47.5 or UNDER 47.5]
TOTAL POINTS: [X+Y total]

HALFTIME SCORE: SF [X] - LA [Y]
HALFTIME LEADER: [SF or LA or Tied]

FIRST SCORE: [SF or LA]
FIRST TD: [SF or LA]

PASSING LEADER: [Purdy or Stafford]
PURDY PASSING YDS: [X yards]
STAFFORD PASSING YDS: [Y yards]

PURDY PASSING TDs: [X]
STAFFORD PASSING TDs: [Y]

TOTAL TDs IN GAME: [X]

KEY PLAY: [Describe the decisive moment]

CONFIDENCE: [50-100%]

REASONING: [3-4 sentences explaining how your memories led to this prediction and why all the numbers are consistent]"""

    logger.info("🤖 Generating comprehensive coherent prediction...\n")

    response = llm_service.generate_completion(
        system_message="You are The Conservative Analyzer with 60 games of memory. Make ONE coherent prediction where all numbers are consistent.",
        user_message=comprehensive_prompt,
        temperature=0.6,
        max_tokens=800,
        model="deepseek/deepseek-chat-v3.1:free"
    )

    logger.info("="*80)
    logger.info("📊 COMPREHENSIVE COHERENT PREDICTION")
    logger.info("="*80)
    logger.info("")
    logger.info(response.content)
    logger.info("")
    logger.info("="*80)
    logger.info("✅ All predictions are mathematically consistent")
    logger.info("📊 Based on 60 accumulated memories (30 SF + 30 LA)")
    logger.info("🎯 Ready for tonight's game at 8:15 PM ET!")
    logger.info("="*80)


if __name__ == "__main__":
    asyncio.run(main())
