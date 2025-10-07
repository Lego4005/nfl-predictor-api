#!/usr/bin/env python3
"""
Apply the tested and confirmed working models to experts
Based on the models that were actually tested and working
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def get_tested_working_models():
    """Models that were confirmed working in tests"""

    # Based on your message showing successful responses
    tested_working_models = [
        'x-ai/grok-4-fast',
        'google/gemini-2.5-flash-preview-09-2025',
        'anthropic/claude-sonnet-4.5',
        'deepseek/deepseek-chat-v3.1:free',
        'z-ai/glm-4.6',
        'google/gemini-2.5-pro',
        'google/gemini-2.5-flash',
        'openai/gpt-5'  # This one was specifically mentioned as working
    ]

    return tested_working_models

def create_expert_assignments_from_tested():
    """Assign tested working models to experts"""

    working_models = get_tested_working_models()

    # Strategic assignments using ONLY tested models
    assignments = {
        # COUNCIL TIER - Top 5 (get the best models)
        'claude-the-analyst': 'anthropic/claude-sonnet-4.5',
        'grok-the-maverick': 'x-ai/grok-4-fast',
        'gemini-the-weatherman': 'google/gemini-2.5-flash-preview-09-2025',
        'deepseek-the-intuitive': 'deepseek/deepseek-chat-v3.1:free',
        'gpt-the-historian': 'openai/gpt-5',

        # CHALLENGER TIER
        'gemini-pro-the-perfectionist': 'google/gemini-2.5-pro',
        'qwen-the-calculator': 'z-ai/glm-4.6',
        'sonoma-the-rookie': 'google/gemini-2.5-flash',
        'deepseek-free-the-underdog': 'deepseek/deepseek-chat-v3.1:free',
        'flash-the-speedster': 'google/gemini-2.5-flash-preview-09-2025',

        # DEVELOPMENT TIER (can reuse top models)
        'claude-opus-the-veteran': 'anthropic/claude-sonnet-4.5',
        'mixtral-the-philosopher': 'z-ai/glm-4.6',
        'llama-the-consistent': 'google/gemini-2.5-pro',
        'o1-the-thinker': 'openai/gpt-5',
        'haiku-the-minimalist': 'anthropic/claude-sonnet-4.5'
    }

    return assignments

def print_tested_assignments():
    """Print the assignments using only tested models"""

    working_models = get_tested_working_models()
    assignments = create_expert_assignments_from_tested()

    print("🧪 TESTED & CONFIRMED WORKING MODELS")
    print("=" * 60)
    print("✅ These models were tested and confirmed working:")
    for i, model in enumerate(working_models, 1):
        print(f"  {i}. {model}")

    print(f"\\n🎯 EXPERT ASSIGNMENTS (TESTED MODELS ONLY)")
    print("=" * 60)

    # Group by tier
    council = ['claude-the-analyst', 'grok-the-maverick', 'gemini-the-weatherman',
               'deepseek-the-intuitive', 'gpt-the-historian']
    challenger = ['gemini-pro-the-perfectionist', 'qwen-the-calculator', 'sonoma-the-rookie',
                  'deepseek-free-the-underdog', 'flash-the-speedster']
    dev = ['claude-opus-the-veteran', 'mixtral-the-philosopher', 'llama-the-consistent',
           'o1-the-thinker', 'haiku-the-minimalist']

    for tier_name, experts in [("👑 COUNCIL", council), ("🥊 CHALLENGER", challenger), ("🌱 DEV", dev)]:
        print(f"\\n{tier_name} TIER:")
        print("-" * 30)
        for expert in experts:
            model = assignments[expert]
            print(f"  {expert} → {model}")

    # Model usage count
    print(f"\\n📊 MODEL USAGE:")
    print("-" * 30)
    usage = {}
    for model in assignments.values():
        usage[model] = usage.get(model, 0) + 1

    for model, count in sorted(usage.items(), key=lambda x: x[1], reverse=True):
        print(f"  {count}x {model}")

    print(f"\\n✅ All {len(working_models)} tested models are being used!")
    print(f"📝 Ready to update expertPanelService.js with these assignments")

def generate_js_code():
    """Generate the JavaScript code for updating expertPanelService.js"""

    assignments = create_expert_assignments_from_tested()

    print(f"\\n🔧 JAVASCRIPT UPDATE CODE")
    print("=" * 60)
    print("// Copy these model assignments into expertPanelService.js")
    print("// Find each expert and update their 'model' field:")
    print()

    for expert_id, model in assignments.items():
        print(f"// {expert_id}")
        print(f"model: '{model}',")
        print()

if __name__ == "__main__":
    print_tested_assignments()

    print("\\n" + "=" * 60)
    user_input = input("Generate JavaScript update code? (y/n): ")

    if user_input.lower() in ['y', 'yes']:
        generate_js_code()
