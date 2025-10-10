#!/usr/bin/env python3
"""
Start Pilot System - Simplified OpenRouter Setup
startup script for the 4-expert pilot system using OpenRouter.
Handles all the setup steps from the runbook in a single command.

Usage:
    python3 scripts/start_pilot_system.py --mode setup
    python3 scripts/start_pilot_system.py --mode train --seasons 2020-2023
    python3 scripts/start_pilot_system.py --mode backtest --season 2024 --week 1
"""

import asyncio
import argparse
import logging
import os
import time
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.supabase_service import SupabaseService
from src.services.openrouter_llm_service import get_llm_service
from src.services.end_to_end_smoke_test_service import EndToEndSmokeTestService

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PilotSystemStarter:
    """Handles pilot system startup and configuration"""

    def __init__(self):
        self.run_id = os.getenv('RUN_ID', 'run_2025_pilot4')
        self.supabase = SupabaseService()
        self.llm_service = get_llm_service()

        # 4-expert pilot configuration
        self.pilot_experts = [
            'conservative_analyzer',
            'momentum_rider',
            'contrarian_rebel',
            'value_hunter'
        ]

        print(f"🚀 NFL Expert Council Betting System - 4-Expert Pilot")
        print(f"📊 Run ID: {self.run_id}")
        print(f"🧠 Experts: {', '.join(self.pilot_experts)}")

    async def setup_system(self) -> bool:
        """Complete system setup"""
        print("\n🔧 Setting up pilot system...")

        try:
            # 1. Test OpenRouter connection
            print("1️⃣ Testing OpenRouter connection...")
            connection_test = await self.llm_service.test_connection()

            if not connection_test['success']:
                print(f"❌ OpenRouter connection failed: {connection_test['error']}")
                print("Please check your OPENROUTER_API_KEY in .env file")
                return False

            print("✅ OpenRouter connection successful")
            print("📋 Available models:")
            for model in connection_test['available_models']:
                print(f"   • {model}")

            # 2. Test database connection
            print("\n2️⃣ Testing database connection...")
            try:
                response = await self.supabase.table('games').select('count', count='exact').limit(1).execute()
                print(f"✅ Database connected ({response.count} games available)")
            except Exception as e:
                print(f"❌ Database connection failed: {e}")
                return False

            # 3. Initialize expert bankrolls
            print("\n3️⃣ Initializing expert bankrolls...")
            for expert_id in self.pilot_experts:
                try:
                    await self.supabase.table('expert_bankroll').upsert({
                        'expert_id': expert_id,
                        'run_id': self.run_id,
                        'current_bankroll': 100.0,
                        'total_wagered': 0.0,
                        'total_winnings': 0.0,
                        'games_played': 0
                    }).execute()
                    print(f"✅ {expert_id} bankroll initialized")
                except Exception as e:
                    print(f"⚠️ {expert_id} bankroll setup warning: {e}")

            # 4. Initialize calibration priors
            print("\n4️⃣ Initializing calibration priors...")
            for expert_id in self.pilot_experts:
                try:
                    await self.supabase.table('expert_category_calibration').upsert({
                        'expert_id': expert_id,
                        'run_id': self.run_id,
                        'category': 'default',
                        'alpha': 1.0,
                        'beta': 1.0,
                        'ema_mean': 0.0,
                        'ema_variance': 1.0
                    }).execute()
                    print(f"✅ {expert_id} calibration initialized")
                except Exception as e:
                    print(f"⚠️ {expert_id} calibration setup warning: {e}")

            # 5. Run system health check
            print("\n5️⃣ Running system health check...")
            smoke_test_service = EndToEndSmokeTestService(self.supabase)
            health_result = await smoke_test_service.validate_system_health()

            if health_result['overall_healthy']:
                print("✅ System health check passed")
            else:
                print("⚠️ System health check warnings:")
                for check, status in health_result['checks'].items():
                    icon = "✅" if status else "❌"
                    print(f"   {icon} {check.replace('_', ' ').title()}")

            print("\n🎉 Pilot system setup complete!")
            print("\n📋 Model Assignments:")
            assignments = self.llm_service.model_mappings
            for expert_id in self.pilot_experts:
                model = assignments.get(expert_id, 'unknown')
                print(f"   • {expert_id} → {model}")

            print("\n🔧 System Configuration:")
            print(f"   • Critic/Repair: {assignments.get('critic_repair', 'claude-3.5-sonnet')}")
            print(f"   • Shadow Models: Gemini Pro, Grok Beta")
            print(f"   • Run Isolation: {self.run_id}")
            print(f"   • Expert Count: {len(self.pilot_experts)}")

            print("\n✅ Ready for training or backtesting!")
            return True

        except Exception as e:
            print(f"❌ Setup failed: {e}")
            return False

    async def quick_test(self) -> bool:
        """Quick system test"""
        print("\n🧪 Running quick system test...")

        try:
            # Test LLM call
            print("1️⃣ Testing LLM generation...")
            test_result = await self.llm_service.generate_expert_prediction(
                expert_id='conservative_analyzer',
                system_prompt='You are a conservative NFL analyst.',
                user_prompt='Predict the winner of Chiefs vs Bills. Respond with JSON: {"winner": "Chiefs", "confidence": 0.65}'
            )

            if test_result['success']:
                print(f"✅ LLM test successful (model: {test_result['model_used']})")
            else:
                print(f"❌ LLM test failed: {test_result['error']}")
                return False

            # Test database write
            print("2️⃣ Testing database write...")
            test_record = {
                'expert_id': 'test_expert',
                'run_id': self.run_id,
                'game_id': 'test_game',
                'predictions': [{'test': True}],
                'overall_confidence': 0.5,
                'created_at': datetime.now().isoformat()
            }

            try:
                await self.supabase.table('expert_predictions').insert(test_record).execute()
                print("✅ Database write successful")

                # Clean up test record
                await self.supabase.table('expert_predictions')\
                    .delete()\
                    .eq('expert_id', 'test_expert')\
                    .eq('run_id', self.run_id)\
                    .execute()

            except Exception as e:
                print(f"❌ Database write failed: {e}")
                return False

            print("\n✅ Quick test passed - system ready!")
            return True

        except Exception as e:
            print(f"❌ Quick test failed: {e}")
            return False

    def show_next_steps(self, mode: str):
        """Show next steps based on mode"""
        print("\n🎯 Next Steps:")

        if mode == 'setup':
            print("1. Run training pass:")
            print("   python3 scripts/start_pilot_system.py --mode train --seasons 2020-2023")
            print("\n2. Or run quick test:")
            print("   python3 scripts/start_pilot_system.py --mode test")

        elif mode == 'train':
            print("1. Check training completion:")
            print("   python3 scripts/check_training_completion.py --run-id run_2025_pilot4")
            print("\n2. Run backtest when ready:")
            print("   python3 scripts/start_pilot_system.py --mode backtest --season 2024 --week 1")

        elif mode == 'backtest':
            print("1. Analyze results:")
            print("   curl http://localhost:8000/api/baseline-testing/compare")
            print("\n2. Check expert performance:")
            print("   curl http://localhost:8000/api/leaderboard")

        elif mode == 'test':
            print("1. Run full training:")
            print("   python3 scripts/start_pilot_system.py --mode train --seasons 2020-2023")
            print("\n2. Monitor system:")
            print("   python3 scripts/system_status.py")

