"""
Access Control Middleware
Implements subscription validation, feature-based access control, and rate limiting
"""

import os
import time
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from functools import wraps
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from .middleware import get_current_user
from ..payments.payment_service import payment_service
from ..database.connection import get_db
from ..database.models import User, Subscription, AuditLog

logger = logging.getLogger(__name__)

# Redis client for rate limiting (optional)
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', 6379)),
        db=int(os.getenv('REDIS_DB', 0)),
        decode_responses=True
    )
    redis_available = True
except Exception as e:
    logger.warning(f"Redis not available for rate limiting: {e}")
    redis_client = None
    redis_available = False

class SubscriptionTier:
    """Subscription tier definitions with access levels"""
    
    FREE = "free"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    SEASON = "season"
    
    # Tier hierarchy (higher number = higher tier)
    TIER_LEVELS = {
        FREE: 0,
        DAILY: 1,
        WEEKLY: 2,
        MONTHLY: 3,
        SEASON: 4
    }
    
    # Rate limits per tier (requests per hour)
    RATE_LIMITS = {
        FREE: 10,
        DAILY: 100,
        WEEKLY: 500,
        MONTHLY: 2000,
        SEASON: 10000
    }
    
    # Features available per tier
    TIER_FEATURES = {
        FREE: [
            'basic_predictions',
            'live_accuracy'
        ],
        DAILY: [
            'basic_predictions',
            'live_accuracy',
            'real_time_predictions',
            'basic_props'
        ],
        WEEKLY: [
            'basic_predictions',
            'live_accuracy',
            'real_time_predictions',
            'basic_props',
            'email_alerts',
            'basic_analytics'
        ],
        MONTHLY: [
            'basic_predictions',
            'live_accuracy',
            'real_time_predictions',
            'basic_props',
            'email_alerts',
            'basic_analytics',
            'advanced_analytics',
            'full_props',
            'data_export'
        ],
        SEASON: [
            'basic_predictions',
            'live_accuracy',
            'real_time_predictions',
            'basic_props',
            'email_alerts',
            'basic_analytics',
            'advanced_analytics',
            'full_props',
            'data_export',
            'playoff_predictions',
            'priority_support',
            'api_access'
        ]
    }

