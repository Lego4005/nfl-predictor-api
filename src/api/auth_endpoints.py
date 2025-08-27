"""
Authentication API Endpoints
User registration, login, logout, and profile management
"""

import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Import our services
from auth import (
    password_service, jwt_service, token_manager, 
    get_current_user, PasswordStrength
)
from database import get_db, User, SubscriptionTier, Subscription

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/auth", tags=["authentication"])

# Pydantic models for request/response
class UserRegistrationRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    
    @validator('email')
    def validate_email(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Email is required')
        return v.lower().strip()
    
    @validator('password')
    def validate_password(cls, v):
        if not v or len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        if v:
            v = v.strip()
            if len(v) > 50:
                raise ValueError('Name must be less than 50 characters')
        return v

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str
    
    @validator('email')
    def validate_email(cls, v):
        return v.lower().strip()

class PasswordResetRequest(BaseModel):
    email: EmailStr
    
    @validator('email')
    def validate_email(cls, v):
        return v.lower().strip()

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if not v or len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class UserResponse(BaseModel):
    user_id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    email_verified: bool
    subscription_tier: Optional[str]
    subscription_expires: Optional[str]
    created_at: str
    
    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: UserResponse

class PasswordStrengthResponse(BaseModel):
    is_valid: bool
    strength: str
    score: int
    feedback: list
    requirements_met: dict

# Helper functions
async def send_verification_email(email: str, token: str):
    """Send email verification (placeholder)"""
    # In production, integrate with SendGrid/AWS SES
    logger.info(f"📧 Sending verification email to {email} with token {token[:16]}...")
    # TODO: Implement actual email sending

async def send_password_reset_email(email: str, token: str):
    """Send password reset email (placeholder)"""
    # In production, integrate with email service
    logger.info(f"🔄 Sending password reset email to {email} with token {token[:16]}...")
    # TODO: Implement actual email sending

def create_free_trial_subscription(db: Session, user_id: str) -> Optional[Subscription]:
    """Create free trial subscription for new user"""
    try:
        # Get free trial tier
        trial_tier = db.query(SubscriptionTier).filter_by(name='free_trial').first()
        if not trial_tier:
            logger.error("Free trial tier not found in database")
            return None
        
        # Create subscription
        subscription = Subscription(
            id=str(uuid.uuid4()),
            user_id=user_id,
            tier_id=trial_tier.id,
            status='trial',
            starts_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc).replace(hour=23, minute=59, second=59) + 
                      timedelta(days=trial_tier.duration_days),
            auto_renew=False
        )
        
        db.add(subscription)
        db.commit()
        db.refresh(subscription)
        
        logger.info(f"Created free trial subscription for user {user_id}")
        return subscription
        
    except Exception as e:
        logger.error(f"Failed to create free trial subscription: {e}")
        db.rollback()
        return None

# API Endpoints

