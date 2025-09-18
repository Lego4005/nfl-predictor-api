"""
Rate Limiting and Security Middleware for NFL Predictions API
Implements rate limiting, API key validation, and security measures
"""

import time
import hashlib
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
import redis
from functools import wraps

logger = logging.getLogger(__name__)

class RateLimiter:
    """In-memory rate limiter with Redis fallback for production"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.local_cache: Dict[str, deque] = defaultdict(lambda: deque())
        self.api_keys: Dict[str, Dict] = {
            # Mock API keys - in production, these would be in database
            "dev_key_001": {
                "name": "Development Key",
                "tier": "basic",
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
                "created": datetime.now()
            },
            "premium_key_001": {
                "name": "Premium Key",
                "tier": "premium",
                "requests_per_minute": 300,
                "requests_per_hour": 10000,
                "created": datetime.now()
            },
            "enterprise_key_001": {
                "name": "Enterprise Key",
                "tier": "enterprise",
                "requests_per_minute": 1000,
                "requests_per_hour": 50000,
                "created": datetime.now()
            }
        }

    def _get_client_id(self, request: Request, api_key: Optional[str] = None) -> str:
        """Generate unique client identifier"""
        if api_key:
            return f"api_key:{api_key}"

        # Fallback to IP-based identification
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")

        # Create hash for privacy
        client_hash = hashlib.md5(f"{client_ip}:{user_agent}".encode()).hexdigest()
        return f"ip:{client_hash}"

    def _get_rate_limits(self, api_key: Optional[str] = None) -> Tuple[int, int]:
        """Get rate limits based on API key tier"""
        if api_key and api_key in self.api_keys:
            key_data = self.api_keys[api_key]
            return key_data["requests_per_minute"], key_data["requests_per_hour"]

        # Default rate limits for unauthenticated requests
        return 30, 500  # 30 per minute, 500 per hour

    def _check_rate_limit_redis(self, client_id: str, limit: int, window: int) -> bool:
        """Check rate limit using Redis"""
        if not self.redis_client:
            return self._check_rate_limit_local(client_id, limit, window)

        try:
            pipe = self.redis_client.pipeline()
            now = time.time()
            key = f"rate_limit:{client_id}:{window}"

            # Remove old entries
            pipe.zremrangebyscore(key, 0, now - window)
            # Add current request
            pipe.zadd(key, {str(now): now})
            # Count current requests
            pipe.zcard(key)
            # Set expiry
            pipe.expire(key, window)

            results = pipe.execute()
            current_requests = results[2]

            return current_requests <= limit

        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Fallback to local cache
            return self._check_rate_limit_local(client_id, limit, window)

    def _check_rate_limit_local(self, client_id: str, limit: int, window: int) -> bool:
        """Check rate limit using local memory"""
        now = time.time()
        client_requests = self.local_cache[client_id]

        # Remove old requests outside the window
        while client_requests and client_requests[0] < now - window:
            client_requests.popleft()

        # Check if under limit
        if len(client_requests) >= limit:
            return False

        # Add current request
        client_requests.append(now)
        return True

    def check_rate_limit(self, request: Request, api_key: Optional[str] = None) -> bool:
        """Check if request is within rate limits"""
        client_id = self._get_client_id(request, api_key)
        per_minute_limit, per_hour_limit = self._get_rate_limits(api_key)

        # Check both minute and hour limits
        minute_ok = self._check_rate_limit_redis(client_id, per_minute_limit, 60)
        hour_ok = self._check_rate_limit_redis(client_id, per_hour_limit, 3600)

        return minute_ok and hour_ok

    def get_rate_limit_info(self, request: Request, api_key: Optional[str] = None) -> Dict:
        """Get current rate limit status"""
        client_id = self._get_client_id(request, api_key)
        per_minute_limit, per_hour_limit = self._get_rate_limits(api_key)

        # Count current requests
        now = time.time()
        client_requests = self.local_cache[client_id]

        # Count requests in last minute
        minute_requests = sum(1 for req_time in client_requests if req_time > now - 60)
        # Count requests in last hour
        hour_requests = sum(1 for req_time in client_requests if req_time > now - 3600)

        return {
            "requests_per_minute": {
                "limit": per_minute_limit,
                "remaining": max(0, per_minute_limit - minute_requests),
                "used": minute_requests
            },
            "requests_per_hour": {
                "limit": per_hour_limit,
                "remaining": max(0, per_hour_limit - hour_requests),
                "used": hour_requests
            },
            "tier": self.api_keys.get(api_key, {}).get("tier", "anonymous") if api_key else "anonymous"
        }

    def validate_api_key(self, api_key: str) -> bool:
        """Validate API key"""
        return api_key in self.api_keys

# Global rate limiter instance
rate_limiter = RateLimiter()

# Security schemes
security = HTTPBearer(auto_error=False)

async def get_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """Extract API key from Authorization header"""
    if credentials:
        api_key = credentials.credentials
        if rate_limiter.validate_api_key(api_key):
            return api_key
        else:
            raise HTTPException(status_code=401, detail="Invalid API key")
    return None

async def rate_limit_dependency(request: Request, api_key: Optional[str] = Depends(get_api_key)):
    """Rate limiting dependency for FastAPI endpoints"""
    if not rate_limiter.check_rate_limit(request, api_key):
        rate_info = rate_limiter.get_rate_limit_info(request, api_key)

        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit-Minute": str(rate_info["requests_per_minute"]["limit"]),
                "X-RateLimit-Remaining-Minute": str(rate_info["requests_per_minute"]["remaining"]),
                "X-RateLimit-Limit-Hour": str(rate_info["requests_per_hour"]["limit"]),
                "X-RateLimit-Remaining-Hour": str(rate_info["requests_per_hour"]["remaining"]),
                "Retry-After": "60"
            }
        )

    return api_key

def add_rate_limit_headers(request: Request, api_key: Optional[str] = None) -> Dict[str, str]:
    """Add rate limit headers to response"""
    rate_info = rate_limiter.get_rate_limit_info(request, api_key)

    return {
        "X-RateLimit-Limit-Minute": str(rate_info["requests_per_minute"]["limit"]),
        "X-RateLimit-Remaining-Minute": str(rate_info["requests_per_minute"]["remaining"]),
        "X-RateLimit-Limit-Hour": str(rate_info["requests_per_hour"]["limit"]),
        "X-RateLimit-Remaining-Hour": str(rate_info["requests_per_hour"]["remaining"]),
        "X-RateLimit-Tier": rate_info["tier"]
    }

# Additional security functions
def validate_prediction_request(game_id: str) -> bool:
    """Validate prediction request parameters"""
    # Check game_id format
    if not game_id or len(game_id) < 3:
        return False

    # Add additional validation as needed
    return True

def log_api_usage(request: Request, api_key: Optional[str], endpoint: str, response_time: float):
    """Log API usage for monitoring and analytics"""
    client_id = rate_limiter._get_client_id(request, api_key)

    usage_data = {
        "timestamp": datetime.now().isoformat(),
        "client_id": client_id,
        "api_key": api_key if api_key else "anonymous",
        "endpoint": endpoint,
        "method": request.method,
        "response_time": response_time,
        "user_agent": request.headers.get("user-agent", ""),
        "ip": request.client.host
    }

    # In production, this would write to a logging service or database
    logger.info(f"API Usage: {usage_data}")

# Security middleware
class SecurityMiddleware:
    """Security middleware for additional protection"""

    def __init__(self):
        self.blocked_ips: set = set()
        self.suspicious_activity: Dict[str, int] = defaultdict(int)

    def is_blocked_ip(self, ip: str) -> bool:
        """Check if IP is blocked"""
        return ip in self.blocked_ips

    def block_ip(self, ip: str, reason: str = "Suspicious activity"):
        """Block an IP address"""
        self.blocked_ips.add(ip)
        logger.warning(f"Blocked IP {ip}: {reason}")

    def check_request_patterns(self, request: Request) -> bool:
        """Check for suspicious request patterns"""
        client_ip = request.client.host

        # Check if IP is already blocked
        if self.is_blocked_ip(client_ip):
            return False

        # Check for rapid requests from same IP
        self.suspicious_activity[client_ip] += 1

        # Block if too many requests in short time
        if self.suspicious_activity[client_ip] > 100:  # Configurable threshold
            self.block_ip(client_ip, "Too many requests")
            return False

        return True

    def validate_request_headers(self, request: Request) -> bool:
        """Validate request headers for security"""
        # Check for required headers
        if request.method == "POST" and not request.headers.get("content-type"):
            return False

        # Check for suspicious headers
        user_agent = request.headers.get("user-agent", "")
        if len(user_agent) > 500 or "bot" in user_agent.lower():
            # Log but don't block - might be legitimate
            logger.info(f"Suspicious user agent: {user_agent}")

        return True

# Global security middleware instance
security_middleware = SecurityMiddleware()

# Performance optimization functions
class ResponseCache:
    """Simple response cache for prediction data"""

    def __init__(self, default_ttl: int = 30):
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """Get cached response"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.default_ttl:
                return data
            else:
                del self.cache[key]
        return None

    def set(self, key: str, data: Any, ttl: Optional[int] = None):
        """Cache response"""
        ttl = ttl or self.default_ttl
        self.cache[key] = (data, time.time())

    def clear_expired(self):
        """Clear expired cache entries"""
        now = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self.cache.items()
            if now - timestamp >= self.default_ttl
        ]
        for key in expired_keys:
            del self.cache[key]

# Global cache instance
response_cache = ResponseCache()

# Decorator for caching responses
def cache_response(ttl: int = 30):
    """Decorator to cache API responses"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Try to get from cache
            cached_result = response_cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            response_cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator