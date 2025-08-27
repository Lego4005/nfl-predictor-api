"""
Promotional and Discount System Models
Handles discount codes, promotional campaigns, and subscription offers
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import (
    Column, String, Integer, DateTime, Boolean, DECIMAL, 
    ForeignKey, Index, UniqueConstraint, Text, JSONB
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..database.models import Base

class PromotionalCampaign(Base):
    """Marketing campaigns with multiple discount codes"""
    __tablename__ = 'promotional_campaigns'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    campaign_type = Column(String(50), nullable=False)  # 'seasonal', 'launch', 'retention', 'acquisition'
    
    # Campaign period
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    
    # Campaign settings
    is_active = Column(Boolean, default=True)
    max_total_uses = Column(Integer)  # Total uses across all codes in campaign
    current_total_uses = Column(Integer, default=0)
    
    # Targeting
    target_audience = Column(String(50))  # 'new_users', 'existing_users', 'churned_users', 'all'
    target_tiers = Column(JSONB, default=list)  # Which subscription tiers this applies to
    
    # Analytics
    conversion_rate = Column(DECIMAL(5, 4))
    total_revenue_impact = Column(DECIMAL(12, 2), default=0.00)
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey('admin_users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    discount_codes = relationship("DiscountCode", back_populates="campaign")
    
    # Indexes
    __table_args__ = (
        Index('idx_promotional_campaigns_active', 'is_active'),
        Index('idx_promotional_campaigns_dates', 'start_date', 'end_date'),
        Index('idx_promotional_campaigns_type', 'campaign_type'),
    )

class DiscountCode(Base):
    """Individual discount codes with usage tracking"""
    __tablename__ = 'discount_codes'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('promotional_campaigns.id'), nullable=True)
    
    # Code details
    code = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(String(500))
    
    # Discount configuration
    discount_type = Column(String(20), nullable=False)  # 'percentage', 'fixed_amount', 'free_trial', 'upgrade'
    discount_value = Column(DECIMAL(10, 2), nullable=False)  # Percentage (0-100) or dollar amount
    
    # Applicability
    applicable_tiers = Column(JSONB, default=list)  # Which tiers this code applies to
    minimum_tier = Column(String(20))  # Minimum tier required to use code
    
    # Usage limits
    max_uses = Column(Integer)  # NULL = unlimited
    max_uses_per_user = Column(Integer, default=1)
    current_uses = Column(Integer, default=0)
    
    # Validity period
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=False)
    
    # Restrictions
    first_time_users_only = Column(Boolean, default=False)
    requires_minimum_purchase = Column(DECIMAL(10, 2))
    stackable = Column(Boolean, default=False)  # Can be combined with other discounts
    
    # Status
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)  # False for targeted/private codes
    
    # Analytics
    conversion_rate = Column(DECIMAL(5, 4))
    total_revenue_impact = Column(DECIMAL(12, 2), default=0.00)
    average_order_value = Column(DECIMAL(10, 2))
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey('admin_users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    campaign = relationship("PromotionalCampaign", back_populates="discount_codes")
    usages = relationship("DiscountUsage", back_populates="discount_code")
    
    # Indexes
    __table_args__ = (
        Index('idx_discount_codes_active', 'is_active'),
        Index('idx_discount_codes_validity', 'valid_from', 'valid_until'),
        Index('idx_discount_codes_type', 'discount_type'),
        Index('idx_discount_codes_public', 'is_public'),
    )

class DiscountUsage(Base):
    """Track individual uses of discount codes"""
    __tablename__ = 'discount_usages'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    discount_code_id = Column(UUID(as_uuid=True), ForeignKey('discount_codes.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id'), nullable=True)
    
    # Usage details
    original_amount_cents = Column(Integer, nullable=False)
    discount_amount_cents = Column(Integer, nullable=False)
    final_amount_cents = Column(Integer, nullable=False)
    
    # Context
    subscription_tier = Column(String(20), nullable=False)
    usage_context = Column(String(50))  # 'new_subscription', 'renewal', 'upgrade'
    
    # Metadata
    used_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Relationships
    discount_code = relationship("DiscountCode", back_populates="usages")
    
    # Indexes
    __table_args__ = (
        Index('idx_discount_usages_code_id', 'discount_code_id'),
        Index('idx_discount_usages_user_id', 'user_id'),
        Index('idx_discount_usages_used_at', 'used_at'),
    )

class SubscriptionOffer(Base):
    """Special subscription offers and bundles"""
    __tablename__ = 'subscription_offers'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Offer details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    offer_type = Column(String(30), nullable=False)  # 'bundle', 'extended_trial', 'loyalty_discount', 'upgrade_incentive'
    
    # Pricing
    original_price_cents = Column(Integer, nullable=False)
    offer_price_cents = Column(Integer, nullable=False)
    savings_cents = Column(Integer, nullable=False)
    savings_percentage = Column(DECIMAL(5, 2), nullable=False)
    
    # Offer configuration
    base_tier = Column(String(20), nullable=False)  # Base subscription tier
    bonus_features = Column(JSONB, default=list)  # Additional features included
    extended_duration_days = Column(Integer, default=0)  # Extra days beyond normal tier
    
    # Availability
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=False)
    max_redemptions = Column(Integer)
    current_redemptions = Column(Integer, default=0)
    
    # Targeting
    target_user_types = Column(JSONB, default=list)  # 'new', 'returning', 'churned'
    requires_code = Column(Boolean, default=False)
    associated_code = Column(String(50))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)  # Show prominently on pricing page
    
    # Analytics
    conversion_rate = Column(DECIMAL(5, 4))
    total_revenue = Column(DECIMAL(12, 2), default=0.00)
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey('admin_users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    redemptions = relationship("OfferRedemption", back_populates="offer")
    
    # Indexes
    __table_args__ = (
        Index('idx_subscription_offers_active', 'is_active'),
        Index('idx_subscription_offers_validity', 'valid_from', 'valid_until'),
        Index('idx_subscription_offers_featured', 'is_featured'),
        Index('idx_subscription_offers_type', 'offer_type'),
    )

class OfferRedemption(Base):
    """Track redemptions of subscription offers"""
    __tablename__ = 'offer_redemptions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_id = Column(UUID(as_uuid=True), ForeignKey('subscription_offers.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey('subscriptions.id'), nullable=False)
    
    # Redemption details
    original_amount_cents = Column(Integer, nullable=False)
    discount_amount_cents = Column(Integer, nullable=False)
    final_amount_cents = Column(Integer, nullable=False)
    
    # Context
    redemption_context = Column(String(50))  # 'new_subscription', 'renewal', 'upgrade'
    discount_code_used = Column(String(50))  # If a code was also used
    
    # Metadata
    redeemed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    offer = relationship("SubscriptionOffer", back_populates="redemptions")
    
    # Indexes
    __table_args__ = (
        Index('idx_offer_redemptions_offer_id', 'offer_id'),
        Index('idx_offer_redemptions_user_id', 'user_id'),
        Index('idx_offer_redemptions_redeemed_at', 'redeemed_at'),
    )

class LoyaltyProgram(Base):
    """Loyalty program for long-term subscribers"""
    __tablename__ = 'loyalty_programs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    
    # Loyalty status
    tier = Column(String(20), default='bronze')  # 'bronze', 'silver', 'gold', 'platinum'
    points_balance = Column(Integer, default=0)
    lifetime_points = Column(Integer, default=0)
    
    # Subscription history
    total_months_subscribed = Column(Integer, default=0)
    consecutive_months = Column(Integer, default=0)
    total_amount_spent_cents = Column(Integer, default=0)
    
    # Benefits
    discount_percentage = Column(DECIMAL(5, 2), default=0.00)  # Ongoing discount
    bonus_features = Column(JSONB, default=list)
    priority_support = Column(Boolean, default=False)
    
    # Milestones
    next_tier_threshold = Column(Integer)
    last_tier_upgrade = Column(DateTime(timezone=True))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_loyalty_programs_tier', 'tier'),
        Index('idx_loyalty_programs_points', 'points_balance'),
    )

class PromotionalEmail(Base):
    """Track promotional email campaigns"""
    __tablename__ = 'promotional_emails'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('promotional_campaigns.id'), nullable=True)
    
    # Email details
    subject = Column(String(200), nullable=False)
    template_name = Column(String(100), nullable=False)
    
    # Targeting
    target_segment = Column(String(50), nullable=False)  # 'all', 'free_users', 'churned', 'high_value'
    target_count = Column(Integer, default=0)
    
    # Performance
    sent_count = Column(Integer, default=0)
    delivered_count = Column(Integer, default=0)
    opened_count = Column(Integer, default=0)
    clicked_count = Column(Integer, default=0)
    converted_count = Column(Integer, default=0)
    
    # Rates
    delivery_rate = Column(DECIMAL(5, 4))
    open_rate = Column(DECIMAL(5, 4))
    click_rate = Column(DECIMAL(5, 4))
    conversion_rate = Column(DECIMAL(5, 4))
    
    # Status
    status = Column(String(20), default='draft')  # 'draft', 'scheduled', 'sending', 'sent', 'cancelled'
    scheduled_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    
    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey('admin_users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_promotional_emails_status', 'status'),
        Index('idx_promotional_emails_sent_at', 'sent_at'),
        Index('idx_promotional_emails_segment', 'target_segment'),
    )