@router.post("/register", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegistrationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Register a new user with email verification"""
    
    # Check rate limiting
    allowed, remaining, reset_time = password_service.check_rate_limit(
        user_data.email, 'registration', max_attempts=3, window_minutes=60
    )
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many registration attempts. Try again in {reset_time} minutes.",
            headers={"Retry-After": str(reset_time * 60)}
        )
    
    try:
        # Validate password strength
        user_info = {
            'first_name': user_data.first_name,
            'last_name': user_data.last_name,
            'email': user_data.email
        }
        
        password_validation = password_service.validate_password_strength(
            user_data.password, user_info
        )
        
        if not password_validation.is_valid:
            password_service.record_failed_attempt(user_data.email, 'registration')
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Password does not meet security requirements",
                    "feedback": password_validation.feedback,
                    "requirements_met": password_validation.requirements_met
                }
            )
        
        # Check if user already exists
        existing_user = db.query(User).filter_by(email=user_data.email).first()
        if existing_user:
            password_service.record_failed_attempt(user_data.email, 'registration')
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        
        # Hash password
        password_hash = password_service.hash_password(user_data.password)
        
        # Create user
        user_id = str(uuid.uuid4())
        new_user = User(
            id=user_id,
            email=user_data.email,
            password_hash=password_hash,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email_verified=False,
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(new_user)
        db.flush()  # Get the user ID
        
        # Create free trial subscription
        trial_subscription = create_free_trial_subscription(db, user_id)
        
        # Generate email verification token
        verification_token = jwt_service.generate_special_token(
            {'user_id': user_id, 'email': user_data.email},
            jwt_service.TokenType.EMAIL_VERIFICATION,
            expire_hours=24
        )
        
        # Send verification email in background
        background_tasks.add_task(send_verification_email, user_data.email, verification_token)
        
        db.commit()
        
        # Clear any failed registration attempts
        password_service.clear_failed_attempts(user_data.email, 'registration')
        
        logger.info(f"User registered successfully: {user_data.email}")
        
        return {
            "message": "User registered successfully",
            "user_id": user_id,
            "email": user_data.email,
            "email_verified": False,
            "free_trial_activated": trial_subscription is not None,
            "verification_required": True,
            "next_steps": [
                "Check your email for verification link",
                "Verify your email to activate account",
                "Start your 7-day free trial"
            ]
        }
        
    except HTTPException:
        raise
    except IntegrityError:
        db.rollback()
        password_service.record_failed_attempt(user_data.email, 'registration')
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    except Exception as e:
        db.rollback()
        password_service.record_failed_attempt(user_data.email, 'registration')
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )

@router.post("/login", response_model=LoginResponse)
async def login_user(
    login_data: UserLoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticate user and return JWT tokens"""
    
    # Check rate limiting
    allowed, remaining, reset_time = password_service.check_rate_limit(
        login_data.email, 'login', max_attempts=5, window_minutes=15
    )
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Try again in {reset_time} minutes.",
            headers={"Retry-After": str(reset_time * 60)}
        )
    
    try:
        # Find user
        user = db.query(User).filter_by(email=login_data.email).first()
        if not user:
            password_service.record_failed_attempt(login_data.email, 'login')
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.is_active:
            password_service.record_failed_attempt(login_data.email, 'login')
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated. Please contact support."
            )
        
        # Verify password
        if not password_service.verify_password(login_data.password, user.password_hash):
            password_service.record_failed_attempt(login_data.email, 'login')
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Get user's active subscription
        active_subscription = db.query(Subscription).filter_by(
            user_id=user.id,
            status='active'
        ).first()
        
        if not active_subscription:
            # Check for trial subscription
            active_subscription = db.query(Subscription).filter_by(
                user_id=user.id,
                status='trial'
            ).first()
        
        # Prepare user data for token
        subscription_tier = None
        subscription_expires = None
        
        if active_subscription:
            tier = db.query(SubscriptionTier).filter_by(id=active_subscription.tier_id).first()
            if tier:
                subscription_tier = tier.name
                subscription_expires = active_subscription.expires_at
        
        user_token_data = {
            'user_id': user.id,
            'email': user.email,
            'subscription_tier': subscription_tier,
            'subscription_expires': subscription_expires,
            'permissions': ['user']  # Basic user permissions
        }
        
        # Generate tokens
        session_data = token_manager.create_user_session(user_token_data)
        
        # Update last login
        user.last_login = datetime.now(timezone.utc)
        db.commit()
        
        # Clear failed login attempts
        password_service.clear_failed_attempts(login_data.email, 'login')
        
        logger.info(f"User logged in successfully: {user.email}")
        
        # Create response
        user_response = UserResponse(
            user_id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            email_verified=user.email_verified,
            subscription_tier=subscription_tier,
            subscription_expires=subscription_expires.isoformat() if subscription_expires else None,
            created_at=user.created_at.isoformat()
        )
        
        return LoginResponse(
            access_token=session_data['access_token'],
            refresh_token=session_data['refresh_token'],
            token_type=session_data['token_type'],
            expires_in=session_data['expires_in'],
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )

