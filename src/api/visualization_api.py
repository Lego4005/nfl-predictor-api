"""
Visualization API Service

Flask API that serves prediction visualization data to frontend dashboards.
Provides endpoints for:

- Expert performance dashboards
- Game analysis and comparisons
- Accuracy analytics and trends
- Real-time prediction tracking
- Interactive chart data

Integrates with prediction_visualization_service to provide rich visual data
for the expert prediction verification system.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import json
import os
import sys

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import aiohttp

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))
sys.path.append(os.path.join(project_root, 'src', 'services'))

from services.prediction_visualization_service import PredictionVisualizationService
from services.enhanced_data_storage import EnhancedDataStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__,
           template_folder=os.path.join(project_root, 'src', 'templates'),
           static_folder=os.path.join(project_root, 'src', 'static'))
CORS(app)

# Global services (will be initialized on startup)
storage = None
viz_service = None

# Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost/nfl_predictor')

async def initialize_services():
    """Initialize database and visualization services"""
    global storage, viz_service

    try:
        # Initialize storage
        storage = EnhancedDataStorage(DATABASE_URL)
        await storage.initialize()

        # Initialize visualization service
        viz_service = PredictionVisualizationService(storage)

        logger.info("Visualization API services initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        return False

def run_async(coro):
    """Helper to run async functions in Flask"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# Dashboard Routes
@app.route('/')
def dashboard():
    """Serve main dashboard page"""
    return render_template('dashboard.html')

@app.route('/game/<game_id>')
def game_analysis(game_id):
    """Serve game analysis page"""
    return render_template('game_analysis.html', game_id=game_id)

@app.route('/expert/<expert_id>')
def expert_profile(expert_id):
    """Serve expert profile page"""
    return render_template('expert_profile.html', expert_id=expert_id)

