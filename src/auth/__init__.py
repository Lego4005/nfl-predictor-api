"""
Authentication package
JWT token management and middleware for FastAPI
"""

from .jwt_service import (
    JWTService, TokenManager, TokenType, TokenPair, TokenPayload,
    jwt_service, token_manager
)
from .middleware import (
    get_current_user, get_optional_user, require_subscription,
    require_permissions, require_admin, require_feature_access,
    rate_limit, SubscriptionTierChecker, security
)
from .password_service import (
    PasswordService, PasswordStrength, PasswordValidation, PasswordResetToken,
    password_service
)
from .session_service import (
    SessionService, SessionInfo, DeviceInfo, SessionStatus,
    session_service
)

__all__ = [
    # JWT Service
    'JWTService',
    'TokenManager', 
    'TokenType',
    'TokenPair',
    'TokenPayload',
    'jwt_service',
    'token_manager',
    
    # Middleware
    'get_current_user',
    'get_optional_user',
    'require_subscription',
    'require_permissions',
    'require_admin',
    'require_feature_access',
    'rate_limit',
    'SubscriptionTierChecker',
    'security',
    
    # Password Service
    'PasswordService',
    'PasswordStrength',
    'PasswordValidation',
    'PasswordResetToken',
    'password_service'
]