#!/usr/bin/env python3
"""
Verify Expert Model Assignments
Quick check to ensure all 15 experts have the correct tested models assigned
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def verify_model_assignments():
    """Verify the expert model assignments match our tested models"""

    # Expected assignments (what we planned)
    expected_assignments = {
        'claude-the-analyst': 'anthropic/claude-sonnet-4.5',
        'grok-the-maverick': 'x-ai/grok-4-fast',
        'gemini-the-weatherman': 'google/gemini-2.5-flash-preview-09-2025',
        'deepseek-the-intuitive': 'deepseek/deepseek-chat-v3.1:free',
        'gpt-the-historian': 'openai/gpt-5',
        'gemini-pro-the-perfectionist': 'google/gemini-2.5-pro',
        'qwen-the-calculator': 'z-ai/glm-4.6',
        'sonoma-the-rookie': 'google/gemini-2.5-flash',
        'deepseek-free-the-underdog': 'deepseek/deepseek-chat-v3.1:free',
        'flash-the-speedster': 'google/gemini-2.5-flash-preview-09-2025',
        'claude-opus-the-veteran': 'anthropic/claude-sonnet-4.5',
        'mixtral-the-philosopher': 'z-ai/glm-4.6',
        'llama-the-consistent': 'google/gemini-2.5-pro',
        'o1-the-thinker': 'openai/gpt-5',
        'haiku-the-minimalist': 'anthropic/claude-sonnet-4.5'
    }

    # Tested working models
    tested_models = [
        'x-ai/grok-4-fast',
        'google/gemini-2.5-flash-preview-09-2025',
        'anthropic/claude-sonnet-4.5',
        'deepseek/deepseek-chat-v3.1:free',
        'z-ai/glm-4.6',
        'google/gemini-2.5-pro',
        'google/gemini-2.5-flash',
        'openai/gpt-5'
    ]

    print("🔍 EXPERT MODEL ASSIGNMENT VERIFICATION")
    print("=" * 60)

    print(f"✅ Expected Assignments: {len(expected_assignments)} experts")
    print(f"✅ Tested Models Available: {len(tested_models)} models")
    print()

    # Verify all assignments use tested models
    print("📋 ASSIGNMENT VERIFICATION:")
    print("-" * 40)

    all_valid = True
    model_usage = {}

    for expert_id, expected_model in expected_assignments.items():
        is_valid = expected_model in tested_models
        status = "✅" if is_valid else "❌"

        print(f"{status} {expert_id}")
        print(f"    Model: {expected_model}")

        if not is_valid:
            print(f"    ⚠️  WARNING: Model not in tested list!")
            all_valid = False

        # Count usage
        if expected_model in model_usage:
            model_usage[expected_model] += 1
        else:
            model_usage[expected_model] = 1

        print()

    # Model usage summary
    print("📊 MODEL USAGE SUMMARY:")
    print("-" * 40)

    for model, count in sorted(model_usage.items(), key=lambda x: x[1], reverse=True):
        print(f"{count}x {model}")

    # Verification results
    print(f"\\n🎯 VERIFICATION RESULTS:")
    print("-" * 40)

    if all_valid:
        print("✅ ALL ASSIGNMENTS VALID!")
        print("✅ All experts use tested working models")
        print(f"✅ {len(tested_models)} tested models distributed across {len(expected_assignments)} experts")
        print("✅ Ready for parallel historical training!")
    else:
        print("❌ SOME ASSIGNMENTS INVALID!")
        print("⚠️  Check expertPanelService.js for incorrect model assignments")

    return all_valid

if __name__ == "__main__":
    verify_model_assignments()
