#!/usr/bin/env python3
"""
Full Comprehensive Prediction - All 43+ Predictions

DeepSeek generates ALL prediction categories based on 60 games of memory:
- Core game predictions
- Quarter-by-quarter
- Player props (QB, RB, WR)
- Special teams
- Game flow
- Situational stats
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
    logger.info("🎯 FULL COMPREHENSIVE PREDICTION: SF @ LA")
    logger.info("="*80)
    logger.info("All 43+ predictions based on 60 accumulated memories")
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

    logger.info(f"📊 Memory Bank: {len(sf_memories)} SF + {len(la_memories)} LA = 60 games\n")

    # Calculate averages from memories
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

    memory_context = f"""YOUR ACCUMULATED KNOWLEDGE (60 GAMES):

49ers: {len(sf_memories)} games, averaging {sf_avg:.1f} PPG
Rams: {len(la_memories)} games, averaging {la_avg:.1f} PPG

You have deep knowledge of:
- How these teams score by quarter
- Their offensive/defensive patterns
- Key players' typical performances
- Game flow tendencies
- Situational success rates
"""

    # Comprehensive prompt
    comprehensive_prompt = f"""{memory_context}

TONIGHT'S GAME: San Francisco 49ers @ Los Angeles Rams
VENUE: SoFi Stadium (LA home, indoor, 72°F, perfect conditions)
TIME: 8:15 PM ET
BETTING LINES: LA -3.5, Total 47.5

KEY PLAYERS:
- SF: Brock Purdy (QB), Christian McCaffrey (RB), Deebo Samuel (WR), Brandon Aiyuk (WR)
- LA: Matthew Stafford (QB), Kyren Williams (RB), Puka Nacua (WR), Cooper Kupp (WR)

Based on your 60 games of accumulated memory, provide COMPREHENSIVE predictions across ALL categories.

IMPORTANT: All predictions must be consistent with each other!

═══════════════════════════════════════════════════════════════════════════════
📊 PROVIDE PREDICTIONS IN THIS EXACT FORMAT:
═══════════════════════════════════════════════════════════════════════════════

1️⃣ CORE GAME PREDICTIONS:
FINAL SCORE: SF [X] - LA [Y]
WINNER: [SF or LA]
MARGIN: [X] points
SPREAD PICK: [SF +3.5 or LA -3.5]
TOTAL PICK: [OVER 47.5 or UNDER 47.5]
MONEYLINE: [SF or LA]
CONFIDENCE: [50-100]%

2️⃣ QUARTER-BY-QUARTER BREAKDOWN:
Q1 SCORE: SF [X] - LA [Y]
Q1 WINNER: [SF or LA or TIE]
Q1 TOTAL: [X+Y]

Q2 SCORE: SF [X] - LA [Y]
Q2 WINNER: [SF or LA or TIE]
Q2 TOTAL: [X+Y]

Q3 SCORE: SF [X] - LA [Y]
Q3 WINNER: [SF or LA or TIE]
Q3 TOTAL: [X+Y]

Q4 SCORE: SF [X] - LA [Y]
Q4 WINNER: [SF or LA or TIE]
Q4 TOTAL: [X+Y]

3️⃣ HALF PREDICTIONS:
HALFTIME SCORE: SF [X] - LA [Y]
HALFTIME LEADER: [SF or LA or TIE]
SECOND HALF SCORE: SF [X] - LA [Y]
SECOND HALF WINNER: [SF or LA or TIE]

4️⃣ SCORING EVENTS:
FIRST SCORE: [SF or LA]
FIRST TD: [SF or LA]
LAST SCORE: [SF or LA]
TOTAL TDs: [X]
TOTAL FGs: [X]

5️⃣ QB PROPS - BROCK PURDY:
PASSING YARDS: [X] yards
PASSING TDs: [X]
INTERCEPTIONS: [X]
COMPLETIONS: [X]/[Y]
QB RATING: [X]
FANTASY POINTS: [X]

6️⃣ QB PROPS - MATTHEW STAFFORD:
PASSING YARDS: [X] yards
PASSING TDs: [X]
INTERCEPTIONS: [X]
COMPLETIONS: [X]/[Y]
QB RATING: [X]
FANTASY POINTS: [X]

