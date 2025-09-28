"""
AI Expert System - Prediction Categories Guide
Shows exactly what each expert votes on for every game
"""

# COMPREHENSIVE PREDICTION CATEGORIES
# Each expert generates predictions across these categories for every game:

PREDICTION_CATEGORIES = {
    
    # 1. CORE GAME OUTCOME PREDICTIONS
    "game_winner": {
        "description": "Which team will win the game",
        "type": "categorical",
        "options": ["home", "away"],
        "consensus_method": "weighted_voting",
        "example": "home",
        "weight_in_final_decision": "HIGH"
    },
    
    "exact_score_home": {
        "description": "Predicted final score for home team",
        "type": "numeric",
        "range": "0-60+ points",
        "consensus_method": "weighted_average",
        "example": 27,
        "weight_in_final_decision": "HIGH"
    },
    
    "exact_score_away": {
        "description": "Predicted final score for away team", 
        "type": "numeric",
        "range": "0-60+ points",
        "consensus_method": "weighted_average",
        "example": 24,
        "weight_in_final_decision": "HIGH"
    },
    
    "margin_of_victory": {
        "description": "Point difference between winning and losing team",
        "type": "numeric",
        "range": "1-40+ points",
        "consensus_method": "weighted_average",
        "example": 3.5,
        "weight_in_final_decision": "MEDIUM"
    },
    
    # 2. BETTING LINE PREDICTIONS
    "against_the_spread": {
        "description": "Which team covers the point spread",
        "type": "categorical", 
        "options": ["home", "away", "push"],
        "consensus_method": "weighted_voting",
        "example": "away",
        "weight_in_final_decision": "HIGH"
    },
    
    "totals_over_under": {
        "description": "Will total points go over or under the line",
        "type": "categorical",
        "options": ["over", "under"],
        "consensus_method": "weighted_voting", 
        "example": "over",
        "weight_in_final_decision": "HIGH"
    },
    
    # 3. GAME FLOW PREDICTIONS
    "first_half_winner": {
        "description": "Which team leads at halftime",
        "type": "categorical",
        "options": ["home", "away", "tie"],
        "consensus_method": "weighted_voting",
        "example": "home", 
        "weight_in_final_decision": "MEDIUM"
    },
    
    "first_quarter_score": {
        "description": "Combined points scored in Q1",
        "type": "numeric",
        "range": "0-35+ points",
        "consensus_method": "weighted_average",
        "example": 14,
        "weight_in_final_decision": "LOW"
    },
    
    # 4. PLAYER PERFORMANCE PREDICTIONS
    "qb_passing_yards": {
        "description": "Combined QB passing yards for both teams",
        "type": "numeric", 
        "range": "200-600+ yards",
        "consensus_method": "weighted_average",
        "example": 485,
        "weight_in_final_decision": "MEDIUM"
    },
    
    "qb_touchdowns": {
        "description": "Total QB touchdown passes",
        "type": "numeric",
        "range": "1-8+ TDs", 
        "consensus_method": "weighted_average",
        "example": 4,
        "weight_in_final_decision": "MEDIUM"
    },
    
    "rushing_yards": {
        "description": "Combined team rushing yards",
        "type": "numeric",
        "range": "50-300+ yards",
        "consensus_method": "weighted_average", 
        "example": 156,
        "weight_in_final_decision": "LOW"
    },
    
    "turnovers": {
        "description": "Total turnovers in the game",
        "type": "numeric",
        "range": "0-8+ turnovers",
        "consensus_method": "weighted_average",
        "example": 3,
        "weight_in_final_decision": "MEDIUM"
    },
    
    # 5. SITUATIONAL FACTORS
    "weather_impact_score": {
        "description": "How much weather affects the game (0-10 scale)",
        "type": "numeric",
        "range": "0-10",
        "consensus_method": "weighted_average", 
        "example": 6.5,
        "weight_in_final_decision": "LOW"
    },
    
    "home_field_advantage": {
        "description": "Points added for home team advantage", 
        "type": "numeric",
        "range": "0-7 points",
        "consensus_method": "weighted_average",
        "example": 2.5,
        "weight_in_final_decision": "MEDIUM"
    },
    
    "injury_impact": {
        "description": "How much injuries affect outcome (0-10 scale)",
        "type": "numeric", 
        "range": "0-10",
        "consensus_method": "weighted_average",
        "example": 4.2,
        "weight_in_final_decision": "MEDIUM"
    },
    
    # 6. ADVANCED METRICS
    "upset_probability": {
        "description": "Likelihood of underdog winning",
        "type": "numeric",
        "range": "0.0-1.0",
        "consensus_method": "weighted_average",
        "example": 0.23,
        "weight_in_final_decision": "MEDIUM"
    },
    
    "game_excitement_factor": {
        "description": "How exciting/close the game will be (1-10)",
        "type": "numeric", 
        "range": "1-10",
        "consensus_method": "weighted_average",
        "example": 7.8,
        "weight_in_final_decision": "LOW"
    },
    
    "blowout_potential": {
        "description": "Likelihood of 21+ point margin",
        "type": "numeric",
        "range": "0.0-1.0", 
        "consensus_method": "weighted_average",
        "example": 0.12,
        "weight_in_final_decision": "LOW"
    }
}

