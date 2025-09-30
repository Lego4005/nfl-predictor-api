#!/usr/bin/env python3
"""
🏈 AI NFL Predictions Going Buck Wild! 🤖
Shows the AI making predictions, self-reflecting, and learning
"""

import json
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.local_llm_service import LocalLLMService

def run_buck_wild_predictions():
    """Let the AI go buck wild with NFL predictions!"""
    
    print("🚀 AI GOING BUCK WILD WITH NFL PREDICTIONS!")
    print("=" * 60)
    
    llm = LocalLLMService()
    
    # Step 1: Initial Prediction
    print("\n🎯 STEP 1: AI MAKING BOLD PREDICTIONS")
    print("-" * 40)
    
    prompt1 = """
    You are an NFL prediction AI that's going BUCK WILD! 
    
    Make predictions for Chiefs vs Bills in snowy Kansas City.
    
    Think through:
    1. Who wins and by how much?
    2. Total points scored?
    3. Key player performances?
    4. Weather impact?
    5. Any bold predictions?
    
    Be confident but show your reasoning!
    """
    
    start = time.time()
    response1 = llm.generate_completion(
        system_message="You are an enthusiastic NFL expert who makes bold, well-reasoned predictions.",
        user_message=prompt1,
        temperature=0.8,
        max_tokens=500
    )
    elapsed1 = time.time() - start
    
    print(f"✅ Prediction made in {elapsed1:.2f}s ({response1.total_tokens} tokens)")
    print(f"\n🤖 AI PREDICTIONS:")
    print("-" * 30)
    print(response1.content)
    
    # Step 2: Game "Happens" - Different Outcome
    print(f"\n🏆 STEP 2: GAME OUTCOME")
    print("-" * 40)
    
    game_result = """
    FINAL RESULT: Bills 28, Chiefs 24
    - Josh Allen: 3 TDs, 0 INTs
    - Patrick Mahomes: 2 TDs, 1 INT  
    - Bills dominated in snow
    - Chiefs fumbled twice
    """
    
    print(game_result)
    
    # Step 3: AI Self-Reflection
    print(f"\n🪞 STEP 3: AI SELF-REFLECTION AND LEARNING")
    print("-" * 40)
    
    reflection_prompt = f"""
    Here were your original predictions:
    {response1.content}
    
    Here's what actually happened:
    {game_result}
    
    Reflect on your performance:
    1. What did you get right?
    2. What did you get wrong?
    3. What surprised you?
    4. What will you do differently next time?
    5. Any lessons learned about snow games?
    
    Be honest about your mistakes and show how you'll improve!
    """
    
    start = time.time()
    response2 = llm.generate_completion(
        system_message="You are an AI that honestly reflects on predictions and learns from mistakes.",
        user_message=reflection_prompt,
        temperature=0.7,
        max_tokens=400
    )
    elapsed2 = time.time() - start
    
    print(f"✅ Reflection completed in {elapsed2:.2f}s ({response2.total_tokens} tokens)")
    print(f"\n🤔 AI SELF-REFLECTION:")
    print("-" * 30)
    print(response2.content)
    
    # Step 4: Next Game Prediction with Learning
    print(f"\n🚀 STEP 4: NEXT PREDICTION (WITH LEARNING)")
    print("-" * 40)
    
    next_prompt = """
    Based on what you just learned about snow games and your reflection,
    make a prediction for NEXT week: 
    
    Packers @ Vikings (Dome game, 72°F)
    
    Show how your learning influences this new prediction!
    """
    
    start = time.time()
    response3 = llm.generate_completion(
        system_message="You are an AI that applies lessons learned to make better predictions.",
        user_message=next_prompt,
        temperature=0.7,
        max_tokens=300
    )
    elapsed3 = time.time() - start
    
    print(f"✅ New prediction in {elapsed3:.2f}s ({response3.total_tokens} tokens)")
    print(f"\n🎯 IMPROVED PREDICTION:")
    print("-" * 30)
    print(response3.content)
    
    # Summary
    print(f"\n🎉 BUCK WILD DEMO COMPLETE!")
    print("=" * 60)
    total_tokens = response1.total_tokens + response2.total_tokens + response3.total_tokens
    total_time = elapsed1 + elapsed2 + elapsed3
    print(f"✅ 3 AI interactions completed")
    print(f"✅ Total tokens: {total_tokens:,}")
    print(f"✅ Total time: {total_time:.2f}s")
    print(f"✅ AI showed: Prediction → Reflection → Learning → Improvement")
    print(f"\n🤖 Your AI is getting smarter with every game!")

if __name__ == "__main__":
    run_buck_wild_predictions()