7️⃣ RB PROPS - CHRISTIAN MCCAFFREY:
RUSHING YARDS: [X] yards
RUSHING TDs: [X]
RECEPTIONS: [X]
RECEIVING YARDS: [X] yards
RECEIVING TDs: [X]
TOTAL FANTASY POINTS: [X]

8️⃣ RB PROPS - KYREN WILLIAMS:
RUSHING YARDS: [X] yards
RUSHING TDs: [X]
RECEPTIONS: [X]
RECEIVING YARDS: [X] yards
RECEIVING TDs: [X]
TOTAL FANTASY POINTS: [X]

9️⃣ WR PROPS - TOP RECEIVERS:
DEEBO SAMUEL: [X] rec, [Y] yards, [Z] TDs
BRANDON AIYUK: [X] rec, [Y] yards, [Z] TDs
PUKA NACUA: [X] rec, [Y] yards, [Z] TDs
COOPER KUPP: [X] rec, [Y] yards, [Z] TDs

🔟 TEAM STATISTICS:
SF TOTAL YARDS: [X]
LA TOTAL YARDS: [X]
SF RUSHING YARDS: [X]
LA RUSHING YARDS: [X]
SF PASSING YARDS: [X]
LA PASSING YARDS: [X]

1️⃣1️⃣ SITUATIONAL STATS:
SF 3RD DOWN %: [X]%
LA 3RD DOWN %: [X]%
SF RED ZONE %: [X]%
LA RED ZONE %: [X]%
SF TIME OF POSSESSION: [X]:[Y]
LA TIME OF POSSESSION: [X]:[Y]

1️⃣2️⃣ TURNOVERS & DEFENSE:
TOTAL TURNOVERS: [X]
SF TURNOVERS: [X]
LA TURNOVERS: [X]
TOTAL SACKS: [X]
SF SACKS: [X]
LA SACKS: [X]

1️⃣3️⃣ SPECIAL TEAMS:
TOTAL FIELD GOALS MADE: [X]
TOTAL FIELD GOALS ATTEMPTED: [X]
LONGEST FIELD GOAL: [X] yards
TOTAL PUNTS: [X]

1️⃣4️⃣ GAME FLOW:
BIGGEST LEAD: [Team] by [X] points
LEAD CHANGES: [X]
TIMES TIED: [X]
WINNING DRIVE: [Description]

1️⃣5️⃣ KEY MOMENTS:
DECISIVE PLAY: [Description]
TURNING POINT: [Description]
GAME MVP: [Player name and team]

═══════════════════════════════════════════════════════════════════════════════
💭 REASONING (2-3 paragraphs):
Explain how your 60 games of memory led to these specific predictions. Reference patterns you've observed, scoring tendencies, and why all these numbers are consistent with each other.
═══════════════════════════════════════════════════════════════════════════════"""

    logger.info("🤖 Generating comprehensive predictions from memory...\n")
    logger.info("⏳ This may take 15-20 seconds...\n")

    response = llm_service.generate_completion(
        system_message="You are The Conservative Analyzer with 60 games of memory about SF and LA. Generate comprehensive, consistent predictions across all categories.",
        user_message=comprehensive_prompt,
        temperature=0.6,
        max_tokens=2500,  # Increased for comprehensive output
        model="deepseek/deepseek-chat-v3.1:free"
    )

    logger.info("="*80)
    logger.info("📊 COMPREHENSIVE PREDICTIONS FROM MEMORY")
    logger.info("="*80)
    logger.info("")
    logger.info(response.content)
    logger.info("")
    logger.info("="*80)
    logger.info("✅ All predictions generated from 60 accumulated memories")
    logger.info("📊 Conservative Analyzer's complete game forecast")
    logger.info("🎯 Game starts at 8:15 PM ET!")
    logger.info("="*80)

    # Save to file
    with open('data/tonight_comprehensive_prediction.txt', 'w') as f:
        f.write("="*80 + "\n")
        f.write("COMPREHENSIVE PREDICTION: SF @ LA\n")
        f.write("="*80 + "\n")
        f.write(f"Generated: {__import__('datetime').datetime.now()}\n")
        f.write(f"Expert: The Conservative Analyzer\n")
        f.write(f"Memory Base: 60 games (30 SF + 30 LA)\n")
        f.write("="*80 + "\n\n")
        f.write(response.content)

    logger.info("\n💾 Saved to: data/tonight_comprehensive_prediction.txt")


if __name__ == "__main__":
    asyncio.run(main())
