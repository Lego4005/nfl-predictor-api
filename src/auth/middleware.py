"""
Authentication Middleware for FastAPI
Handles JWT token validation and user authentication
"""

import logging
from typing import Optional, Dict, List
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import wraps

from .jwt_service import token_manager, TokenType

logger = logging.getLogger(__name__)

# Security scheme for FastAPI
security = HTTPBearer()

class AuthenticationError(Exception):
    """Authentication related errors"""
    pass

class AuthorizationError(Exception):
    """Authorization related errors"""
    pass

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """FastAPI dependency to get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = token_manager.get_current_user(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user

def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict]:
    """FastAPI dependency to get current user (optional)"""
    if not credentials:
        return None
    
    try:
        return token_manager.get_current_user(credentials.credentials)
    except Exception:
        return None

def require_subscription(required_tiers: List[str] = None):
    """Decorator to require active subscription"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current user from kwargs (injected by FastAPI)
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Check if user has active subscription
            subscription_tier = current_user.get('subscription_tier')
            if not subscription_tier:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Active subscription required",
                    headers={"X-Upgrade-Required": "true"}
                )
            
            # Check specific tier requirements
            if required_tiers and subscription_tier not in required_tiers:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Subscription tier '{subscription_tier}' insufficient. Required: {required_tiers}",
                    headers={"X-Upgrade-Required": "true"}
                )
            
            # Check subscription expiration
            subscription_expires = current_user.get('subscription_expires')
            if subscription_expires:
                from datetime import datetime
                try:
                    expires_at = datetime.fromisoformat(subscription_expires)
                    if datetime.now() > expires_at:
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail="Subscription has expired",
                            headers={"X-Subscription-Expired": "true"}
                        )
                except ValueError:
                    logger.warning(f"Invalid subscription expiration format: {subscription_expires}")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_permissions(required_permissions: List[str]):
    """Decorator to require specific permissions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_permissions = current_user.get('permissions', [])
            
            # Check if user has all required permissions
            missing_permissions = [perm for perm in required_permissions if perm not in user_permissions]
            if missing_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing permissions: {missing_permissions}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_admin(func):
    """Decorator to require admin permissions"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user = kwargs.get('current_user')
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        user_permissions = current_user.get('permissions', [])
        admin_permissions = ['admin', 'super_admin', 'system_admin']
        
        if not any(perm in user_permissions for perm in admin_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        return await func(*args, **kwargs)
    return wrapper

class SubscriptionTierChecker:
    """Helper class to check subscription tiers and features"""
    
    TIER_HIERARCHY = {
        'free_trial': 0,
        'daily': 1,
        'weekly': 2,
        'monthly': 3,
        'season': 4,
        'friends_family': 4,  # Same level as season
        'beta_tester': 5,     # Highest level
        'enterprise': 6      # Enterprise level
    }
    
    TIER_FEATURES = {
        'free_trial': ['sample_predictions', 'basic_accuracy'],
        'daily': ['real_time_predictions', 'basic_props', 'live_accuracy'],
        'weekly': ['real_time_predictions', 'basic_props', 'live_accuracy', 'email_alerts'],
        'monthly': ['all_weekly', 'advanced_analytics', 'full_props', 'priority_email_alerts'],
        'season': ['all_monthly', 'playoff_predictions', 'data_export', 'priority_support'],
        'friends_family': ['all_season', 'special_access'],
        'beta_tester': ['all_season', 'beta_features', 'feedback_tools'],
        'enterprise': ['everything']
    }
    
    @classmethod
    def has_tier_access(cls, user_tier: str, required_tier: str) -> bool:
        """Check if user tier has access to required tier features"""
        user_level = cls.TIER_HIERARCHY.get(user_tier, -1)
        required_level = cls.TIER_HIERARCHY.get(required_tier, 999)
        return user_level >= required_level
    
    @classmethod
    def has_feature_access(cls, user_tier: str, feature: str) -> bool:
        """Check if user tier has access to specific feature"""
        tier_features = cls.TIER_FEATURES.get(user_tier, [])
        
        # Check direct feature access
        if feature in tier_features:
            return True
        
        # Check hierarchical access (e.g., 'all_weekly' includes weekly features)
        if 'everything' in tier_features:
            return True
        
        if 'all_season' in tier_features and feature in cls.TIER_FEATURES.get('season', []):
            return True
        
        if 'all_monthly' in tier_features and feature in cls.TIER_FEATURES.get('monthly', []):
            return True
        
        if 'all_weekly' in tier_features and feature in cls.TIER_FEATURES.get('weekly', []):
            return True
        
        return False
    
    @classmethod
    def get_upgrade_suggestion(cls, current_tier: str, required_feature: str) -> Optional[str]:
        """Get suggested upgrade tier for accessing a feature"""
        for tier, features in cls.TIER_FEATURES.items():
            if cls.has_feature_access(tier, required_feature):
                if cls.TIER_HIERARCHY.get(tier, 0) > cls.TIER_HIERARCHY.get(current_tier, 0):
                    return tier
        return None

def require_feature_access(feature: str):
    """Decorator to require access to specific feature"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_tier = current_user.get('subscription_tier')
            if not user_tier:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Subscription required",
                    headers={"X-Upgrade-Required": "true"}
                )
            
            if not SubscriptionTierChecker.has_feature_access(user_tier, feature):
                suggested_tier = SubscriptionTierChecker.get_upgrade_suggestion(user_tier, feature)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Feature '{feature}' requires higher subscription tier",
                    headers={
                        "X-Upgrade-Required": "true",
                        "X-Suggested-Tier": suggested_tier or "unknown"
                    }
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Rate limiting decorator (basic implementation)
def rate_limit(requests_per_minute: int = 60):
    """Basic rate limiting decorator"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # In production, implement proper rate limiting with Redis
            # For now, just log the request
            current_user = kwargs.get('current_user')
            user_id = current_user.get('user_id') if current_user else 'anonymous'
            logger.info(f"Rate limit check for user {user_id}: {requests_per_minute} req/min")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator