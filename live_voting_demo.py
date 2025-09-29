"""
AI Expert System - Live Voting Example
Shows exactly how 15 experts vote and 5 AI Council members reach consensus
"""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def demonstrate_live_voting():
    """Show a real example of expert voting and consensus building"""
    
    print("🗳️  LIVE EXPERT VOTING DEMONSTRATION")
    print("="*70)
    
    # Initialize the system
    from src.ml.expert_competition.competition_framework import ExpertCompetitionFramework
    framework = ExpertCompetitionFramework(supabase_client=None)
    
    # Get current AI Council
    council_members = await framework.select_ai_council()
    
    print(f"\n📋 GAME: Buffalo Bills @ Kansas City Chiefs")
    print(f"📅 Spread: Chiefs -3.5 | Total: 49.5 | Weather: Clear, 72°F")
    print(f"\n👥 Current AI Council (Top 5 Performers):")
    for i, expert_id in enumerate(council_members, 1):
        expert = framework.experts[expert_id]
        rank = getattr(expert, 'current_rank', i)
        accuracy = getattr(expert, 'overall_accuracy', 0.5)
        print(f"   {i}. {expert.name} (Rank #{rank}, {accuracy:.1%} accuracy)")
    
    print(f"\n" + "="*70)
    print("🎯 INDIVIDUAL EXPERT VOTES")
    print("="*70)
    
    # Simulate expert predictions
    import random
    expert_votes = {}
    
    # Generate predictions for each council member
    for expert_id in council_members:
        expert = framework.experts[expert_id]
        
        # Simulate personality-driven predictions
        if expert.name == "The Analyst":
            # Conservative, data-driven
            winner = "home"  # Goes with favorite
            home_score = 26
            away_score = 20
            spread_pick = "home"
            confidence = 0.72
            reasoning = "Chiefs at home with superior QB rating and red zone efficiency"
            
        elif expert.name == "The Rebel":
            # Contrarian
            winner = "away"  # Fades public
            home_score = 21
            away_score = 28  
            spread_pick = "away"
            confidence = 0.81
            reasoning = "Public heavily on Chiefs, Bills motivated after playoff loss"
            
        elif expert.name == "The Gambler":
            # High-risk, aggressive
            winner = "away"
            home_score = 17
            away_score = 35
            spread_pick = "away" 
            confidence = 0.69
            reasoning = "Bills blow out Chiefs in statement game, live bet opportunity"
            
        elif expert.name == "The Hunter":
            # Value-focused
            winner = "away"
            home_score = 23
            away_score = 27
            spread_pick = "away"
            confidence = 0.74
            reasoning = "Bills +3.5 offers value, market overreacting to Chiefs home field"
            
        elif expert.name == "The Quant":
            # Statistics-pure
            winner = "home"
            home_score = 24
            away_score = 21
            spread_pick = "home"
            confidence = 0.78
            reasoning = "Chiefs win 67% at home vs elite teams, regression model favors KC"
            
        else:
            # Default random for any other expert
            winner = random.choice(["home", "away"])
            home_score = random.randint(17, 31)
            away_score = random.randint(17, 31)
            spread_pick = random.choice(["home", "away"])
            confidence = random.uniform(0.5, 0.85)
            reasoning = f"Mock prediction from {expert.name}"
        
        expert_votes[expert_id] = {
            "expert_name": expert.name,
            "winner_prediction": winner,
            "exact_score_home": home_score,
            "exact_score_away": away_score,
            "against_the_spread": spread_pick,
            "confidence_overall": confidence,
            "reasoning": reasoning
        }
        
        # Display the vote
        team_name = "Chiefs" if winner == "home" else "Bills"
        spread_team = "Chiefs" if spread_pick == "home" else "Bills"
        print(f"\n🔸 {expert.name.upper()}")
        print(f"   Winner: {team_name} ({home_score}-{away_score})")
        print(f"   Spread: {spread_team} cover the spread")
        print(f"   Confidence: {confidence:.0%}")
        print(f"   Logic: {reasoning}")
    
    print(f"\n" + "="*70)
    print("⚖️  VOTE WEIGHT CALCULATION")
    print("="*70)
    
    # Calculate vote weights
    council_experts = [framework.experts[expert_id] for expert_id in council_members]
    expert_confidences = {expert_id: expert_votes[expert_id]["confidence_overall"] for expert_id in council_members}
    
    vote_weights = framework.vote_weight_calculator.calculate_vote_weights(
        council_experts, expert_confidences
    )
    
    print(f"\nVote weights based on performance metrics:")
    for weight in vote_weights:
        expert_name = framework.experts[weight.expert_id].name
        print(f"   {expert_name}: {weight.normalized_weight:.1%} vote power")
        print(f"      ├─ Accuracy: {weight.accuracy_component:.3f}")
        print(f"      ├─ Recent Performance: {weight.recent_performance_component:.3f}")
        print(f"      ├─ Confidence: {weight.confidence_component:.3f}")
        print(f"      └─ Council Tenure: {weight.council_tenure_component:.3f}")
    
    print(f"\n" + "="*70)
    print("🏆 CONSENSUS BUILDING")
    print("="*70)
    
    # Build consensus for key categories
    mock_predictions = {}
    for expert_id in council_members:
        vote = expert_votes[expert_id]
        mock_prediction = type('MockPrediction', (), {
            'expert_id': expert_id,
            'winner_prediction': vote['winner_prediction'],
            'exact_score_home': vote['exact_score_home'],
            'exact_score_away': vote['exact_score_away'],
            'against_the_spread': vote['against_the_spread'],
            'confidence_overall': vote['confidence_overall']
        })()
        mock_predictions[expert_id] = mock_prediction
    
    # Winner consensus
    winner_consensus = framework.consensus_builder.build_consensus(
        mock_predictions, council_experts, 'winner_prediction'
    )
    
    # Spread consensus  
    spread_consensus = framework.consensus_builder.build_consensus(
        mock_predictions, council_experts, 'against_the_spread'
    )
    
    # Score consensus
    home_score_consensus = framework.consensus_builder.build_consensus(
        mock_predictions, council_experts, 'exact_score_home'
    )
    
    away_score_consensus = framework.consensus_builder.build_consensus(
        mock_predictions, council_experts, 'exact_score_away'
    )
    
    print(f"\n📊 WEIGHTED VOTING RESULTS:")
    
    # Winner breakdown
    print(f"\n🎯 GAME WINNER:")
    home_votes = sum(vw.normalized_weight for vw in vote_weights 
                    if expert_votes[vw.expert_id]['winner_prediction'] == 'home')
    away_votes = 1.0 - home_votes
    
    winner_team = "Chiefs" if winner_consensus.consensus_value == "home" else "Bills"
    print(f"   Consensus: {winner_team} wins")
    print(f"   Vote Distribution: Chiefs {home_votes:.1%} | Bills {away_votes:.1%}")
    print(f"   Confidence: {winner_consensus.confidence_score:.0%}")
    print(f"   Agreement: {winner_consensus.agreement_level:.0%}")
    
    # Spread breakdown
    print(f"\n📈 AGAINST THE SPREAD:")
    home_spread_votes = sum(vw.normalized_weight for vw in vote_weights 
                           if expert_votes[vw.expert_id]['against_the_spread'] == 'home')
    away_spread_votes = 1.0 - home_spread_votes
    
    spread_team = "Chiefs" if spread_consensus.consensus_value == "home" else "Bills" 
    print(f"   Consensus: {spread_team} cover the spread")
    print(f"   Vote Distribution: Chiefs {home_spread_votes:.1%} | Bills {away_spread_votes:.1%}")
    print(f"   Confidence: {spread_consensus.confidence_score:.0%}")
    
    # Score prediction
    print(f"\n🏈 FINAL SCORE PREDICTION:")
    home_score = round(home_score_consensus.consensus_value)
    away_score = round(away_score_consensus.consensus_value) 
    print(f"   Consensus Score: Chiefs {home_score}, Bills {away_score}")
    print(f"   Score Confidence: {(home_score_consensus.confidence_score + away_score_consensus.confidence_score)/2:.0%}")
    
    print(f"\n" + "="*70)
    print("📋 FINAL AI COUNCIL PREDICTION")
    print("="*70)
    
    margin = abs(home_score - away_score)
    winning_team = "Chiefs" if home_score > away_score else "Bills"
    
    print(f"\n🎖️  OFFICIAL PREDICTION:")
    print(f"   Winner: {winning_team}")
    print(f"   Final Score: Chiefs {home_score}, Bills {away_score}")
    print(f"   Margin: {winning_team} by {margin}")
    print(f"   Spread Pick: {spread_team} cover (-3.5)")
    print(f"   Total Points: {home_score + away_score} ({'Over' if home_score + away_score > 49.5 else 'Under'} 49.5)")
    
    overall_confidence = (winner_consensus.confidence_score + spread_consensus.confidence_score) / 2
    print(f"\n📊 PREDICTION METADATA:")
    print(f"   Overall Confidence: {overall_confidence:.0%}")
    print(f"   Council Agreement: {winner_consensus.agreement_level:.0%}")
    print(f"   Participating Experts: {len(council_members)}")
    print(f"   Prediction Method: Weighted Consensus")
    
    print(f"\n💡 KEY FACTORS:")
    print(f"   • Vote weights based on recent performance")  
    print(f"   • Contrarian experts identified value in underdog")
    print(f"   • Statistical models split on outcome")
    print(f"   • High confidence in spread prediction")
    
    return True

if __name__ == "__main__":
    asyncio.run(demonstrate_live_voting())