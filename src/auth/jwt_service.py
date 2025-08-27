"""
JWT Token Service
Handles JWT token generation, validation, and refresh token rotation
"""

import os
import jwt
import uuid
import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class TokenType(Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"

@dataclass
class TokenPair:
    """Access and refresh token pair"""
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime
    token_type: str = "Bearer"

@dataclass
class TokenPayload:
    """JWT token payload data"""
    user_id: str
    email: str
    token_type: TokenType
    subscription_tier: Optional[str] = None
    subscription_expires: Optional[datetime] = None
    permissions: Optional[list] = None
    issued_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    jti: Optional[str] = None  # JWT ID for blacklisting

class JWTService:
    """JWT token management service"""
    
    def __init__(self):
        self.secret_key = self._get_secret_key()
        self.algorithm = os.getenv('JWT_ALGORITHM', 'HS256')
        self.access_token_expire_minutes = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', '15'))
        self.refresh_token_expire_days = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRE_DAYS', '7'))
        
        # Token blacklist (in production, use Redis)
        self._blacklisted_tokens = set()
    
    def _get_secret_key(self) -> str:
        """Get JWT secret key from environment"""
        secret_key = os.getenv('JWT_SECRET_KEY')
        if not secret_key:
            logger.warning("JWT_SECRET_KEY not set, using default (INSECURE!)")
            return "your_super_secret_jwt_key_change_this_in_production"
        return secret_key
    
    def generate_token_pair(self, user_data: Dict) -> TokenPair:
        """Generate access and refresh token pair"""
        now = datetime.now(timezone.utc)
        access_expires = now + timedelta(minutes=self.access_token_expire_minutes)
        refresh_expires = now + timedelta(days=self.refresh_token_expire_days)
        
        # Generate unique JTI for each token
        access_jti = str(uuid.uuid4())
        refresh_jti = str(uuid.uuid4())
        
        # Access token payload
        access_payload = {
            'user_id': user_data['user_id'],
            'email': user_data['email'],
            'token_type': TokenType.ACCESS.value,
            'subscription_tier': user_data.get('subscription_tier'),
            'subscription_expires': user_data.get('subscription_expires').isoformat() if user_data.get('subscription_expires') else None,
            'permissions': user_data.get('permissions', []),
            'iat': now.timestamp(),
            'exp': access_expires.timestamp(),
            'jti': access_jti
        }
        
        # Refresh token payload (minimal data)
        refresh_payload = {
            'user_id': user_data['user_id'],
            'email': user_data['email'],
            'token_type': TokenType.REFRESH.value,
            'iat': now.timestamp(),
            'exp': refresh_expires.timestamp(),
            'jti': refresh_jti
        }
        
        # Generate tokens
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)
        
        logger.info(f"Generated token pair for user {user_data['email']}")
        
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            access_expires_at=access_expires,
            refresh_expires_at=refresh_expires
        )
    
    def verify_token(self, token: str, expected_type: TokenType = TokenType.ACCESS) -> Optional[TokenPayload]:
        """Verify and decode JWT token"""
        try:
            # Decode token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check if token is blacklisted
            jti = payload.get('jti')
            if jti and jti in self._blacklisted_tokens:
                logger.warning(f"Attempted use of blacklisted token: {jti}")
                return None
            
            # Verify token type
            token_type = TokenType(payload.get('token_type'))
            if token_type != expected_type:
                logger.warning(f"Token type mismatch: expected {expected_type.value}, got {token_type.value}")
                return None
            
            # Convert timestamps back to datetime
            issued_at = datetime.fromtimestamp(payload['iat'], tz=timezone.utc) if payload.get('iat') else None
            expires_at = datetime.fromtimestamp(payload['exp'], tz=timezone.utc) if payload.get('exp') else None
            
            # Parse subscription expiration
            subscription_expires = None
            if payload.get('subscription_expires'):
                try:
                    subscription_expires = datetime.fromisoformat(payload['subscription_expires'])
                except ValueError:
                    logger.warning("Invalid subscription_expires format in token")
            
            return TokenPayload(
                user_id=payload['user_id'],
                email=payload['email'],
                token_type=token_type,
                subscription_tier=payload.get('subscription_tier'),
                subscription_expires=subscription_expires,
                permissions=payload.get('permissions', []),
                issued_at=issued_at,
                expires_at=expires_at,
                jti=jti
            )
            
        except jwt.ExpiredSignatureError:
            logger.info("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    def refresh_token_pair(self, refresh_token: str) -> Optional[TokenPair]:
        """Generate new token pair using refresh token"""
        # Verify refresh token
        payload = self.verify_token(refresh_token, TokenType.REFRESH)
        if not payload:
            return None
        
        # Blacklist the old refresh token
        if payload.jti:
            self._blacklisted_tokens.add(payload.jti)
        
        # Generate new token pair
        user_data = {
            'user_id': payload.user_id,
            'email': payload.email,
            'subscription_tier': payload.subscription_tier,
            'subscription_expires': payload.subscription_expires,
            'permissions': payload.permissions or []
        }
        
        logger.info(f"Refreshed token pair for user {payload.email}")
        return self.generate_token_pair(user_data)
    
    def blacklist_token(self, token: str) -> bool:
        """Add token to blacklist (for logout)"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": False})
            jti = payload.get('jti')
            if jti:
                self._blacklisted_tokens.add(jti)
                logger.info(f"Blacklisted token: {jti}")
                return True
        except Exception as e:
            logger.error(f"Error blacklisting token: {e}")
        return False
    
    def generate_special_token(self, user_data: Dict, token_type: TokenType, 
                             expire_hours: int = 24) -> str:
        """Generate special purpose tokens (email verification, password reset)"""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=expire_hours)
        
        payload = {
            'user_id': user_data['user_id'],
            'email': user_data['email'],
            'token_type': token_type.value,
            'iat': now.timestamp(),
            'exp': expires.timestamp(),
            'jti': str(uuid.uuid4())
        }
        
        # Add additional data for specific token types
        if token_type == TokenType.EMAIL_VERIFICATION:
            payload['action'] = 'verify_email'
        elif token_type == TokenType.PASSWORD_RESET:
            payload['action'] = 'reset_password'
            # Add password hash for extra security
            payload['password_hash'] = hashlib.sha256(
                user_data.get('password_hash', '').encode()
            ).hexdigest()[:16]
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        logger.info(f"Generated {token_type.value} token for user {user_data['email']}")
        return token
    
    def verify_special_token(self, token: str, token_type: TokenType) -> Optional[TokenPayload]:
        """Verify special purpose tokens"""
        return self.verify_token(token, token_type)
    
    def get_token_info(self, token: str) -> Optional[Dict]:
        """Get token information without verification (for debugging)"""
        try:
            # Decode without verification
            payload = jwt.decode(token, options={"verify_signature": False, "verify_exp": False})
            
            # Convert timestamps to readable format
            if payload.get('iat'):
                payload['issued_at_readable'] = datetime.fromtimestamp(
                    payload['iat'], tz=timezone.utc
                ).isoformat()
            
            if payload.get('exp'):
                payload['expires_at_readable'] = datetime.fromtimestamp(
                    payload['exp'], tz=timezone.utc
                ).isoformat()
                payload['is_expired'] = datetime.now(timezone.utc) > datetime.fromtimestamp(
                    payload['exp'], tz=timezone.utc
                )
            
            return payload
            
        except Exception as e:
            logger.error(f"Error getting token info: {e}")
            return None
    
    def cleanup_blacklist(self):
        """Clean up expired tokens from blacklist"""
        # In production, this would be handled by Redis TTL
        # For now, we'll keep it simple
        logger.info(f"Blacklist contains {len(self._blacklisted_tokens)} tokens")
    
    def is_token_blacklisted(self, token: str) -> bool:
        """Check if token is blacklisted"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": False})
            jti = payload.get('jti')
            return jti in self._blacklisted_tokens if jti else False
        except Exception:
            return True  # Treat invalid tokens as blacklisted
    
    def get_token_expiry(self, token: str) -> Optional[datetime]:
        """Get token expiration time"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm], options={"verify_exp": False})
            exp = payload.get('exp')
            return datetime.fromtimestamp(exp, tz=timezone.utc) if exp else None
        except Exception:
            return None
    
    def validate_token_structure(self, token: str) -> Tuple[bool, str]:
        """Validate token structure and return detailed feedback"""
        try:
            # Check if it's a valid JWT structure
            parts = token.split('.')
            if len(parts) != 3:
                return False, "Invalid JWT structure: must have 3 parts separated by dots"
            
            # Try to decode header
            try:
                header = jwt.get_unverified_header(token)
                if header.get('alg') != self.algorithm:
                    return False, f"Invalid algorithm: expected {self.algorithm}, got {header.get('alg')}"
            except Exception as e:
                return False, f"Invalid JWT header: {e}"
            
            # Try to decode payload (without verification)
            try:
                payload = jwt.decode(token, options={"verify_signature": False, "verify_exp": False})
                
                # Check required fields
                required_fields = ['user_id', 'email', 'token_type', 'iat', 'exp', 'jti']
                missing_fields = [field for field in required_fields if field not in payload]
                if missing_fields:
                    return False, f"Missing required fields: {missing_fields}"
                
                # Check token type
                token_type = payload.get('token_type')
                if token_type not in [t.value for t in TokenType]:
                    return False, f"Invalid token type: {token_type}"
                
                return True, "Token structure is valid"
                
            except Exception as e:
                return False, f"Invalid JWT payload: {e}"
                
        except Exception as e:
            return False, f"Token validation error: {e}"

class TokenAnalytics:
    """Token usage analytics and monitoring"""
    
    def __init__(self):
        self._token_stats = {
            'generated': 0,
            'verified': 0,
            'refreshed': 0,
            'blacklisted': 0,
            'failed_verifications': 0
        }
        self._user_token_counts = {}
    
    def record_token_generation(self, user_id: str):
        """Record token generation"""
        self._token_stats['generated'] += 1
        self._user_token_counts[user_id] = self._user_token_counts.get(user_id, 0) + 1
    
    def record_token_verification(self, success: bool):
        """Record token verification attempt"""
        if success:
            self._token_stats['verified'] += 1
        else:
            self._token_stats['failed_verifications'] += 1
    
    def record_token_refresh(self):
        """Record token refresh"""
        self._token_stats['refreshed'] += 1
    
    def record_token_blacklist(self):
        """Record token blacklisting"""
        self._token_stats['blacklisted'] += 1
    
    def get_stats(self) -> Dict:
        """Get token statistics"""
        return {
            'token_stats': self._token_stats.copy(),
            'active_users': len(self._user_token_counts),
            'total_user_tokens': sum(self._user_token_counts.values()),
            'avg_tokens_per_user': sum(self._user_token_counts.values()) / len(self._user_token_counts) if self._user_token_counts else 0
        }

class TokenManager:
    """High-level token management with analytics"""
    
    def __init__(self):
        self.jwt_service = JWTService()
        self.analytics = TokenAnalytics()
    
    def create_user_session(self, user_data: Dict) -> Dict:
        """Create complete user session with tokens"""
        token_pair = self.jwt_service.generate_token_pair(user_data)
        self.analytics.record_token_generation(user_data['user_id'])
        
        return {
            'access_token': token_pair.access_token,
            'refresh_token': token_pair.refresh_token,
            'token_type': token_pair.token_type,
            'expires_in': self.jwt_service.access_token_expire_minutes * 60,  # seconds
            'access_expires_at': token_pair.access_expires_at.isoformat(),
            'refresh_expires_at': token_pair.refresh_expires_at.isoformat(),
            'user': {
                'user_id': user_data['user_id'],
                'email': user_data['email'],
                'subscription_tier': user_data.get('subscription_tier'),
                'permissions': user_data.get('permissions', [])
            }
        }
    
    def refresh_session(self, refresh_token: str) -> Optional[Dict]:
        """Refresh user session"""
        token_pair = self.jwt_service.refresh_token_pair(refresh_token)
        if not token_pair:
            self.analytics.record_token_verification(False)
            return None
        
        # Get user info from new access token
        payload = self.jwt_service.verify_token(token_pair.access_token)
        if not payload:
            self.analytics.record_token_verification(False)
            return None
        
        self.analytics.record_token_refresh()
        self.analytics.record_token_verification(True)
        
        return {
            'access_token': token_pair.access_token,
            'refresh_token': token_pair.refresh_token,
            'token_type': token_pair.token_type,
            'expires_in': self.jwt_service.access_token_expire_minutes * 60,
            'access_expires_at': token_pair.access_expires_at.isoformat(),
            'refresh_expires_at': token_pair.refresh_expires_at.isoformat(),
            'user': {
                'user_id': payload.user_id,
                'email': payload.email,
                'subscription_tier': payload.subscription_tier,
                'permissions': payload.permissions or []
            }
        }
    
    def logout_user(self, access_token: str, refresh_token: str) -> bool:
        """Logout user by blacklisting tokens"""
        access_blacklisted = self.jwt_service.blacklist_token(access_token)
        refresh_blacklisted = self.jwt_service.blacklist_token(refresh_token)
        
        if access_blacklisted and refresh_blacklisted:
            self.analytics.record_token_blacklist()
        
        return access_blacklisted and refresh_blacklisted
    
    def get_current_user(self, access_token: str) -> Optional[Dict]:
        """Get current user from access token"""
        payload = self.jwt_service.verify_token(access_token)
        
        if not payload:
            self.analytics.record_token_verification(False)
            return None
        
        self.analytics.record_token_verification(True)
        
        return {
            'user_id': payload.user_id,
            'email': payload.email,
            'subscription_tier': payload.subscription_tier,
            'subscription_expires': payload.subscription_expires.isoformat() if payload.subscription_expires else None,
            'permissions': payload.permissions or [],
            'token_expires_at': payload.expires_at.isoformat() if payload.expires_at else None
        }
    
    def validate_and_analyze_token(self, token: str) -> Dict:
        """Comprehensive token validation and analysis"""
        result = {
            'is_valid': False,
            'is_blacklisted': False,
            'is_expired': False,
            'structure_valid': False,
            'token_info': None,
            'validation_message': '',
            'expires_in_seconds': 0
        }
        
        # Check structure
        structure_valid, structure_message = self.jwt_service.validate_token_structure(token)
        result['structure_valid'] = structure_valid
        result['validation_message'] = structure_message
        
        if not structure_valid:
            return result
        
        # Check if blacklisted
        result['is_blacklisted'] = self.jwt_service.is_token_blacklisted(token)
        if result['is_blacklisted']:
            result['validation_message'] = 'Token is blacklisted'
            return result
        
        # Get token info
        token_info = self.jwt_service.get_token_info(token)
        result['token_info'] = token_info
        
        if token_info:
            result['is_expired'] = token_info.get('is_expired', True)
            
            # Calculate time until expiration
            if token_info.get('exp'):
                exp_time = datetime.fromtimestamp(token_info['exp'], tz=timezone.utc)
                now = datetime.now(timezone.utc)
                if exp_time > now:
                    result['expires_in_seconds'] = int((exp_time - now).total_seconds())
        
        # Try to verify token
        payload = self.jwt_service.verify_token(token)
        result['is_valid'] = payload is not None
        
        if result['is_valid']:
            result['validation_message'] = 'Token is valid'
        elif result['is_expired']:
            result['validation_message'] = 'Token has expired'
        else:
            result['validation_message'] = 'Token verification failed'
        
        return result
    
    def get_analytics(self) -> Dict:
        """Get token analytics"""
        return self.analytics.get_stats()

# Global instances
jwt_service = JWTService()
token_manager = TokenManager()