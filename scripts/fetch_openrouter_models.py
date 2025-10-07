#!/usr/bin/env python3
"""
Fetch available models from OpenRouter API
"""
import os
import sys
import requests
import json
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()

def fetch_openrouter_models():
    """Fetch available models from OpenRouter"""

    api_key = os.getenv('VITE_OPENROUTER_API_KEY')
    if not api_key:
        print("❌ VITE_OPENROUTER_API_KEY not found in environment")
        return None

    url = "https://openrouter.ai/api/v1/models"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://github.com/nfl-predictor',
        'X-Title': 'NFL Predictor'
    }

    try:
        print("🔄 Fetching models from OpenRouter...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()
        models = data.get('data', [])

        print(f"✅ Found {len(models)} models")

        # Filter for top models (by context length, capabilities, etc.)
        top_models = []

        for model in models:
            model_id = model.get('id', '')
            name = model.get('name', '')
            context_length = model.get('context_length', 0)
            pricing = model.get('pricing', {})

            # Focus on high-quality models with good context length
            if context_length >= 32000:  # At least 32k context
                top_models.append({
                    'id': model_id,
                    'name': name,
                    'context_length': context_length,
                    'prompt_cost': pricing.get('prompt', '0'),
                    'completion_cost': pricing.get('completion', '0')
                })

        # Sort by context length (descending)
        top_models.sort(key=lambda x: x['context_length'], reverse=True)

        print(f"\\n🎯 Top Models (32k+ context):")
        print("=" * 80)

        for i, model in enumerate(top_models[:20], 1):  # Top 20
            print(f"{i:2d}. {model['id']}")
            print(f"    Name: {model['name']}")
            print(f"    Context: {model['context_length']:,} tokens")
            print(f"    Cost: ${model['prompt_cost']} / ${model['completion_cost']}")
            print()

        return top_models

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

if __name__ == "__main__":
    models = fetch_openrouter_models()

    if models:
        print(f"\\n📊 Summary:")
        print(f"   Total models with 32k+ context: {len(models)}")
        print(f"   Highest context length: {models[0]['context_length']:,} tokens")
        print(f"\\n💡 Use these model IDs for expert assignments!")