# EXPERT-SPECIFIC PREDICTION EXAMPLE
def show_expert_prediction_example():
    """Shows what a complete expert prediction looks like"""
    
    example_prediction = {
        "expert_info": {
            "expert_id": "contrarian_rebel",
            "expert_name": "The Rebel", 
            "personality": "contrarian",
            "current_rank": 3,
            "overall_accuracy": 0.672
        },
        
        "game_info": {
            "game_id": "2024_week_5_buf_kc",
            "home_team": "Kansas City Chiefs",
            "away_team": "Buffalo Bills", 
            "game_time": "2024-10-15T20:20:00Z",
            "location": "Arrowhead Stadium"
        },
        
        # CORE PREDICTIONS - What the expert votes on:
        "predictions": {
            # Primary Outcomes
            "game_winner": "away",  # Bills win
            "exact_score_home": 21,  # Chiefs 21
            "exact_score_away": 28,  # Bills 28
            "margin_of_victory": 7,   # Bills by 7
            
            # Betting Lines  
            "against_the_spread": "away",  # Bills cover
            "totals_over_under": "under",   # Under 49 points
            
            # Game Flow
            "first_half_winner": "home",    # Chiefs lead at half
            "first_quarter_score": 10,     # 10 total Q1 points
            
            # Player Stats
            "qb_passing_yards": 520,        # Combined QB yards
            "qb_touchdowns": 5,            # Total QB TDs
            "rushing_yards": 89,           # Combined rushing
            "turnovers": 2,                # Total turnovers
            
            # Situational Factors
            "weather_impact_score": 3.2,   # Light weather impact
            "home_field_advantage": 2.5,   # Standard home advantage
            "injury_impact": 6.8,          # High injury impact
            
            # Advanced Metrics
            "upset_probability": 0.65,     # 65% upset chance
            "game_excitement_factor": 8.5, # Very exciting game
            "blowout_potential": 0.08      # Low blowout chance
        },
        
        # CONFIDENCE LEVELS - How sure the expert is
        "confidence_overall": 0.73,        # 73% overall confidence
        "confidence_by_category": {
            "game_winner": 0.82,          # Very confident in Bills
            "exact_score_home": 0.65,     # Moderately confident 
            "exact_score_away": 0.71,     # Good confidence
            "against_the_spread": 0.88,   # Very confident Bills cover
            "totals_over_under": 0.54,    # Low confidence on total
            "upset_probability": 0.91     # Very confident in upset
        },
        
        # REASONING - Why the expert made these picks
        "reasoning": "Contrarian analysis shows public heavily on Chiefs (-3.5). Bills have motivation edge after last playoff loss. Mahomes dealing with ankle injury (70% public unaware). Weather favors Bills rushing attack. Market overvaluing Chiefs home field vs elite road team.",
        
        "key_factors": [
            "Public betting 68% on Chiefs - fade opportunity",
            "Mahomes ankle injury undervalued by market", 
            "Bills 6-1 ATS as road underdog this season",
            "Weather conditions favor Buffalo's ground game",
            "Emotional edge for Bills after playoff loss"
        ],
        
        "personality_influence": {
            "contrarian_tendency": 0.92,    # High contrarian play
            "public_fade_factor": 0.85,     # Strong public fade
            "narrative_skepticism": 0.88,   # Doubts Chiefs hype
            "value_identification": 0.76    # Sees value in Bills
        }
    }
    
    return example_prediction