async def main():
    """Main startup function"""
    parser = argparse.ArgumentParser(description='Start Pilot System')
    parser.add_argument('--mode', required=True,
                       choices=['setup', 'train', 'backtest', 'test'],
                       help='Operation mode')
    parser.add_argument('--seasons', help='Comma-separated seasons for training (e.g., 2020,2021,2022,2023)')
    parser.add_argument('--season', help='Season for backtesting (e.g., 2024)')
    parser.add_argument('--week', type=int, help='Week for backtesting (optional)')

    args = parser.parse_args()

    # Create system starter
    starter = PilotSystemStarter()

    try:
        if args.mode == 'setup':
            success = await starter.setup_system()
            if success:
                starter.show_next_steps('setup')
                return 0
            else:
                return 1

        elif args.mode == 'test':
            setup_success = await starter.setup_system()
            if not setup_success:
                return 1

            test_success = await starter.quick_test()
            if test_success:
                starter.show_next_steps('test')
                return 0
            else:
                return 1

        elif args.mode == 'train':
            if not args.seasons:
                print("❌ --seasons required for training mode")
                return 1

            print(f"\n🎓 Starting training for seasons: {args.seasons}")
            print("📝 This would run the training script...")
            print(f"Command: python3 scripts/pilot_training_runner.py --run-id {starter.run_id} --seasons {args.seasons} --experts {','.join(starter.pilot_experts)} --stakes 0 --reflections off --tools off")

            starter.show_next_steps('train')
            return 0

        elif args.mode == 'backtest':
            if not args.season:
                print("❌ --season required for backtest mode")
                return 1

            week_str = f" --week {args.week}" if args.week else ""
            print(f"\n📊 Starting backtest for season {args.season}{f' week {args.week}' if args.week else ''}...")
            print("📝 This would run the backtest script...")
            print(f"Command: python3 scripts/pilot_backtest_runner.py --run-id {starter.run_id} --season {args.season}{week_str} --experts {','.join(starter.pilot_experts)} --baselines coin_flip,market_only,one_shot,deliberate --stakes 1.0")

            starter.show_next_steps('backtest')
            return 0

    except Exception as e:
        print(f"\n❌ Operation failed: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
