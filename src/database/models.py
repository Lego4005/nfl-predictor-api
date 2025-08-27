"""
Database models for NFL Prediction SaaS Platform
Includes user authentication, subscriptions, admin access, and affiliate program
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, DECIMAL, 
    ForeignKey, Index, UniqueConstraint, JSON
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, INET, JSONB
from sqlalchemy.types import TypeDecorator, CHAR
import uuid as uuid_lib
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import Optional, List

Base = declarative_base()

class UUID(TypeDecorator):
    """Platform-independent UUID type"""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PG_UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if not isinstance(value, uuid_lib.UUID):
                return str(uuid_lib.UUID(value))
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid_lib.UUID):
                return uuid_lib.UUID(value)
            return value

# Use JSON for SQLite compatibility, JSONB for PostgreSQL
def get_json_type():
    """Get appropriate JSON type for the database"""
    import os
    if os.getenv('USE_SQLITE', 'false').lower() == 'true':
        return JSON
    return JSONB

class User(Base):
    """Core user model for authentication and profile management"""
    __tablename__ = 'users'
    
    id = Column(UUID(), primary_key=True, default=uuid_lib.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    email_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    free_access_grants = relationship("FreeAccessGrant", back_populates="user", cascade="all, delete-orphan")
    admin_user = relationship("AdminUser", back_populates="user", uselist=False)
    affiliate = relationship("Affiliate", back_populates="user", uselist=False)
    referrals = relationship("Referral", foreign_keys="Referral.referred_user_id", back_populates="referred_user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

class UserSession(Base):
    """User session management for JWT tokens"""
    __tablename__ = 'user_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token_hash = Column(String(255), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(INET)
    user_agent = Column(Text)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_sessions_user_id', 'user_id'),
        Index('idx_user_sessions_expires_at', 'expires_at'),
    )

class EmailVerification(Base):
    """Email verification tokens"""
    __tablename__ = 'email_verifications'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PasswordReset(Base):
    """Password reset tokens"""
    __tablename__ = 'password_resets'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SubscriptionTier(Base):
    """Subscription tier definitions"""
    __tablename__ = 'subscription_tiers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)  # 'free_trial', 'daily', 'weekly', 'monthly', 'season'
    display_name = Column(String(100), nullable=False)
    price_cents = Column(Integer, nullable=False)  # Price in cents
    duration_days = Column(Integer)  # NULL for custom/admin-granted
    features = Column(JSONB, nullable=False, default=list)
    is_active = Column(Boolean, default=True)
    is_admin_granted = Column(Boolean, default=False)  # For friends/family, beta tester
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="tier")

class Subscription(Base):
    """User subscriptions"""
    __tablename__ = 'subscriptions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    tier_id = Column(Integer, ForeignKey('subscription_tiers.id'), nullable=False)
    status = Column(String(20), nullable=False, default='active')  # 'active', 'cancelled', 'expired', 'trial'
    starts_at = Column(DateTime(timezone=True), nullable=False)
    expires_at = Column(DateTime(timezone=True))
    stripe_subscription_id = Column(String(255), index=True)
    stripe_customer_id = Column(String(255), index=True)
    auto_renew = Column(Boolean, default=True)
    amount_paid_cents = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    tier = relationship("SubscriptionTier", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription")
    referrals = relationship("Referral", back_populates="subscription")
    
    # Indexes
    __table_args__ = (
        Index('idx_subscriptions_user_id', 'user_id'),
        Index('idx_subscriptions_status', 'status'),
        Index('idx_subscriptions_expires_at', 'expires_at'),
    )

class Payment(Base):
    """Payment history and transactions"""
    __tablename__ = 'payments'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id'), nullable=True)
    stripe_payment_intent_id = Column(String(255), index=True)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), default='USD')
    status = Column(String(20), nullable=False)  # 'pending', 'succeeded', 'failed', 'refunded'
    payment_method = Column(String(50))  # 'stripe', 'paypal', etc.
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    subscription = relationship("Subscription", back_populates="payments")

class AdminUser(Base):
    """Admin users with role-based permissions"""
    __tablename__ = 'admin_users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    role = Column(String(50), nullable=False, default='admin')  # 'super_admin', 'admin', 'support'
    permissions = Column(JSONB, nullable=False, default=list)
    created_by = Column(UUID(as_uuid=True), ForeignKey('admin_users.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_admin_login = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="admin_user")
    created_grants = relationship("FreeAccessGrant", foreign_keys="FreeAccessGrant.granted_by", back_populates="granted_by_admin")

class FreeAccessGrant(Base):
    """Free access grants for friends/family and beta testers"""
    __tablename__ = 'free_access_grants'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    granted_by = Column(UUID(as_uuid=True), ForeignKey('admin_users.id'), nullable=False)
    access_type = Column(String(50), nullable=False)  # 'friends_family', 'beta_tester', 'promotional'
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True), nullable=False)
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="free_access_grants")
    granted_by_admin = relationship("AdminUser", foreign_keys=[granted_by], back_populates="created_grants")
    
    # Indexes
    __table_args__ = (
        Index('idx_free_access_grants_user_id', 'user_id'),
        Index('idx_free_access_grants_access_type', 'access_type'),
        Index('idx_free_access_grants_end_date', 'end_date'),
    )

class Affiliate(Base):
    """Affiliate program participants"""
    __tablename__ = 'affiliates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    referral_code = Column(String(20), unique=True, nullable=False, index=True)
    commission_rate = Column(DECIMAL(5, 4), default=0.30)  # 30% default
    tier = Column(String(20), default='bronze')  # 'bronze', 'silver', 'gold'
    total_referrals = Column(Integer, default=0)
    total_earnings_cents = Column(Integer, default=0)
    pending_earnings_cents = Column(Integer, default=0)
    paid_earnings_cents = Column(Integer, default=0)
    payout_method = Column(String(50))  # 'paypal', 'bank_transfer'
    payout_details = Column(JSONB, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="affiliate")
    referrals = relationship("Referral", back_populates="affiliate")
    payouts = relationship("AffiliatePayout", back_populates="affiliate")

class Referral(Base):
    """Referral tracking for affiliate program"""
    __tablename__ = 'referrals'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    affiliate_id = Column(UUID(as_uuid=True), ForeignKey('affiliates.id', ondelete='CASCADE'), nullable=False)
    referred_user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    referral_code = Column(String(20), nullable=False, index=True)
    conversion_date = Column(DateTime(timezone=True))  # When they became paying customer
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id'))
    commission_earned_cents = Column(Integer, default=0)
    commission_paid = Column(Boolean, default=False)
    status = Column(String(20), default='pending')  # 'pending', 'converted', 'paid'
    click_data = Column(JSONB, default=dict)  # IP, user agent, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    affiliate = relationship("Affiliate", back_populates="referrals")
    referred_user = relationship("User", foreign_keys=[referred_user_id], back_populates="referrals")
    subscription = relationship("Subscription", back_populates="referrals")
    
    # Indexes
    __table_args__ = (
        Index('idx_referrals_affiliate_id', 'affiliate_id'),
        Index('idx_referrals_referred_user_id', 'referred_user_id'),
        Index('idx_referrals_status', 'status'),
        UniqueConstraint('affiliate_id', 'referred_user_id', name='uq_affiliate_referred_user'),
    )

class AffiliatePayout(Base):
    """Affiliate payout processing"""
    __tablename__ = 'affiliate_payouts'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    affiliate_id = Column(UUID(as_uuid=True), ForeignKey('affiliates.id', ondelete='CASCADE'), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    payout_method = Column(String(50), nullable=False)
    transaction_id = Column(String(255))
    status = Column(String(20), default='pending')  # 'pending', 'processing', 'completed', 'failed'
    processed_at = Column(DateTime(timezone=True))
    metadata = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    affiliate = relationship("Affiliate", back_populates="payouts")
    
    # Indexes
    __table_args__ = (
        Index('idx_affiliate_payouts_affiliate_id', 'affiliate_id'),
        Index('idx_affiliate_payouts_status', 'status'),
    )

class Prediction(Base):
    """Prediction tracking for accuracy metrics"""
    __tablename__ = 'predictions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    week = Column(Integer, nullable=False)
    season = Column(Integer, nullable=False)
    prediction_type = Column(String(20), nullable=False)  # 'game', 'ats', 'total', 'prop'
    home_team = Column(String(10))
    away_team = Column(String(10))
    matchup = Column(String(100))
    prediction_data = Column(JSONB, nullable=False)
    confidence = Column(DECIMAL(5, 4))
    actual_result = Column(JSONB)
    is_correct = Column(Boolean)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    result_updated_at = Column(DateTime(timezone=True))
    
    # Relationships
    user_accesses = relationship("UserPredictionAccess", back_populates="prediction")
    
    # Indexes
    __table_args__ = (
        Index('idx_predictions_week_season', 'week', 'season'),
        Index('idx_predictions_type', 'prediction_type'),
        Index('idx_predictions_created_at', 'created_at'),
    )

class UserPredictionAccess(Base):
    """Track which predictions users have accessed"""
    __tablename__ = 'user_prediction_access'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    prediction_id = Column(UUID(as_uuid=True), ForeignKey('predictions.id', ondelete='CASCADE'), nullable=False)
    accessed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    prediction = relationship("Prediction", back_populates="user_accesses")
    
    # Indexes
    __table_args__ = (
        Index('idx_user_prediction_access_user_id', 'user_id'),
        Index('idx_user_prediction_access_prediction_id', 'prediction_id'),
        UniqueConstraint('user_id', 'prediction_id', name='uq_user_prediction_access'),
    )

class AccuracyMetric(Base):
    """Aggregated accuracy metrics"""
    __tablename__ = 'accuracy_metrics'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    week = Column(Integer, nullable=False)
    season = Column(Integer, nullable=False)
    prediction_type = Column(String(20), nullable=False)
    total_predictions = Column(Integer, nullable=False)
    correct_predictions = Column(Integer, nullable=False)
    accuracy_percentage = Column(DECIMAL(5, 2), nullable=False)
    confidence_weighted_accuracy = Column(DECIMAL(5, 2))
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_accuracy_metrics_week_season_type', 'week', 'season', 'prediction_type'),
        UniqueConstraint('week', 'season', 'prediction_type', name='uq_accuracy_metrics'),
    )

class AuditLog(Base):
    """Audit trail for security and compliance"""
    __tablename__ = 'audit_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    admin_user_id = Column(UUID(as_uuid=True), ForeignKey('admin_users.id', ondelete='SET NULL'))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(String(255))
    details = Column(JSONB, default=dict)
    ip_address = Column(INET)
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_audit_logs_user_id', 'user_id'),
        Index('idx_audit_logs_admin_user_id', 'admin_user_id'),
        Index('idx_audit_logs_action', 'action'),
        Index('idx_audit_logs_created_at', 'created_at'),
    )