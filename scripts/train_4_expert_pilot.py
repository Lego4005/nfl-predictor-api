#!/usr/bin/env python3
"""
4-Expert Pilot Training & Evaluation Framework
Implements the full training loop with baselines and go/no-go gates.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from pathlib import Path

from src.services.supabase_service import SupabaseService
from src.services.orchestrator_model_switcher import OrchestratorModelSwitcher
from src.services.agentuity_adapter import AgentuityAdapter
from src.validation.expert_predictions_validator import ExpertPredictionsValidator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TrainingPhase:
    name: str
    start_date: str
    end_date: str
    enable_tools: bool
    enable_stakes: bool
    description: str

@dataclass
class BaselineResult:
    name: str
    win_rate: float
    brier_score: float
    roi: float
    total_games: int

class FourExpertPilotTrainer:
    """
    Comprehensive training and evaluation system for 4-expert pilot.
    Implements Phase A (Learn 2020-2023), Phase B (Backtest 2024), Phase C (2025 YTD).
    """

    def __init__(self):
        self.supabase = SupabaseService()
        self.model_switcher = OrchestratorModelSwitcher(self.supabase)
        self.agentuity = AgentuityAdapter()
        self.validator = ExpertPredictionsValidator()

        # 4 pilot experts with max personality spread
        self.pilot_experts = [
            'conservative_analyzer',
            'momentum_rider',
            'contrarian_rebel',
            'value_hunter'
        ]

        # Training phases
        self.phases = [
            TrainingPhase(
                name="Phase A - Learn 2020-2023",
                start_date="2020-09-01",
                end_date="2023-12-31",
                enable_tools=False,  # Start with no tools
                enable_stakes=False,  # Learning focus
                description="Chronological learning to build episodic memories"
            ),
            TrainingPhase(
                name="Phase A2 - Learn 2020-2023 (Tools)",
                start_date="2020-09-01",
                end_date="2023-12-31",
                enable_tools=True,   # Enable tools
                enable_stakes=False,  # Still learning
                description="Same period with tools enabled for comparison"
            ),
            TrainingPhase(
                name="Phase B - Backtest 2024",
                start_date="2024-01-01",
                end_date="2024-12-31",
                enable_tools=True,
                enable_stakes=True,   # Full stakes for PnL
                description="Full 2024 season with baselines comparison"
            ),
            TrainingPhase(
                name="Phase C - 2025 YTD",
                start_date="2025-01-01",
                end_date="2025-10-09",  # Current date
                enable_tools=True,
                enable_stakes=True,
                description="Current season validation"
            )
        ]

    async def run_full_training_pipeline(self) -> Dict:
        """Execute complete training pipeline with all phases and baselines"""

        logger.info("Starting 4-Expert Pilot Training Pipeline")
        results = {}

        # Phase A: Learning (2020-2023)
        logger.info("=== PHASE A: LEARNING 2020-2023 ===")
        phase_a_results = await self.run_learning_phase()
        results['phase_a'] = phase_a_results

        # Phase B: Backtesting 2024 with baselines
        logger.info("=== PHASE B: BACKTEST 2024 WITH BASELINES ===")
        phase_b_results = await self.run_backtest_phase()
        results['phase_b'] = phase_b_results

        # Go/No-Go evaluation
        go_decision = self.evaluate_go_no_go(phase_b_results)
        results['go_no_go'] = go_decision

        if go_decision['proceed_to_full_system']:
            logger.info("✅ GO DECISION: Proceeding to full 15-expert system")
        else:
            logger.warning("❌ NO-GO: Need improvements before scaling")

        # Phase C: 2025 validation (if go decision)
        if go_decision['proceed_to_full_system']:
            logger.info("=== PHASE C: 2025 YTD VALIDATION ===")
            phase_c_results = await self.run_current_season_validation()
            results['phase_c'] = phase_c_results

        # Generate comprehensive report
        report = self.generate_training_report(results)
        await self.save_training_results(results, report)

        return results
