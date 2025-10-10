#!/usr/bin/env python3
"""
Expert Council Betting System - Status Check Script

Quick system status check to verify all components are worcorrectly.
"""

import asyncio
import aiohttp
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_status(message: str, status: str = "info"):
    """Print colored status message"""
    color = Colors.GREEN if status == "success" else Colors.RED if status == "error" else Colors.YELLOW if status == "warning" else Colors.BLUE
    icon = "✅" if status == "success" else "❌" if status == "error" else "⚠️" if status == "warning" else "ℹ️"
    print(f"{color}{icon} {message}{Colors.END}")

async def check_api_health(session: aiohttp.ClientSession, base_url: str) -> Dict[str, Any]:
    """Check API server health"""
    try:
        async with session.get(f"{base_url}/health", timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                return {"status": "success", "data": data}
            else:
                return {"status": "error", "message": f"HTTP {response.status}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def check_system_health(session: aiohttp.ClientSession, base_url: str) -> Dict[str, Any]:
    """Check comprehensive system health"""
    try:
        async with session.get(f"{base_url}/api/smoke-test/health", timeout=10) as response:
            if response.status == 200:
                data = await response.json()
                return {"status": "success", "data": data}
            else:
                return {"status": "error", "message": f"HTTP {response.status}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def check_recent_tests(session: aiohttp.ClientSession, base_url: str) -> Dict[str, Any]:
    """Check recent smoke test results"""
    try:
        async with session.get(f"{base_url}/api/smoke-test/history?limit=1", timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                return {"status": "success", "data": data}
            else:
                return {"status": "error", "message": f"HTTP {response.status}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def check_expert_status(session: aiohttp.ClientSession, base_url: str) -> Dict[str, Any]:
    """Check expert system status"""
    try:
        async with session.get(f"{base_url}/api/leaderboard", timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                return {"status": "success", "data": data}
            else:
                return {"status": "error", "message": f"HTTP {response.status}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def check_performance_metrics(session: aiohttp.ClientSession, base_url: str) -> Dict[str, Any]:
    """Check performance metrics"""
    try:
        async with session.get(f"{base_url}/api/smoke-test/validate/performance", timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                return {"status": "success", "data": data}
            else:
                return {"status": "error", "message": f"HTTP {response.status}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def main():
    """Main status check function"""
    print(f"{Colors.BOLD}🔍 Expert Council Betting System - Status Check{Colors.END}")
    print("=" * 55)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Configuration
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

    print(f"Checking system at: {base_url}")
    print()

    async with aiohttp.ClientSession() as session:
        # 1. Basic API Health
        print("1. API Server Health")
        api_health = await check_api_health(session, base_url)
        if api_health["status"] == "success":
            print_status("API server is responding", "success")
            if "version" in api_health["data"]:
                print(f"   Version: {api_health['data']['version']}")
        else:
            print_status(f"API server error: {api_health['message']}", "error")
            print("   Cannot continue with other checks")
            return

        print()

        # 2. System Health Check
        print("2. System Health Check")
        system_health = await check_system_health(session, base_url)
        if system_health["status"] == "success":
            health_data = system_health["data"]
            overall_healthy = health_data.get("overall_healthy", False)

            if overall_healthy:
                print_status("System is healthy", "success")
            else:
                print_status("System health issues detected", "warning")

            # Show individual health checks
            print("   Component Status:")
            print(f"   • Database: {'✅' if health_data.get('database_connectivity') else '❌'}")
            print(f"   • Expert Bankrolls: {'✅' if health_data.get('expert_bankrolls_initialized') else '❌'}")
            print(f"   • Schema Validator: {'✅' if health_data.get('schema_validator_available') else '❌'}")
            print(f"   • Performance: {'✅' if health_data.get('performance_within_targets') else '❌'}")
            print(f"   • Recent Activity: {'✅' if health_data.get('recent_predictions_available') else '❌'}")
        else:
            print_status(f"System health check failed: {system_health['message']}", "error")

        print()

        # 3. Recent Test Results
        print("3. Recent Test Results")
        recent_tests = await check_recent_tests(session, base_url)
        if recent_tests["status"] == "success":
            tests_data = recent_tests["data"]
            if tests_data.get("tests"):
                latest_test = tests_data["tests"][0]
                success = latest_test.get("success", False)
                timestamp = latest_test.get("timestamp", "Unknown")

                if success:
                    print_status(f"Latest test passed ({timestamp})", "success")
                else:
                    print_status(f"Latest test failed ({timestamp})", "warning")

                print(f"   Success Rate: {tests_data.get('success_rate', 0):.1%}")
                print(f"   Total Tests: {tests_data.get('total_count', 0)}")
            else:
                print_status("No recent tests found", "warning")
        else:
            print_status(f"Could not retrieve test history: {recent_tests['message']}", "error")

        print()

        # 4. Expert System Status
        print("4. Expert System Status")
        expert_status = await check_expert_status(session, base_url)
        if expert_status["status"] == "success":
            expert_data = expert_status["data"]
            if expert_data.get("experts"):
                active_experts = len(expert_data["experts"])
                print_status(f"{active_experts} experts active", "success")

                # Show top 3 experts
                print("   Top Experts:")
                for i, expert in enumerate(expert_data["experts"][:3]):
                    name = expert.get("expert_id", "Unknown")
                    roi = expert.get("roi", 0)
                    bankroll = expert.get("current_bankroll", 0)
                    print(f"   {i+1}. {name}: ROI {roi:.1%}, Bankroll ${bankroll:.2f}")
            else:
                print_status("No expert data available", "warning")
        else:
            print_status(f"Expert system check failed: {expert_status['message']}", "error")

        print()

        # 5. Performance Metrics
        print("5. Performance Metrics")
        performance = await check_performance_metrics(session, base_url)
        if performance["status"] == "success":
            perf_data = performance["data"]

            # Check if all targets are met
            all_targets_met = perf_data.get("overall_performance", {}).get("all_targets_met", False)

            if all_targets_met:
                print_status("All performance targets met", "success")
            else:
                print_status("Some performance targets not met", "warning")

            # Show specific metrics
            print("   Performance Metrics:")
            vector_perf = perf_data.get("vector_retrieval", {})
            e2e_perf = perf_data.get("end_to_end", {})
            projection_perf = perf_data.get("council_projection", {})

            print(f"   • Vector Retrieval: {vector_perf.get('p95_ms', 0):.1f}ms (target: ≤{vector_perf.get('target_ms', 100)}ms)")
            print(f"   • End-to-End: {e2e_perf.get('p95_seconds', 0):.1f}s (target: ≤{e2e_perf.get('target_seconds', 6)}s)")
            print(f"   • Council Projection: {projection_perf.get('p95_ms', 0):.1f}ms (target: ≤{projection_perf.get('target_ms', 150)}ms)")
        else:
            print_status(f"Performance check failed: {performance['message']}", "error")

        print()

        # Summary
        print(f"{Colors.BOLD}📊 System Status Summary{Colors.END}")
        print("-" * 30)

        # Determine overall status
        checks = [api_health, system_health, recent_tests, expert_status, performance]
        successful_checks = sum(1 for check in checks if check["status"] == "success")
        total_checks = len(checks)

        if successful_checks == total_checks:
            print_status(f"All systems operational ({successful_checks}/{total_checks} checks passed)", "success")
            print("🚀 System is ready for operation!")
        elif successful_checks >= total_checks * 0.8:
            print_status(f"System mostly operational ({successful_checks}/{total_checks} checks passed)", "warning")
            print("⚠️  Some components may need attention")
        else:
            print_status(f"System issues detected ({successful_checks}/{total_checks} checks passed)", "error")
            print("🔧 System requires maintenance")

        print()
        print("💡 Useful Commands:")
        print("   • Run smoke test: curl -X POST http://localhost:8000/api/smoke-test/run")
        print("   • View logs: docker-compose logs -f")
        print("   • Restart services: docker-compose restart")
        print("   • Check API docs: http://localhost:8000/docs")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Status check interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Status check failed: {e}")
        sys.exit(1)
