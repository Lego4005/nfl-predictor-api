"""
API Key Rotation and Management System.
Provides secure key rotation, validation, and fallback mechanisms.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import secrets


logger = logging.getLogger(__name__)


class KeyStatus(Enum):
    """Status of API keys"""
    ACTIVE = "active"
    ROTATING = "rotating"
    DEPRECATED = "deprecated"
    REVOKED = "revoked"


@dataclass
class APIKeyInfo:
    """Information about an API key"""
    key_id: str
    key_hash: str  # Hashed version for security
    status: KeyStatus
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    usage_count: int
    rate_limit_remaining: Optional[int]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "key_id": self.key_id,
            "key_hash": self.key_hash,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "usage_count": self.usage_count,
            "rate_limit_remaining": self.rate_limit_remaining
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'APIKeyInfo':
        """Create from dictionary"""
        return cls(
            key_id=data["key_id"],
            key_hash=data["key_hash"],
            status=KeyStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data["expires_at"] else None,
            last_used=datetime.fromisoformat(data["last_used"]) if data["last_used"] else None,
            usage_count=data["usage_count"],
            rate_limit_remaining=data.get("rate_limit_remaining")
        )


class KeyRotationManager:
    """
    Manages API key rotation, validation, and fallback mechanisms.
    Provides secure storage and rotation of API keys for production use.
    """
    
    def __init__(self, storage_path: str = "config/keys.json"):
        self.storage_path = storage_path
        self.keys: Dict[str, Dict[str, APIKeyInfo]] = {}  # service -> key_id -> key_info
        self._load_keys()
    
    def _hash_key(self, api_key: str) -> str:
        """Create secure hash of API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def _generate_key_id(self) -> str:
        """Generate unique key ID"""
        return secrets.token_urlsafe(16)
    
    def _load_keys(self):
        """Load keys from storage file"""
        if not os.path.exists(self.storage_path):
            self.keys = {}
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            
            self.keys = {}
            for service, service_keys in data.items():
                self.keys[service] = {}
                for key_id, key_data in service_keys.items():
                    self.keys[service][key_id] = APIKeyInfo.from_dict(key_data)
                    
        except Exception as e:
            logger.error(f"Failed to load keys from {self.storage_path}: {e}")
            self.keys = {}
    
    def _save_keys(self):
        """Save keys to storage file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            
            # Convert to serializable format
            data = {}
            for service, service_keys in self.keys.items():
                data[service] = {}
                for key_id, key_info in service_keys.items():
                    data[service][key_id] = key_info.to_dict()
            
            # Write to file with secure permissions
            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Set secure file permissions (owner read/write only)
            os.chmod(self.storage_path, 0o600)
            
        except Exception as e:
            logger.error(f"Failed to save keys to {self.storage_path}: {e}")
    
    def add_key(
        self,
        service: str,
        api_key: str,
        expires_at: Optional[datetime] = None
    ) -> str:
        """
        Add new API key for service.
        Returns the key ID for reference.
        """
        key_id = self._generate_key_id()
        key_hash = self._hash_key(api_key)
        
        key_info = APIKeyInfo(
            key_id=key_id,
            key_hash=key_hash,
            status=KeyStatus.ACTIVE,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            last_used=None,
            usage_count=0,
            rate_limit_remaining=None
        )
        
        if service not in self.keys:
            self.keys[service] = {}
        
        self.keys[service][key_id] = key_info
        self._save_keys()
        
        logger.info(f"Added new API key for {service} with ID {key_id}")
        return key_id
    
    def get_active_key(self, service: str) -> Optional[str]:
        """
        Get the currently active API key for service.
        Returns the actual key from environment variables.
        """
        if service not in self.keys:
            return None
        
        # Find active key with latest creation date
        active_keys = [
            (key_id, key_info) for key_id, key_info in self.keys[service].items()
            if key_info.status == KeyStatus.ACTIVE
        ]
        
        if not active_keys:
            return None
        
        # Sort by creation date (newest first)
        active_keys.sort(key=lambda x: x[1].created_at, reverse=True)
        key_id, key_info = active_keys[0]
        
        # Get actual key from environment
        env_var_map = {
            "odds_api": "ODDS_API_KEY",
            "sportsdata_io": "SPORTSDATA_IO_KEY",
            "rapid_api": "RAPID_API_KEY"
        }
        
        env_var = env_var_map.get(service)
        if not env_var:
            return None
        
        api_key = os.getenv(env_var)
        if not api_key:
            return None
        
        # Verify key hash matches
        if self._hash_key(api_key) != key_info.key_hash:
            logger.warning(f"Key hash mismatch for {service}, key may have been changed")
            return None
        
        # Update usage tracking
        key_info.last_used = datetime.utcnow()
        key_info.usage_count += 1
        self._save_keys()
        
        return api_key
    
    def rotate_key(
        self,
        service: str,
        new_api_key: str,
        grace_period_hours: int = 24
    ) -> Tuple[str, bool]:
        """
        Rotate API key for service with grace period.
        Returns (new_key_id, success).
        """
        try:
            # Mark current active keys as rotating
            if service in self.keys:
                for key_info in self.keys[service].values():
                    if key_info.status == KeyStatus.ACTIVE:
                        key_info.status = KeyStatus.ROTATING
                        # Set expiration for grace period
                        key_info.expires_at = datetime.utcnow() + timedelta(hours=grace_period_hours)
            
            # Add new key
            expires_at = datetime.utcnow() + timedelta(days=365)  # 1 year expiration
            new_key_id = self.add_key(service, new_api_key, expires_at)
            
            logger.info(f"Rotated API key for {service}, new key ID: {new_key_id}")
            return new_key_id, True
            
        except Exception as e:
            logger.error(f"Failed to rotate key for {service}: {e}")
            return "", False
    
    def revoke_key(self, service: str, key_id: str) -> bool:
        """Revoke specific API key"""
        if service not in self.keys or key_id not in self.keys[service]:
            return False
        
        self.keys[service][key_id].status = KeyStatus.REVOKED
        self._save_keys()
        
        logger.info(f"Revoked API key {key_id} for {service}")
        return True
    
    def cleanup_expired_keys(self) -> int:
        """Remove expired keys and return count of cleaned up keys"""
        now = datetime.utcnow()
        cleaned_count = 0
        
        for service in list(self.keys.keys()):
            for key_id in list(self.keys[service].keys()):
                key_info = self.keys[service][key_id]
                
                # Remove expired keys
                if key_info.expires_at and key_info.expires_at < now:
                    if key_info.status in [KeyStatus.ROTATING, KeyStatus.DEPRECATED]:
                        del self.keys[service][key_id]
                        cleaned_count += 1
                        logger.info(f"Cleaned up expired key {key_id} for {service}")
        
        if cleaned_count > 0:
            self._save_keys()
        
        return cleaned_count
    
    def update_rate_limit_info(
        self,
        service: str,
        remaining: int,
        reset_time: Optional[datetime] = None
    ):
        """Update rate limit information for active key"""
        if service not in self.keys:
            return
        
        # Find active key
        for key_info in self.keys[service].values():
            if key_info.status == KeyStatus.ACTIVE:
                key_info.rate_limit_remaining = remaining
                break
        
        self._save_keys()
    
    def get_key_status(self, service: str) -> Dict[str, any]:
        """Get status information for service keys"""
        if service not in self.keys:
            return {
                "service": service,
                "active_keys": 0,
                "rotating_keys": 0,
                "total_keys": 0,
                "has_active_key": False,
                "rate_limit_remaining": None
            }
        
        service_keys = self.keys[service]
        status_counts = {}
        rate_limit_remaining = None
        
        for status in KeyStatus:
            status_counts[status.value] = 0
        
        for key_info in service_keys.values():
            status_counts[key_info.status.value] += 1
            if key_info.status == KeyStatus.ACTIVE and key_info.rate_limit_remaining:
                rate_limit_remaining = key_info.rate_limit_remaining
        
        return {
            "service": service,
            "active_keys": status_counts["active"],
            "rotating_keys": status_counts["rotating"],
            "deprecated_keys": status_counts["deprecated"],
            "revoked_keys": status_counts["revoked"],
            "total_keys": len(service_keys),
            "has_active_key": status_counts["active"] > 0,
            "rate_limit_remaining": rate_limit_remaining
        }
    
    def get_all_services_status(self) -> Dict[str, Dict[str, any]]:
        """Get status for all services"""
        services = ["odds_api", "sportsdata_io", "rapid_api"]
        return {service: self.get_key_status(service) for service in services}
    
    def validate_key_configuration(self) -> Dict[str, List[str]]:
        """Validate key configuration and return any issues"""
        issues = {
            "errors": [],
            "warnings": [],
            "info": []
        }
        
        required_services = ["odds_api", "sportsdata_io"]
        optional_services = ["rapid_api"]
        
        # Check required services
        for service in required_services:
            status = self.get_key_status(service)
            if not status["has_active_key"]:
                issues["errors"].append(f"No active API key configured for {service}")
            elif status["active_keys"] > 1:
                issues["warnings"].append(f"Multiple active keys for {service}")
        
        # Check optional services
        for service in optional_services:
            status = self.get_key_status(service)
            if not status["has_active_key"]:
                issues["info"].append(f"Optional service {service} has no active key")
        
        # Check for expired keys
        now = datetime.utcnow()
        for service, service_keys in self.keys.items():
            for key_id, key_info in service_keys.items():
                if key_info.expires_at and key_info.expires_at < now + timedelta(days=7):
                    if key_info.status == KeyStatus.ACTIVE:
                        issues["warnings"].append(f"Active key {key_id} for {service} expires soon")
        
        return issues


# Global key rotation manager instance
key_manager = KeyRotationManager()


def get_key_manager() -> KeyRotationManager:
    """Get the global key rotation manager instance"""
    return key_manager