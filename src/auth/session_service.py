"""
Session Management Service
Tracks user sessions, devices, and provides session analytics
"""

import os
import logging
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from user_agents import parse

logger = logging.getLogger(__name__)

class SessionStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"

@dataclass
class SessionInfo:
    """User session information"""
    session_id: str
    user_id: str
    device_info: Dict
    ip_address: str
    location: Optional[str]
    created_at: datetime
    last_accessed: datetime
    expires_at: datetime
    status: SessionStatus
    token_hash: str

@dataclass
class DeviceInfo:
    """Device information from user agent"""
    browser: str
    browser_version: str
    os: str
    os_version: str
    device_type: str
    is_mobile: bool
    is_tablet: bool
    is_pc: bool

class SessionService:
    """Manages user sessions and device tracking"""
    
    def __init__(self):
        # In production, use Redis or database for session storage
        self._active_sessions: Dict[str, SessionInfo] = {}
        self._user_sessions: Dict[str, List[str]] = {}  # user_id -> session_ids
        
        # Session configuration
        self.max_sessions_per_user = int(os.getenv('MAX_SESSIONS_PER_USER', '5'))
        self.session_timeout_hours = int(os.getenv('SESSION_TIMEOUT_HOURS', '24'))
        self.cleanup_interval_hours = int(os.getenv('SESSION_CLEANUP_HOURS', '1'))
        
        self._last_cleanup = datetime.now(timezone.utc)
    
    def parse_user_agent(self, user_agent: str) -> DeviceInfo:
        """Parse user agent string to extract device information"""
        try:
            parsed = parse(user_agent)
            
            return DeviceInfo(
                browser=parsed.browser.family,
                browser_version=parsed.browser.version_string,
                os=parsed.os.family,
                os_version=parsed.os.version_string,
                device_type=parsed.device.family,
                is_mobile=parsed.is_mobile,
                is_tablet=parsed.is_tablet,
                is_pc=parsed.is_pc
            )
        except Exception as e:
            logger.warning(f"Failed to parse user agent: {e}")
            return DeviceInfo(
                browser="Unknown",
                browser_version="",
                os="Unknown",
                os_version="",
                device_type="Unknown",
                is_mobile=False,
                is_tablet=False,
                is_pc=True
            )
    
    def create_session(self, user_id: str, ip_address: str, user_agent: str, 
                      token_hash: str) -> SessionInfo:
        """Create a new user session"""
        
        # Clean up expired sessions first
        self._cleanup_expired_sessions()
        
        # Parse device info
        device_info = self.parse_user_agent(user_agent)
        
        # Generate session ID
        session_data = f"{user_id}:{ip_address}:{user_agent}:{datetime.now(timezone.utc).isoformat()}"
        session_id = hashlib.sha256(session_data.encode()).hexdigest()[:32]
        
        # Create session
        now = datetime.now(timezone.utc)
        session = SessionInfo(
            session_id=session_id,
            user_id=user_id,
            device_info=device_info.__dict__,
            ip_address=ip_address,
            location=self._get_location_from_ip(ip_address),
            created_at=now,
            last_accessed=now,
            expires_at=now + timedelta(hours=self.session_timeout_hours),
            status=SessionStatus.ACTIVE,
            token_hash=token_hash
        )
        
        # Check session limits
        self._enforce_session_limits(user_id)
        
        # Store session
        self._active_sessions[session_id] = session
        
        if user_id not in self._user_sessions:
            self._user_sessions[user_id] = []
        self._user_sessions[user_id].append(session_id)
        
        logger.info(f"Created session {session_id} for user {user_id} from {ip_address}")
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """Get session by ID"""
        session = self._active_sessions.get(session_id)
        
        if session and session.status == SessionStatus.ACTIVE:
            # Check if expired
            if datetime.now(timezone.utc) > session.expires_at:
                session.status = SessionStatus.EXPIRED
                return None
            
            # Update last accessed
            session.last_accessed = datetime.now(timezone.utc)
            return session
        
        return None
    
    def get_user_sessions(self, user_id: str) -> List[SessionInfo]:
        """Get all active sessions for a user"""
        session_ids = self._user_sessions.get(user_id, [])
        sessions = []
        
        for session_id in session_ids:
            session = self.get_session(session_id)
            if session:
                sessions.append(session)
        
        return sessions
    
    def revoke_session(self, session_id: str) -> bool:
        """Revoke a specific session"""
        session = self._active_sessions.get(session_id)
        
        if session:
            session.status = SessionStatus.REVOKED
            logger.info(f"Revoked session {session_id}")
            return True
        
        return False
    
    def revoke_user_sessions(self, user_id: str, except_session_id: str = None) -> int:
        """Revoke all sessions for a user except optionally one"""
        session_ids = self._user_sessions.get(user_id, [])
        revoked_count = 0
        
        for session_id in session_ids:
            if session_id != except_session_id:
                if self.revoke_session(session_id):
                    revoked_count += 1
        
        logger.info(f"Revoked {revoked_count} sessions for user {user_id}")
        return revoked_count
    
    def _enforce_session_limits(self, user_id: str):
        """Enforce maximum sessions per user"""
        user_sessions = self.get_user_sessions(user_id)
        
        if len(user_sessions) >= self.max_sessions_per_user:
            # Sort by last accessed (oldest first)
            user_sessions.sort(key=lambda s: s.last_accessed)
            
            # Revoke oldest sessions
            sessions_to_revoke = len(user_sessions) - self.max_sessions_per_user + 1
            for i in range(sessions_to_revoke):
                self.revoke_session(user_sessions[i].session_id)
                logger.info(f"Revoked old session for user {user_id} due to session limit")
    
    def _get_location_from_ip(self, ip_address: str) -> Optional[str]:
        """Get approximate location from IP address (placeholder)"""
        # In production, integrate with IP geolocation service
        if ip_address.startswith('127.') or ip_address.startswith('192.168.'):
            return "Local Network"
        return "Unknown Location"
    
    def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        now = datetime.now(timezone.utc)
        
        # Only run cleanup periodically
        if now - self._last_cleanup < timedelta(hours=self.cleanup_interval_hours):
            return
        
        expired_sessions = []
        
        for session_id, session in self._active_sessions.items():
            if (session.status == SessionStatus.EXPIRED or 
                session.status == SessionStatus.REVOKED or
                now > session.expires_at):
                expired_sessions.append(session_id)
        
        # Remove expired sessions
        for session_id in expired_sessions:
            session = self._active_sessions.pop(session_id, None)
            if session:
                # Remove from user sessions
                user_sessions = self._user_sessions.get(session.user_id, [])
                if session_id in user_sessions:
                    user_sessions.remove(session_id)
        
        self._last_cleanup = now
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def get_session_analytics(self, user_id: str) -> Dict:
        """Get session analytics for a user"""
        user_sessions = self.get_user_sessions(user_id)
        
        if not user_sessions:
            return {
                "total_sessions": 0,
                "active_sessions": 0,
                "devices": [],
                "locations": [],
                "last_login": None
            }
        
        # Analyze devices
        devices = {}
        locations = {}
        
        for session in user_sessions:
            device_key = f"{session.device_info.get('os', 'Unknown')} - {session.device_info.get('browser', 'Unknown')}"
            devices[device_key] = devices.get(device_key, 0) + 1
            
            location = session.location or "Unknown"
            locations[location] = locations.get(location, 0) + 1
        
        # Find most recent session
        most_recent = max(user_sessions, key=lambda s: s.last_accessed)
        
        return {
            "total_sessions": len(user_sessions),
            "active_sessions": len([s for s in user_sessions if s.status == SessionStatus.ACTIVE]),
            "devices": [{"name": k, "count": v} for k, v in devices.items()],
            "locations": [{"name": k, "count": v} for k, v in locations.items()],
            "last_login": most_recent.created_at.isoformat(),
            "last_accessed": most_recent.last_accessed.isoformat()
        }
    
    def detect_suspicious_activity(self, user_id: str) -> List[Dict]:
        """Detect potentially suspicious session activity"""
        user_sessions = self.get_user_sessions(user_id)
        alerts = []
        
        if len(user_sessions) <= 1:
            return alerts
        
        # Check for multiple locations
        locations = set(s.location for s in user_sessions if s.location)
        if len(locations) > 2:
            alerts.append({
                "type": "multiple_locations",
                "severity": "medium",
                "message": f"Sessions detected from {len(locations)} different locations",
                "locations": list(locations)
            })
        
        # Check for rapid session creation
        now = datetime.now(timezone.utc)
        recent_sessions = [s for s in user_sessions 
                          if now - s.created_at < timedelta(minutes=30)]
        
        if len(recent_sessions) > 3:
            alerts.append({
                "type": "rapid_sessions",
                "severity": "high",
                "message": f"{len(recent_sessions)} sessions created in the last 30 minutes",
                "session_count": len(recent_sessions)
            })
        
        # Check for unusual devices
        device_types = set(s.device_info.get('device_type', 'Unknown') for s in user_sessions)
        if len(device_types) > 3:
            alerts.append({
                "type": "multiple_devices",
                "severity": "low",
                "message": f"Sessions from {len(device_types)} different device types",
                "devices": list(device_types)
            })
        
        return alerts
    
    def get_session_summary(self) -> Dict:
        """Get overall session statistics"""
        self._cleanup_expired_sessions()
        
        active_sessions = [s for s in self._active_sessions.values() 
                          if s.status == SessionStatus.ACTIVE]
        
        # Device statistics
        device_stats = {}
        location_stats = {}
        
        for session in active_sessions:
            device = session.device_info.get('os', 'Unknown')
            device_stats[device] = device_stats.get(device, 0) + 1
            
            location = session.location or "Unknown"
            location_stats[location] = location_stats.get(location, 0) + 1
        
        return {
            "total_active_sessions": len(active_sessions),
            "unique_users": len(set(s.user_id for s in active_sessions)),
            "device_breakdown": device_stats,
            "location_breakdown": location_stats,
            "average_sessions_per_user": len(active_sessions) / max(len(self._user_sessions), 1)
        }

# Global session service instance
session_service = SessionService()