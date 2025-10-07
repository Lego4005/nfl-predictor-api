#!/usr/bin/env python3
"""
Update Expert Model Assignments with Latest OpenRouter Models
"""
import os
import sys
import json

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def create_expert_model_mapping():
    """Create mapping of experts to new models based on personalities"""

    # Available top-tier models from user
    available_models = [
        'x-ai/grok-4-fast',
        'google/gemini-2.5-flash-preview-09-2025',
        'anthropic/claude-sonnet-4.5',
        'deepseek/deepseek-chat-v3.1:free',
        'z-ai/glm-4.6',
        'google/gemini-2.5-pro',
        'google/gemini-2.5-flash',
        'openai/gpt-5'
    ]

    # Expert assignments based on personality fit
    expert_model_assignments = {
        # COUNCIL TIER - Top 5 Active Experts
        'claude-the-analyst': {
            'current': 'anthropic/claude-4-sonnet-20250522',
            'suggested': 'anthropic/claude-sonnet-4.5',
            'reason': 'Upgrade to latest Claude Sonnet for advanced analytics'
        },
        'grok-the-maverick': {
            'current': 'x-ai/grok-code-fast-1',
            'suggested': 'x-ai/grok-4-fast',
            'reason': 'Upgrade to Grok 4 Fast for contrarian analysis'
        },
        'gemini-the-weatherman': {
            'current': 'google/gemini-2.5-flash',
            'suggested': 'google/gemini-2.5-flash-preview-09-2025',
            'reason': 'Latest Gemini preview for environmental analysis'
        },
        'deepseek-the-intuitive': {
            'current': 'deepseek/deepseek-chat-v3-0324',
            'suggested': 'deepseek/deepseek-chat-v3.1:free',
            'reason': 'Upgrade to v3.1 for better intuitive reasoning'
        },
        'gpt-the-historian': {
            'current': 'openai/gpt-4.1-mini-2025-04-14',
            'suggested': 'openai/gpt-5',
            'reason': 'GPT-5 for superior historical pattern recognition'
        },

        # CHALLENGER TIER - Fighting for Council Spots
        'gemini-pro-the-perfectionist': {
            'current': 'google/gemini-2.5-pro',
            'suggested': 'google/gemini-2.5-pro',
            'reason': 'Keep current - already using latest Pro model'
        },
        'qwen-the-calculator': {
            'current': 'qwen/qwen3-30b-a3b-04-28',
            'suggested': 'z-ai/glm-4.6',
            'reason': 'Switch to GLM-4.6 for mathematical precision'
        },
        'sonoma-the-rookie': {
            'current': 'openrouter/sonoma-sky-alpha',
            'suggested': 'google/gemini-2.5-flash',
            'reason': 'Upgrade rookie to proven Gemini Flash'
        },
        'deepseek-free-the-underdog': {
            'current': 'deepseek/deepseek-chat-v3.1:free',
            'suggested': 'deepseek/deepseek-chat-v3.1:free',
            'reason': 'Keep current - already using latest free version'
        },
        'flash-the-speedster': {
            'current': 'google/gemini-2.0-flash-001',
            'suggested': 'google/gemini-2.5-flash-preview-09-2025',
            'reason': 'Upgrade to latest flash preview for speed'
        },

        # DEVELOPMENT LEAGUE - Could use upgrades but lower priority
        'claude-opus-the-veteran': {
            'current': 'anthropic/claude-3-opus-20240229',
            'suggested': 'anthropic/claude-sonnet-4.5',
            'reason': 'Major upgrade from Opus 3 to Sonnet 4.5'
        },
        'mixtral-the-philosopher': {
            'current': 'mistralai/mixtral-8x7b-instruct',
            'suggested': 'z-ai/glm-4.6',
            'reason': 'Upgrade to GLM for philosophical reasoning'
        },
        'llama-the-consistent': {
            'current': 'meta-llama/llama-3.3-70b-instruct',
            'suggested': 'google/gemini-2.5-pro',
            'reason': 'Upgrade to Gemini Pro for consistency'
        },
        'o1-the-thinker': {
            'current': 'openai/o1-mini',
            'suggested': 'openai/gpt-5',
            'reason': 'Upgrade to GPT-5 for deep thinking'
        },
        'haiku-the-minimalist': {
            'current': 'anthropic/claude-3.5-haiku-20241022',
            'suggested': 'anthropic/claude-sonnet-4.5',
            'reason': 'Upgrade to Sonnet while keeping minimalist approach'
        }
    }

    return expert_model_assignments, available_models

def print_assignment_summary():
    """Print summary of proposed model assignments"""

    assignments, available_models = create_expert_model_mapping()

    print("🎯 PROPOSED EXPERT MODEL ASSIGNMENTS")
    print("=" * 60)
    print(f"Available Models: {len(available_models)}")
    print(f"Experts to Update: {len(assignments)}")
    print()

    # Group by tier
    council_tier = ['claude-the-analyst', 'grok-the-maverick', 'gemini-the-weatherman',
                   'deepseek-the-intuitive', 'gpt-the-historian']

    challenger_tier = ['gemini-pro-the-perfectionist', 'qwen-the-calculator', 'sonoma-the-rookie',
                      'deepseek-free-the-underdog', 'flash-the-speedster']

    dev_tier = ['claude-opus-the-veteran', 'mixtral-the-philosopher', 'llama-the-consistent',
               'o1-the-thinker', 'haiku-the-minimalist']

    for tier_name, tier_experts in [
        ("👑 COUNCIL TIER", council_tier),
        ("🥊 CHALLENGER TIER", challenger_tier),
        ("🌱 DEVELOPMENT TIER", dev_tier)
    ]:
        print(f"\\n{tier_name}")
        print("-" * 40)

        for expert_id in tier_experts:
            if expert_id in assignments:
                assignment = assignments[expert_id]
                current = assignment['current']
                suggested = assignment['suggested']
                reason = assignment['reason']

                # Check if it's an upgrade
                is_upgrade = current != suggested
                status = "🔄 UPGRADE" if is_upgrade else "✅ KEEP"

                print(f"{status} {expert_id}")
                print(f"    Current:  {current}")
                print(f"    Suggested: {suggested}")
                print(f"    Reason: {reason}")
                print()

    # Model usage summary
    print("\\n📊 MODEL USAGE SUMMARY")
    print("-" * 40)

    model_usage = {}
    for assignment in assignments.values():
        model = assignment['suggested']
        if model in model_usage:
            model_usage[model] += 1
        else:
            model_usage[model] = 1

    for model, count in sorted(model_usage.items(), key=lambda x: x[1], reverse=True):
        print(f"{count}x {model}")

    print(f"\\n💡 Ready to update? This will modify expertPanelService.js")
    print(f"   Models can be reused - multiple experts can share the same model")

def generate_javascript_update():
    """Generate JavaScript code to update the expert models"""

    assignments, _ = create_expert_model_mapping()

    print("\\n🔧 JAVASCRIPT UPDATE CODE")
    print("=" * 60)
    print("// Update the model assignments in src/services/expertPanelService.js")
    print("// Replace the existing expert configurations with these:")
    print()

    for expert_id, assignment in assignments.items():
        suggested_model = assignment['suggested']
        print(f"// {expert_id}")
        print(f"model: '{suggested_model}',")
        print()

if __name__ == "__main__":
    print_assignment_summary()

    print("\\n" + "=" * 60)
    user_input = input("Generate JavaScript update code? (y/n): ")

    if user_input.lower() in ['y', 'yes']:
        generate_javascript_update()
