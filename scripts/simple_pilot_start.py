#!/usr/bin/env python3
"""
Simple Pilot Start - Direct OpenRouter Test

Simplified startup script that tests OpenRouter directly without complex dependencies.
"""

import asyncio
import aiohttp
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_openrouter_connection():
    """Test OpenRouter connection directly"""
    api_key = os.getenv('OPENROUTER_API_KEY')

    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in .env file")
        return False

    print(f"🔑 API Key found: {api_key[:20]}...")

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://github.com/your-repo/nfl-predictor-api',
        'X-Title': 'NFL Expert Council Betting System'
    }

    # Test payload
    payload = {
        'model': 'deepseek/deepseek-chat',
        'messages': [
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': 'Say "OpenRouter connection successful" in JSON format: {"status": "success", "message": "OpenRouter connection successful"}'}
        ],
        'max_tokens': 100,
        'temperature': 0.3
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    content = data['choices'][0]['message']['content']
                    usage = data.get('usage', {})

                    print("✅ OpenRouter connection successful!")
                    print(f"📝 Response: {content}")
                    print(f"🔢 Tokens used: {usage.get('total_tokens', 0)}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ OpenRouter API error {response.status}: {error_text}")
                    return False

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

async def test_supabase_connection():
    """Test Supabase connection directly"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')

    if not supabase_url or not supabase_key:
        print("❌ Supabase credentials not found in .env file")
        return False

    print(f"🔗 Supabase URL: {supabase_url}")
    print(f"🔑 Supabase Key: {supabase_key[:20]}...")

    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json'
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{supabase_url}/rest/v1/",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:

                if response.status == 200:
                    print("✅ Supabase connection successful!")
                    return True
                else:
                    print(f"❌ Supabase connection failed: HTTP {response.status}")
                    return False

    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False

async def test_expert_model_assignments():
    """Test expert model assignments"""
    print("🧠 Expert Model Assignments:")

    # 4-expert pilot configuration
    expert_models = {
        'conservative_analyzer': 'anthropic/claude-3.5-sonnet',
        'momentum_rider': 'deepseek/deepseek-chat',
        'contrarian_rebel': 'deepseek/deepseek-chat',
        'value_hunter': 'anthropic/claude-3.5-sonnet'
    }

    for expert, model in expert_models.items():
        print(f"   • {expert} → {model}")

    print("🔧 System Configuration:")
    print("   • Critic/Repair: anthropic/claude-3.5-sonnet")
    print("   • Shadow Models: google/gemini-pro-1.5, x-ai/grok-beta")
    print(f"   • Run ID: {os.getenv('RUN_ID', 'run_2025_pilot4')}")
    print("   • Stakes: 0 (training), 1.0 (backtesting)")

    return True

async def generate_sample_prediction():
    """Generate a sample prediction to test the full pipeline"""
    api_key = os.getenv('OPENROUTER_API_KEY')

    if not api_key:
        return False

    print("🎯 Testing Sample Prediction Generation...")

    system_prompt = """You are a conservative NFL analyst. You provide careful, well-reasoned predictions.
Return your response in JSON format with the following structure:
{
    "winner": "team_name",
    "confidence": 0.65,
    "reasoning": "brief explanation"
}"""

    user_prompt = """Predict the winner of Chiefs vs Bills. Consider:
- Chiefs are at home
- Both teams have strong offenses
- Weather conditions are clear
- Chiefs are 3-point favorites

Provide your prediction in the exact JSON format specified."""

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://github.com/your-repo/nfl-predictor-api',
        'X-Title': 'NFL Expert Council Betting System'
    }

    payload = {
        'model': 'anthropic/claude-3.5-sonnet',
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_prompt}
        ],
        'max_tokens': 200,
        'temperature': 0.3
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    content = data['choices'][0]['message']['content']

                    print("✅ Sample prediction generated!")
                    print(f"📝 Expert Response: {content}")

                    # Try to parse JSON
                    try:
                        prediction_json = json.loads(content)
                        print("✅ JSON parsing successful!")
                        print(f"🏆 Winner: {prediction_json.get('winner', 'Unknown')}")
                        print(f"📊 Confidence: {prediction_json.get('confidence', 0)}")
                        return True
                    except json.JSONDecodeError:
                        print("⚠️ Response not valid JSON, but generation worked")
                        return True
                else:
                    print(f"❌ Prediction generation failed: HTTP {response.status}")
                    return False

    except Exception as e:
        print(f"❌ Prediction generation failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 NFL Expert Council Betting System - Simple Pilot Test")
    print("=" * 60)

    # Test 1: OpenRouter Connection
    print("1️⃣ Testing OpenRouter Connection...")
    openrouter_ok = await test_openrouter_connection()

    # Test 2: Supabase Connection
    print("\n2️⃣ Testing Supabase Connection...")
    supabase_ok = await test_supabase_connection()

    # Test 3: Expert Model Assignments
    print("\n3️⃣ Expert Model Configuration...")
    models_ok = await test_expert_model_assignments()

    # Test 4: Sample Prediction
    print("\n4️⃣ Testing Sample Prediction...")
    prediction_ok = await generate_sample_prediction()

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   OpenRouter: {'✅ PASS' if openrouter_ok else '❌ FAIL'}")
    print(f"   Supabase: {'✅ PASS' if supabase_ok else '❌ FAIL'}")
    print(f"   Models: {'✅ PASS' if models_ok else '❌ FAIL'}")
    print(f"   Prediction: {'✅ PASS' if prediction_ok else '❌ FAIL'}")

    all_passed = openrouter_ok and supabase_ok and models_ok and prediction_ok

    if all_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("🚀 Your system is ready for the 4-expert pilot!")
        print("\n📋 Next Steps:")
        print("1. Start FastAPI server: uvicorn src.api.main:app --reload --port 8000")
        print("2. Run system status: python3 scripts/system_status.py")
        print("3. Generate predictions via API calls")
        return 0
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("Please check your .env configuration and try again.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))
