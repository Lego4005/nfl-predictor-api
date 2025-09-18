#!/usr/bin/env python3
"""
Setup 15 personality experts in the database
"""

import os
import sys
from supabase import create_client
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

def setup_experts():
    # Initialize Supabase client
    supabase_url = os.getenv('VITE_SUPABASE_URL')
    supabase_key = os.getenv('VITE_SUPABASE_ANON_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase credentials")
        return

    supabase = create_client(supabase_url, supabase_key)

    # 15 personality experts - matching actual DB schema
    expert_data = [
        ("the_analyst", "The Analyst", "analytical", "Pure statistical analysis and data patterns", 0.75),
        ("the_veteran", "The Veteran", "conservative", "Experience-based wisdom and historical patterns", 0.80),
        ("the_contrarian", "The Contrarian", "contrarian", "Fades public opinion and conventional wisdom", 0.65),
        ("the_gambler", "The Gambler", "intuitive", "Gut instincts and betting market feel", 0.70),
        ("the_momentum_rider", "The Momentum Rider", "momentum", "Reads current team energy and flow", 0.68),
        ("the_matchup_expert", "The Matchup Expert", "analytical", "Deep statistical matchup analysis", 0.78),
        ("the_chaos_theorist", "The Chaos Theorist", "contrarian", "Expects variance and unpredictable outcomes", 0.60),
        ("the_home_field_guru", "The Home Field Guru", "situational", "Specializes in venue and crowd effects", 0.72),
        ("the_weather_watcher", "The Weather Watcher", "analytical", "Focuses on environmental game conditions", 0.74),
        ("the_injury_tracker", "The Injury Tracker", "conservative", "Analyzes roster health and availability", 0.76),
        ("the_referee_reader", "The Referee Reader", "analytical", "Studies officiating crew tendencies", 0.71),
        ("the_primetime_prophet", "The Primetime Prophet", "situational", "Specializes in nationally televised games", 0.73),
        ("the_divisional_detective", "The Divisional Detective", "conservative", "Expert in rivalry and division dynamics", 0.77),
        ("the_playoff_predictor", "The Playoff Predictor", "momentum", "Reads postseason intensity and pressure", 0.69),
        ("the_upset_specialist", "The Upset Specialist", "contrarian", "Identifies underdog opportunities", 0.64)
    ]

    experts = []
    for expert_id, name, personality_type, specialty, confidence in expert_data:
        expert = {
            "expert_id": expert_id,
            "name": name,
            "personality_traits": {
                "type": personality_type,
                "specialty": specialty,
                "confidence_baseline": confidence,
                "risk_tolerance": "moderate" if personality_type == "analytical" else "high" if personality_type == "contrarian" else "low",
                "data_dependency": "high" if personality_type == "analytical" else "medium" if personality_type == "conservative" else "low"
            },
            "decision_style": "data_driven" if personality_type == "analytical" else "experience_based" if personality_type == "conservative" else "contrarian" if personality_type == "contrarian" else "momentum_based",
            "learning_rate": 0.05 if personality_type == "analytical" else 0.03 if personality_type == "conservative" else 0.08,
            "current_weights": {},
            "performance_stats": {}
        }
        experts.append(expert)

    print("🔧 Setting up 15 personality experts in database...")

    try:
        # First, let's check if experts already exist
        existing = supabase.table('personality_experts').select('expert_id').execute()
        existing_ids = [row['expert_id'] for row in existing.data] if existing.data else []

        # Insert new experts only
        new_experts = [expert for expert in experts if expert['expert_id'] not in existing_ids]

        if new_experts:
            result = supabase.table('personality_experts').insert(new_experts).execute()
            print(f"✅ Inserted {len(new_experts)} new experts into database")
            for expert in new_experts:
                print(f"   • {expert['name']} ({expert['personality_type']})")
        else:
            print("✅ All experts already exist in database")

        # Verify all experts are present
        final_check = supabase.table('personality_experts').select('expert_id, name').execute()
        print(f"\n📊 Total experts in database: {len(final_check.data)}")

        return True

    except Exception as e:
        print(f"❌ Error setting up experts: {e}")
        return False

if __name__ == "__main__":
    setup_experts()