# AI COUNCIL CONSENSUS PROCESS
def show_consensus_process():
    """Shows how 5 expert votes become 1 consensus prediction"""
    
    consensus_example = {
        "game_id": "2024_week_5_buf_kc",
        
        # INDIVIDUAL EXPERT VOTES
        "expert_votes": {
            "the_analyst": {
                "game_winner": "home",      # Chiefs
                "exact_score_home": 24,
                "exact_score_away": 21, 
                "against_the_spread": "home",
                "confidence": 0.67,
                "vote_weight": 0.22
            },
            "the_rebel": {
                "game_winner": "away",      # Bills  
                "exact_score_home": 21,
                "exact_score_away": 28,
                "against_the_spread": "away", 
                "confidence": 0.73,
                "vote_weight": 0.24
            },
            "the_hunter": {
                "game_winner": "away",      # Bills
                "exact_score_home": 20,
                "exact_score_away": 26,
                "against_the_spread": "away",
                "confidence": 0.69, 
                "vote_weight": 0.21
            },
            "the_quant": {
                "game_winner": "home",      # Chiefs
                "exact_score_home": 27,
                "exact_score_away": 23,
                "against_the_spread": "home",
                "confidence": 0.81,
                "vote_weight": 0.18
            },
            "the_chaos": {
                "game_winner": "away",      # Bills
                "exact_score_home": 17,
                "exact_score_away": 31,
                "against_the_spread": "away", 
                "confidence": 0.59,
                "vote_weight": 0.15
            }
        },
        
        # WEIGHTED CONSENSUS RESULTS
        "consensus_predictions": {
            "game_winner": {
                "value": "away",            # Bills (3 votes vs 2)
                "confidence": 0.68,         # Weighted average confidence
                "agreement_level": 0.60,    # 60% agreement
                "vote_breakdown": {
                    "away": 0.60,          # 60% weighted vote share
                    "home": 0.40           # 40% weighted vote share
                }
            },
            
            "exact_score_home": {
                "value": 21.8,             # Weighted average: ~22
                "confidence": 0.69,
                "agreement_level": 0.85,    # High agreement on score
                "vote_breakdown": {
                    "range": "20-27 points",
                    "std_deviation": 2.9
                }
            },
            
            "exact_score_away": {
                "value": 25.6,             # Weighted average: ~26  
                "confidence": 0.71,
                "agreement_level": 0.78,
                "vote_breakdown": {
                    "range": "21-31 points", 
                    "std_deviation": 3.8
                }
            },
            
            "against_the_spread": {
                "value": "away",           # Bills cover
                "confidence": 0.72,
                "agreement_level": 0.60,
                "vote_breakdown": {
                    "away": 0.60,         # Bills cover spread
                    "home": 0.40          # Chiefs cover spread
                }
            }
        },
        
        # FINAL CONSENSUS SUMMARY
        "final_prediction": {
            "winner": "Buffalo Bills",
            "score": "Bills 26, Chiefs 22", 
            "spread_pick": "Bills +3.5 ✓",
            "confidence": "68% (Moderate-High)",
            "key_consensus": "Bills upset on road, close game"
        }
    }
    
    return consensus_example

if __name__ == "__main__":
    print("🎯 AI EXPERT SYSTEM - PREDICTION CATEGORIES")
    print("="*60)
    
    print(f"\n📊 TOTAL PREDICTION CATEGORIES: {len(PREDICTION_CATEGORIES)}")
    print("\nEach expert votes on these categories for EVERY game:")
    
    for category, details in PREDICTION_CATEGORIES.items():
        print(f"\n• {category.upper().replace('_', ' ')}")
        print(f"  └─ {details['description']}")
        print(f"  └─ Type: {details['type']} | Method: {details['consensus_method']}")
        print(f"  └─ Example: {details['example']} | Weight: {details['weight_in_final_decision']}")
    
    print(f"\n" + "="*60)
    print("🏆 AI COUNCIL CONSENSUS PROCESS")
    print("="*60)
    print("5 experts vote → Weighted by performance → 1 consensus prediction")
    
    print(f"\n💡 KEY INSIGHT:")
    print("Each expert's vote weight is calculated based on:")
    print("• Overall accuracy (40%)")  
    print("• Recent performance trend (30%)")
    print("• Prediction confidence (20%)")
    print("• Council tenure/experience (10%)")
    
    print(f"\n🎮 LIVE EXAMPLE:")
    consensus = show_consensus_process()
    final = consensus["final_prediction"]
    print(f"Consensus: {final['winner']} wins {final['score']}")
    print(f"Spread: {final['spread_pick']}")
    print(f"Confidence: {final['confidence']}")