class AccessControlError(Exception):
    """Custom exception for access control violations"""
    def __init__(self, message: str, error_code: str = "ACCESS_DENIED"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

class RateLimiter:
    """Rate limiting implementation"""
    
    def __init__(self):
        self.in_memory_store = {}  # Fallback when Redis is not available
    
    def is_rate_limited(self, user_id: str, tier: str, endpoint: str) -> tuple[bool, Dict]:
        """Check if user is rate limited"""
        rate_limit = SubscriptionTier.RATE_LIMITS.get(tier, SubscriptionTier.RATE_LIMITS[SubscriptionTier.FREE])
        
        # Create rate limit key
        current_hour = int(time.time() // 3600)
        rate_key = f"rate_limit:{user_id}:{endpoint}:{current_hour}"
        
        if redis_available and redis_client:
            return self._check_redis_rate_limit(rate_key, rate_limit)
        else:
            return self._check_memory_rate_limit(rate_key, rate_limit)
    
    def _check_redis_rate_limit(self, rate_key: str, rate_limit: int) -> tuple[bool, Dict]:
        """Check rate limit using Redis"""
        try:
            current_count = redis_client.get(rate_key)
            if current_count is None:
                # First request in this hour
                redis_client.setex(rate_key, 3600, 1)
                return False, {"requests_made": 1, "limit": rate_limit, "reset_time": int(time.time()) + 3600}
            
            current_count = int(current_count)
            if current_count >= rate_limit:
                return True, {"requests_made": current_count, "limit": rate_limit, "reset_time": int(time.time()) + 3600}
            
            # Increment counter
            redis_client.incr(rate_key)
            return False, {"requests_made": current_count + 1, "limit": rate_limit, "reset_time": int(time.time()) + 3600}
            
        except Exception as e:
            logger.error(f"Redis rate limiting error: {e}")
            return False, {"requests_made": 0, "limit": rate_limit, "reset_time": int(time.time()) + 3600}
    
    def _check_memory_rate_limit(self, rate_key: str, rate_limit: int) -> tuple[bool, Dict]:
        """Check rate limit using in-memory storage (fallback)"""
        current_time = time.time()
        
        # Clean old entries
        self._cleanup_memory_store(current_time)
        
        if rate_key not in self.in_memory_store:
            self.in_memory_store[rate_key] = {"count": 1, "reset_time": current_time + 3600}
            return False, {"requests_made": 1, "limit": rate_limit, "reset_time": int(current_time + 3600)}
        
        entry = self.in_memory_store[rate_key]
        if current_time > entry["reset_time"]:
            # Reset counter for new hour
            entry["count"] = 1
            entry["reset_time"] = current_time + 3600
            return False, {"requests_made": 1, "limit": rate_limit, "reset_time": int(current_time + 3600)}
        
        if entry["count"] >= rate_limit:
            return True, {"requests_made": entry["count"], "limit": rate_limit, "reset_time": int(entry["reset_time"])}
        
        entry["count"] += 1
        return False, {"requests_made": entry["count"], "limit": rate_limit, "reset_time": int(entry["reset_time"])}
    
    def _cleanup_memory_store(self, current_time: float):
        """Clean up expired entries from memory store"""
        expired_keys = [key for key, value in self.in_memory_store.items() 
                       if current_time > value["reset_time"]]
        for key in expired_keys:
            del self.in_memory_store[key]

# Global rate limiter instance
rate_limiter = RateLimiter()

class SubscriptionValidator:
    """Validates user subscriptions and access rights"""
    
    @staticmethod
    async def get_user_tier(user_id: str) -> str:
        """Get user's current subscription tier"""
        try:
            subscription = await payment_service.get_user_subscription(user_id)
            
            if not subscription:
                return SubscriptionTier.FREE
            
            if subscription['status'] not in ['active', 'trial']:
                return SubscriptionTier.FREE
            
            # Check if subscription is expired
            if subscription.get('expires_at'):
                expires_at = datetime.fromisoformat(subscription['expires_at'].replace('Z', '+00:00'))
                if expires_at <= datetime.utcnow():
                    # Check for grace period (3 days)
                    grace_period_end = expires_at + timedelta(days=3)
                    if datetime.utcnow() > grace_period_end:
                        return SubscriptionTier.FREE
                    # Still in grace period, allow access but log warning
                    logger.warning(f"User {user_id} accessing during grace period")
            
            return subscription['tier']
            
        except Exception as e:
            logger.error(f"Error getting user tier for {user_id}: {e}")
            return SubscriptionTier.FREE
    
    @staticmethod
    def has_feature_access(tier: str, feature: str) -> bool:
        """Check if tier has access to specific feature"""
        tier_features = SubscriptionTier.TIER_FEATURES.get(tier, [])
        return feature in tier_features
    
    @staticmethod
    def has_tier_access(user_tier: str, required_tier: str) -> bool:
        """Check if user tier meets minimum required tier"""
        user_level = SubscriptionTier.TIER_LEVELS.get(user_tier, 0)
        required_level = SubscriptionTier.TIER_LEVELS.get(required_tier, 0)
        return user_level >= required_level

def require_subscription(min_tier: str = SubscriptionTier.DAILY):
    """Decorator to require minimum subscription tier"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs or dependencies
            current_user = kwargs.get('current_user')
            if not current_user:
                # Try to get from function signature
                for arg in args:
                    if isinstance(arg, dict) and 'user_id' in arg:
                        current_user = arg
                        break
            
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Get user's subscription tier
            user_tier = await SubscriptionValidator.get_user_tier(current_user['user_id'])
            
            # Check if user meets minimum tier requirement
            if not SubscriptionValidator.has_tier_access(user_tier, min_tier):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "Insufficient subscription level",
                        "current_tier": user_tier,
                        "required_tier": min_tier,
                        "upgrade_url": "/api/v1/subscriptions/packages"
                    }
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_feature(feature: str):
    """Decorator to require specific feature access"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Get user's subscription tier
            user_tier = await SubscriptionValidator.get_user_tier(current_user['user_id'])
            
            # Check if user has feature access
            if not SubscriptionValidator.has_feature_access(user_tier, feature):
                # Find minimum tier that has this feature
                min_tier = None
                for tier, features in SubscriptionTier.TIER_FEATURES.items():
                    if feature in features:
                        min_tier = tier
                        break
                
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": f"Feature '{feature}' not available in your subscription",
                        "current_tier": user_tier,
                        "required_tier": min_tier,
                        "feature": feature,
                        "upgrade_url": "/api/v1/subscriptions/packages"
                    }
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def rate_limit(endpoint_name: str = None):
    """Decorator to apply rate limiting based on subscription tier"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # Get user's subscription tier
            user_tier = await SubscriptionValidator.get_user_tier(current_user['user_id'])
            
            # Use function name as endpoint if not specified
            endpoint = endpoint_name or func.__name__
            
            # Check rate limit
            is_limited, rate_info = rate_limiter.is_rate_limited(
                current_user['user_id'], user_tier, endpoint
            )
            
            if is_limited:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "requests_made": rate_info["requests_made"],
                        "limit": rate_info["limit"],
                        "reset_time": rate_info["reset_time"],
                        "current_tier": user_tier,
                        "upgrade_message": "Upgrade your subscription for higher rate limits"
                    },
                    headers={
                        "X-RateLimit-Limit": str(rate_info["limit"]),
                        "X-RateLimit-Remaining": str(max(0, rate_info["limit"] - rate_info["requests_made"])),
                        "X-RateLimit-Reset": str(rate_info["reset_time"])
                    }
                )
            
            # Add rate limit headers to response
            response = await func(*args, **kwargs)
            
            # If response is a dict, add rate limit info
            if isinstance(response, dict):
                response["rate_limit"] = {
                    "requests_made": rate_info["requests_made"],
                    "limit": rate_info["limit"],
                    "reset_time": rate_info["reset_time"]
                }
            
            return response
        return wrapper
    return decorator

class AccessControlMiddleware:
    """Middleware class for access control"""
    
    def __init__(self):
        self.validator = SubscriptionValidator()
    
    async def validate_subscription_access(self, request: Request, current_user: dict) -> Dict:
        """Validate subscription access for request"""
        user_tier = await self.validator.get_user_tier(current_user['user_id'])
        
        # Log access attempt
        with get_db() as db:
            try:
                audit_log = AuditLog(
                    user_id=current_user['user_id'],
                    action='api_access',
                    resource_type='endpoint',
                    resource_id=str(request.url.path),
                    details={
                        'method': request.method,
                        'tier': user_tier,
                        'ip_address': request.client.host if request.client else None,
                        'user_agent': request.headers.get('user-agent')
                    },
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get('user-agent')
                )
                db.add(audit_log)
                db.commit()
            except Exception as e:
                logger.error(f"Failed to log access attempt: {e}")
        
        return {
            'user_tier': user_tier,
            'features': SubscriptionTier.TIER_FEATURES.get(user_tier, []),
            'rate_limit': SubscriptionTier.RATE_LIMITS.get(user_tier, 10)
        }
    
    def create_feature_dependency(self, feature: str):
        """Create a FastAPI dependency for feature access"""
        async def feature_dependency(current_user: dict = Depends(get_current_user)):
            user_tier = await self.validator.get_user_tier(current_user['user_id'])
            
            if not self.validator.has_feature_access(user_tier, feature):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": f"Feature '{feature}' not available",
                        "current_tier": user_tier,
                        "upgrade_url": "/api/v1/subscriptions/packages"
                    }
                )
            
            return current_user
        
        return feature_dependency
    
    def create_tier_dependency(self, min_tier: str):
        """Create a FastAPI dependency for tier access"""
        async def tier_dependency(current_user: dict = Depends(get_current_user)):
            user_tier = await self.validator.get_user_tier(current_user['user_id'])
            
            if not self.validator.has_tier_access(user_tier, min_tier):
                raise HTTPException(
                    status_code=403,
                    detail={
                        "error": "Insufficient subscription level",
                        "current_tier": user_tier,
                        "required_tier": min_tier,
                        "upgrade_url": "/api/v1/subscriptions/packages"
                    }
                )
            
            return current_user
        
        return tier_dependency

# Global access control middleware instance
access_control = AccessControlMiddleware()

# Convenience dependencies for common access levels
require_daily_subscription = access_control.create_tier_dependency(SubscriptionTier.DAILY)
require_weekly_subscription = access_control.create_tier_dependency(SubscriptionTier.WEEKLY)
require_monthly_subscription = access_control.create_tier_dependency(SubscriptionTier.MONTHLY)
require_season_subscription = access_control.create_tier_dependency(SubscriptionTier.SEASON)

# Convenience dependencies for common features
require_real_time_predictions = access_control.create_feature_dependency('real_time_predictions')
require_advanced_analytics = access_control.create_feature_dependency('advanced_analytics')
require_full_props = access_control.create_feature_dependency('full_props')
require_data_export = access_control.create_feature_dependency('data_export')
require_api_access = access_control.create_feature_dependency('api_access')