# API Endpoints
@app.route('/api/dashboard')
def api_dashboard():
    """Get comprehensive dashboard data"""
    try:
        days_back = request.args.get('days', 30, type=int)
        dashboard_data = run_async(viz_service.get_expert_performance_dashboard_data(days_back))

        return jsonify({
            "success": True,
            "data": dashboard_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Error in dashboard API: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 500

@app.route('/api/expert-leaderboard')
def api_expert_leaderboard():
    """Get expert leaderboard data"""
    try:
        days_back = request.args.get('days', 30, type=int)
        dashboard_data = run_async(viz_service.get_expert_performance_dashboard_data(days_back))

        return jsonify({
            "success": True,
            "data": {
                "leaderboard": dashboard_data.get("expert_leaderboard", []),
                "summary": dashboard_data.get("summary", {})
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Error in expert leaderboard API: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/accuracy-heatmap')
def api_accuracy_heatmap():
    """Get accuracy heatmap data"""
    try:
        days_back = request.args.get('days', 30, type=int)
        dashboard_data = run_async(viz_service.get_expert_performance_dashboard_data(days_back))

        return jsonify({
            "success": True,
            "data": dashboard_data.get("accuracy_heatmap", {}),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Error in accuracy heatmap API: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/confidence-calibration')
def api_confidence_calibration():
    """Get confidence calibration data"""
    try:
        days_back = request.args.get('days', 30, type=int)
        dashboard_data = run_async(viz_service.get_expert_performance_dashboard_data(days_back))

        return jsonify({
            "success": True,
            "data": dashboard_data.get("confidence_calibration", {}),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Error in confidence calibration API: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/category-performance')
def api_category_performance():
    """Get category performance data"""
    try:
        days_back = request.args.get('days', 30, type=int)
        dashboard_data = run_async(viz_service.get_expert_performance_dashboard_data(days_back))

        return jsonify({
            "success": True,
            "data": dashboard_data.get("category_performance", []),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Error in category performance API: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/recent-games')
def api_recent_games():
    """Get recent games summary"""
    try:
        days_back = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 10, type=int)

        dashboard_data = run_async(viz_service.get_expert_performance_dashboard_data(days_back))
        recent_games = dashboard_data.get("recent_games", [])[:limit]

        return jsonify({
            "success": True,
            "data": recent_games,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Error in recent games API: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/game/<game_id>')
def api_game_analysis(game_id):
    """Get detailed game analysis"""
    try:
        game_data = run_async(viz_service.get_game_analysis_data(game_id))

        return jsonify({
            "success": True,
            "data": game_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Error in game analysis API: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/game-comparison')
def api_game_comparison():
    """Get prediction vs reality comparison for multiple games"""
    try:
        # Get game IDs from query parameters
        game_ids_param = request.args.get('games', '')
        if game_ids_param:
            game_ids = game_ids_param.split(',')
        else:
            # Get recent games if no specific games specified
            days_back = request.args.get('days', 7, type=int)
            dashboard_data = run_async(viz_service.get_expert_performance_dashboard_data(days_back))
            recent_games = dashboard_data.get("recent_games", [])[:5]  # Last 5 games
            game_ids = [game["game_id"] for game in recent_games]

        comparison_data = run_async(viz_service.get_prediction_comparison_data(game_ids))

        return jsonify({
            "success": True,
            "data": comparison_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Error in game comparison API: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/expert/<expert_id>')
def api_expert_profile(expert_id):
    """Get detailed expert profile data"""
    try:
        days_back = request.args.get('days', 30, type=int)

        # Get dashboard data to extract expert info
        dashboard_data = run_async(viz_service.get_expert_performance_dashboard_data(days_back))

        # Find specific expert in leaderboard
        expert_data = None
        for expert in dashboard_data.get("expert_leaderboard", []):
            if expert["expert_id"] == expert_id:
                expert_data = expert
                break

        if not expert_data:
            return jsonify({
                "success": False,
                "error": "Expert not found"
            }), 404

        # Get additional expert-specific data
        expert_profile = {
            "expert_info": expert_data,
            "category_breakdown": {},  # Would get from heatmap data
            "recent_predictions": [],  # Would get recent predictions
            "performance_trends": {}   # Would get historical trends
        }

        return jsonify({
            "success": True,
            "data": expert_profile,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Error in expert profile API: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/live-games')
def api_live_games():
    """Get live games with current predictions"""
    try:
        # This would integrate with live game data
        # For now, return placeholder
        live_games = {
            "active_games": [],
            "upcoming_games": [],
            "live_predictions": {}
        }

        return jsonify({
            "success": True,
            "data": live_games,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Error in live games API: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/performance-trends')
def api_performance_trends():
    """Get performance trends over time"""
    try:
        days_back = request.args.get('days', 90, type=int)
        expert_id = request.args.get('expert_id')

        dashboard_data = run_async(viz_service.get_expert_performance_dashboard_data(days_back))
        trends_data = dashboard_data.get("performance_trends", {})

        # Filter by expert if specified
        if expert_id:
            # Would filter trends for specific expert
            pass

        return jsonify({
            "success": True,
            "data": trends_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Error in performance trends API: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/system-status')
def api_system_status():
    """Get system health and status"""
    try:
        status = {
            "api_status": "healthy",
            "database_connected": storage.pool is not None and not storage.pool._closed if storage else False,
            "services_initialized": viz_service is not None,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0"
        }

        return jsonify({
            "success": True,
            "data": status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    except Exception as e:
        logger.error(f"Error in system status API: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 500

# Static file serving for development
@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory(app.static_folder, filename)

def create_app(config=None):
    """Application factory"""
    if config:
        app.config.update(config)

    return app

def run_server(host='localhost', port=5000, debug=True):
    """Run the visualization server"""
    logger.info(f"Starting NFL Prediction Visualization API on {host}:{port}")

    # Initialize services
    init_success = run_async(initialize_services())

    if not init_success:
        logger.error("Failed to initialize services - server cannot start")
        return False

    logger.info("✅ Services initialized successfully")
    logger.info("📊 Visualization API ready for requests")
    logger.info(f"🌐 Dashboard available at: http://{host}:{port}")

    try:
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        # Cleanup
        if storage:
            run_async(storage.close())
        logger.info("Services cleaned up")

    return True

# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='NFL Prediction Visualization API')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    print("🏈 NFL Expert Prediction Visualization API")
    print("==========================================")
    print(f"Starting server on {args.host}:{args.port}")
    print()

    run_server(host=args.host, port=args.port, debug=args.debug)