@router.post("/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """Verify user email address"""
    
    try:
        # Verify token
        payload = jwt_service.verify_special_token(token, jwt_service.TokenType.EMAIL_VERIFICATION)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        # Find user
        user = db.query(User).filter_by(id=payload.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if user.email_verified:
            return {"message": "Email already verified"}
        
        # Verify email
        user.email_verified = True
        db.commit()
        
        logger.info(f"Email verified for user: {user.email}")
        
        return {
            "message": "Email verified successfully",
            "email": user.email,
            "verified": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )

@router.post("/check-password-strength", response_model=PasswordStrengthResponse)
async def check_password_strength(
    password: str,
    user_info: Optional[Dict[str, str]] = None
):
    """Check password strength without creating account"""
    
    try:
        validation = password_service.validate_password_strength(password, user_info or {})
        
        return PasswordStrengthResponse(
            is_valid=validation.is_valid,
            strength=validation.strength.name,
            score=validation.score,
            feedback=validation.feedback,
            requirements_met=validation.requirements_met
        )
        
    except Exception as e:
        logger.error(f"Password strength check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password strength check failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    
    try:
        user = db.query(User).filter_by(id=current_user['user_id']).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(
            user_id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            email_verified=user.email_verified,
            subscription_tier=current_user.get('subscription_tier'),
            subscription_expires=current_user.get('subscription_expires'),
            created_at=user.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )

@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token"""
    
    try:
        # Refresh the session
        new_session = token_manager.refresh_session(refresh_token)
        
        if not new_session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        logger.info(f"Token refreshed for user: {new_session['user']['email']}")
        
        return {
            "access_token": new_session['access_token'],
            "refresh_token": new_session['refresh_token'],
            "token_type": new_session['token_type'],
            "expires_in": new_session['expires_in'],
            "refreshed_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/logout")
async def logout_user(
    access_token: str,
    refresh_token: str,
    current_user: Dict = Depends(get_current_user)
):
    """Logout user by blacklisting tokens"""
    
    try:
        # Blacklist both tokens
        success = token_manager.logout_user(access_token, refresh_token)
        
        if success:
            logger.info(f"User logged out: {current_user['email']}")
            return {
                "message": "Logged out successfully",
                "logged_out": True,
                "logged_out_at": datetime.now(timezone.utc).isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to logout properly"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.post("/forgot-password")
async def forgot_password(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Send password reset email"""
    
    # Check rate limiting for password reset requests
    allowed, remaining, reset_time = password_service.check_rate_limit(
        request.email, 'password_reset', max_attempts=3, window_minutes=60
    )
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many password reset requests. Try again in {reset_time} minutes."
        )
    
    try:
        # Find user
        user = db.query(User).filter_by(email=request.email).first()
        
        if user:
            # Generate reset token
            reset_token = password_service.generate_reset_token(user.id, user.email)
            
            # Send reset email in background
            background_tasks.add_task(send_password_reset_email, user.email, reset_token)
            
            logger.info(f"Password reset requested for: {user.email}")
        else:
            # Don't reveal if email exists or not
            logger.info(f"Password reset requested for non-existent email: {request.email}")
        
        # Always return success to prevent email enumeration
        return {
            "message": "If an account with that email exists, a password reset link has been sent.",
            "email": request.email,
            "reset_requested": True
        }
        
    except Exception as e:
        logger.error(f"Password reset request error: {e}")
        # Still return success to prevent information leakage
        return {
            "message": "If an account with that email exists, a password reset link has been sent.",
            "email": request.email,
            "reset_requested": True
        }

@router.post("/reset-password")
async def reset_password(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Reset password using reset token"""
    
    try:
        # Verify reset token
        token_data = password_service.verify_reset_token(request.token)
        
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Find user
        user = db.query(User).filter_by(id=token_data.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validate new password
        user_info = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email
        }
        
        password_validation = password_service.validate_password_strength(
            request.new_password, user_info
        )
        
        if not password_validation.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "New password does not meet security requirements",
                    "feedback": password_validation.feedback,
                    "requirements_met": password_validation.requirements_met
                }
            )
        
        # Hash new password
        new_password_hash = password_service.hash_password(request.new_password)
        
        # Update user password
        user.password_hash = new_password_hash
        
        # Mark token as used
        password_service.use_reset_token(request.token)
        
        db.commit()
        
        logger.info(f"Password reset completed for user: {user.email}")
        
        return {
            "message": "Password reset successfully",
            "email": user.email,
            "reset_completed": True,
            "reset_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )

@router.get("/sessions")
async def get_user_sessions(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's active sessions (placeholder for future implementation)"""
    
    try:
        # In a full implementation, you'd track sessions in the database
        # For now, return basic session info
        return {
            "user_id": current_user['user_id'],
            "email": current_user['email'],
            "current_session": {
                "token_expires_at": current_user.get('token_expires_at'),
                "subscription_tier": current_user.get('subscription_tier'),
                "permissions": current_user.get('permissions', [])
            },
            "active_sessions_count": 1,  # Current session
            "last_login": None  # Would come from database
        }
        
    except Exception as e:
        logger.error(f"Get sessions error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get session information"
        )

@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password (requires current password)"""
    
    try:
        # Find user
        user = db.query(User).filter_by(id=current_user['user_id']).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not password_service.verify_password(old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password
        user_info = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email
        }
        
        password_validation = password_service.validate_password_strength(
            new_password, user_info
        )
        
        if not password_validation.is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "New password does not meet security requirements",
                    "feedback": password_validation.feedback,
                    "requirements_met": password_validation.requirements_met
                }
            )
        
        # Check if new password is different from old password
        if password_service.verify_password(new_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password"
            )
        
        # Hash new password
        new_password_hash = password_service.hash_password(new_password)
        
        # Update password
        user.password_hash = new_password_hash
        db.commit()
        
        logger.info(f"Password changed for user: {user.email}")
        
        return {
            "message": "Password changed successfully",
            "changed_at": datetime.now(timezone.utc).isoformat(),
            "user_id": user.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Change password error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )