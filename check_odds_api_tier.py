#!/usr/bin/env python3
"""
Check The Odds API tier and usage limits
"""

import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

try:
    import httpx
except ImportError:
    print("❌ httpx not installed. Please run: pip install httpx")
    exit(1)


async def check_api_tier():
    """Check your Odds API tier and usage"""
    print("🔍 Checking The Odds API Tier & Usage")
    print("=" * 50)
    
    # Check for API key
    api_key = os.getenv("ODDS_API_KEY") or os.getenv("VITE_ODDS_API_KEY")
    
    if not api_key:
        print("❌ No API key found!")
        print("   Please set ODDS_API_KEY or VITE_ODDS_API_KEY environment variable")
        return
    
    print(f"✅ API key found: {api_key[:12]}...{api_key[-6:]}")
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Make a simple request to check headers
            url = "https://api.the-odds-api.com/v4/sports"
            params = {"apiKey": api_key}
            
            response = await client.get(url, params=params)
            
            if response.status_code == 200:
                print(f"✅ API connection successful!")
                print(f"   Status: {response.status_code}")
                
                # Extract usage information from headers
                headers = dict(response.headers)
                
                print(f"\n📊 API Usage Information:")
                print(f"   Response headers:")
                
                usage_headers = {
                    "x-requests-remaining": "Requests Remaining",
                    "x-requests-used": "Requests Used",
                    "x-ratelimit-requests-remaining": "Rate Limit Remaining", 
                    "x-ratelimit-requests-used": "Rate Limit Used",
                    "x-ratelimit-requests-limit": "Rate Limit Total",
                    "x-ratelimit-period": "Rate Limit Period",
                    "x-plan": "API Plan",
                    "x-tier": "API Tier"
                }
                
                for header, description in usage_headers.items():
                    value = headers.get(header, "Not provided")
                    print(f"     {description}: {value}")
                
                # Calculate percentage if we have the data
                remaining = headers.get("x-requests-remaining")
                used = headers.get("x-requests-used") 
                limit = headers.get("x-ratelimit-requests-limit")
                
                if remaining and remaining.isdigit():
                    remaining_int = int(remaining)
                    print(f"\n💡 Analysis:")
                    print(f"   Requests remaining: {remaining_int}")
                    
                    if used and used.isdigit():
                        used_int = int(used)
                        total = remaining_int + used_int
                        percentage_used = (used_int / total) * 100
                        print(f"   Requests used: {used_int}")
                        print(f"   Total allocation: {total}")
                        print(f"   Usage: {percentage_used:.1f}%")
                        
                        # Determine tier based on total
                        if total <= 500:
                            tier = "Free Tier (500 requests/month)"
                        elif total <= 5000:
                            tier = "Basic Paid Plan"
                        elif total <= 10000:
                            tier = "Standard Paid Plan"
                        else:
                            tier = "Premium Paid Plan"
                        
                        print(f"   Likely tier: {tier}")
                    else:
                        # Fall back to documentation assumption
                        if remaining_int <= 500:
                            print(f"   Likely tier: Free (500 requests/month)")
                        else:
                            print(f"   Likely tier: Paid plan")
                
                # Now test the NFL odds endpoint to see current data
                print(f"\n🏈 Testing NFL odds endpoint...")
                odds_url = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"
                odds_params = {
                    "apiKey": api_key,
                    "regions": "us",
                    "markets": "h2h",  # Just moneylines to minimize data
                    "oddsFormat": "american"
                }
                
                odds_response = await client.get(odds_url, params=odds_params)
                
                if odds_response.status_code == 200:
                    odds_data = odds_response.json()
                    print(f"✅ NFL odds endpoint working!")
                    print(f"   Games available: {len(odds_data)}")
                    
                    # Check updated usage
                    new_remaining = odds_response.headers.get("x-requests-remaining")
                    if new_remaining and remaining:
                        used_requests = int(remaining) - int(new_remaining)
                        print(f"   Requests used for this test: {used_requests}")
                        print(f"   Remaining after test: {new_remaining}")
                else:
                    print(f"❌ NFL odds endpoint failed: {odds_response.status_code}")
                    print(f"   Response: {odds_response.text}")
                
                return True
                
            elif response.status_code == 401:
                print(f"❌ Authentication failed: Invalid API key")
                return False
            elif response.status_code == 429:
                print(f"❌ Rate limit exceeded")
                remaining = response.headers.get("x-requests-remaining", "Unknown")
                print(f"   Requests remaining: {remaining}")
                return False
            else:
                print(f"❌ API error: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error checking API: {e}")
        return False


async def main():
    """Main function"""
    print("🎯 The Odds API Tier Checker")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    await check_api_tier()
    
    print(f"\n💡 About The Odds API Tiers:")
    print(f"   Free Tier: 500 requests/month")
    print(f"   Basic Paid: Usually 5,000+ requests/month")
    print(f"   Higher tiers: 10,000+ requests/month")
    print(f"   Check your dashboard at: https://the-odds-api.com/")


if __name__ == "__main__":
    asyncio.run(main())