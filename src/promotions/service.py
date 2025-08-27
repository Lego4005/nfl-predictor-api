"""
Promotional Service
Handles discount validation, application, and promotional campaign management
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from .models import (
    PromotionalCampaign, DiscountCode, DiscountUsage, 
    SubscriptionOffer, OfferRedemption, LoyaltyProgram
)
from ..database.models import User, Subscription, SubscriptionTier
from ..database.connection import get_db

logger = logging.getLogger(__name__)

class PromotionalService:
    """Service for managing promotions, discounts, and offers"""
    
    def __init__(self):
        self.loyalty_tiers = {
            'bronze': {'threshold': 0, 'discount': 0, 'features': []},
            'silver': {'threshold': 6, 'discount': 5, 'features': ['priority_support']},
            'gold': {'threshold': 12, 'discount': 10, 'features': ['priority_support', 'early_access']},
            'platinum': {'threshold': 24, 'discount': 15, 'features': ['priority_support', 'early_access', 'exclusive_content']}
        }
    
    def validate_discount_code(self, code: str, user_id: str, tier_name: str) -> Dict:
        """Validate if a discount code can be used by a user"""
        with get_db() as db:
            try:
                # Get discount code
                discount = db.query(DiscountCode).filter_by(
                    code=code.upper(),
                    is_active=True
                ).first()
                
                if not discount:
                    return {
                        'valid': False,
                        'error': 'Invalid or expired discount code',
                        'error_code': 'INVALID_CODE'
                    }
                
                # Check validity period
                current_time = datetime.utcnow()
                if current_time < discount.valid_from or current_time > discount.valid_until:
                    return {
                        'valid': False,
                        'error': 'Discount code has expired',
                        'error_code': 'EXPIRED_CODE'
                    }
                
                # Check usage limits
                if discount.max_uses and discount.current_uses >= discount.max_uses:
                    return {
                        'valid': False,
                        'error': 'Discount code usage limit reached',
                        'error_code': 'USAGE_LIMIT_REACHED'
                    }
                
                # Check per-user usage limit
                user_usage_count = db.query(DiscountUsage).filter_by(
                    discount_code_id=discount.id,
                    user_id=user_id
                ).count()
                
                if user_usage_count >= discount.max_uses_per_user:
                    return {
                        'valid': False,
                        'error': 'You have already used this discount code',
                        'error_code': 'USER_LIMIT_REACHED'
                    }
                
                # Check tier applicability
                if discount.applicable_tiers and tier_name not in discount.applicable_tiers:
                    return {
                        'valid': False,
                        'error': f'Discount code not applicable to {tier_name} subscription',
                        'error_code': 'TIER_NOT_APPLICABLE'
                    }
                
                # Check minimum tier requirement
                if discount.minimum_tier:
                    tier_levels = {'daily': 1, 'weekly': 2, 'monthly': 3, 'season': 4}
                    user_tier_level = tier_levels.get(tier_name, 0)
                    min_tier_level = tier_levels.get(discount.minimum_tier, 0)
                    
                    if user_tier_level < min_tier_level:
                        return {
                            'valid': False,
                            'error': f'Minimum {discount.minimum_tier} subscription required',
                            'error_code': 'MINIMUM_TIER_REQUIRED'
                        }
                
                # Check first-time user restriction
                if discount.first_time_users_only:
                    existing_subs = db.query(Subscription).filter_by(user_id=user_id).count()
                    if existing_subs > 0:
                        return {
                            'valid': False,
                            'error': 'This discount is only for new subscribers',
                            'error_code': 'NEW_USERS_ONLY'
                        }
                
                return {
                    'valid': True,
                    'discount': {
                        'id': str(discount.id),
                        'code': discount.code,
                        'type': discount.discount_type,
                        'value': float(discount.discount_value),
                        'description': discount.description
                    }
                }
                
            except Exception as e:
                logger.error(f"Error validating discount code: {e}")
                return {
                    'valid': False,
                    'error': 'Error validating discount code',
                    'error_code': 'VALIDATION_ERROR'
                } 
   def calculate_discount(self, original_amount_cents: int, discount_code: str, 
                          user_id: str, tier_name: str) -> Dict:
        """Calculate the discount amount for a subscription"""
        with get_db() as db:
            try:
                # Validate discount code first
                validation = self.validate_discount_code(discount_code, user_id, tier_name)
                if not validation['valid']:
                    return validation
                
                discount_info = validation['discount']
                discount_type = discount_info['type']
                discount_value = Decimal(str(discount_info['value']))
                
                # Calculate discount amount
                if discount_type == 'percentage':
                    discount_amount_cents = int((original_amount_cents * discount_value) / 100)
                elif discount_type == 'fixed_amount':
                    discount_amount_cents = int(discount_value * 100)  # Convert to cents
                elif discount_type == 'free_trial':
                    # Free trial extends the subscription period
                    discount_amount_cents = 0
                    trial_days = int(discount_value)
                else:
                    return {
                        'valid': False,
                        'error': 'Unsupported discount type',
                        'error_code': 'UNSUPPORTED_TYPE'
                    }
                
                # Ensure discount doesn't exceed original amount
                discount_amount_cents = min(discount_amount_cents, original_amount_cents)
                final_amount_cents = original_amount_cents - discount_amount_cents
                
                # Check minimum purchase requirement
                discount = db.query(DiscountCode).filter_by(code=discount_code.upper()).first()
                if discount.requires_minimum_purchase:
                    min_purchase_cents = int(discount.requires_minimum_purchase * 100)
                    if original_amount_cents < min_purchase_cents:
                        return {
                            'valid': False,
                            'error': f'Minimum purchase of ${discount.requires_minimum_purchase:.2f} required',
                            'error_code': 'MINIMUM_PURCHASE_REQUIRED'
                        }
                
                return {
                    'valid': True,
                    'discount_applied': {
                        'code': discount_code.upper(),
                        'type': discount_type,
                        'original_amount_cents': original_amount_cents,
                        'discount_amount_cents': discount_amount_cents,
                        'final_amount_cents': final_amount_cents,
                        'savings_percentage': round((discount_amount_cents / original_amount_cents) * 100, 2),
                        'trial_days': trial_days if discount_type == 'free_trial' else 0
                    }
                }
                
            except Exception as e:
                logger.error(f"Error calculating discount: {e}")
                return {
                    'valid': False,
                    'error': 'Error calculating discount',
                    'error_code': 'CALCULATION_ERROR'
                }
    
    def apply_discount(self, discount_code: str, user_id: str, subscription_id: str,
                      original_amount_cents: int, final_amount_cents: int, 
                      tier_name: str, context: str = 'new_subscription') -> Dict:
        """Apply and record discount usage"""
        with get_db() as db:
            try:
                # Get discount code
                discount = db.query(DiscountCode).filter_by(
                    code=discount_code.upper(),
                    is_active=True
                ).first()
                
                if not discount:
                    return {'success': False, 'error': 'Discount code not found'}
                
                # Create usage record
                usage = DiscountUsage(
                    discount_code_id=discount.id,
                    user_id=user_id,
                    subscription_id=subscription_id,
                    original_amount_cents=original_amount_cents,
                    discount_amount_cents=original_amount_cents - final_amount_cents,
                    final_amount_cents=final_amount_cents,
                    subscription_tier=tier_name,
                    usage_context=context
                )
                db.add(usage)
                
                # Update discount usage count
                discount.current_uses += 1
                
                # Update campaign usage if applicable
                if discount.campaign:
                    discount.campaign.current_total_uses += 1
                
                db.commit()
                
                return {
                    'success': True,
                    'usage_id': str(usage.id),
                    'discount_applied': original_amount_cents - final_amount_cents
                }
                
            except Exception as e:
                db.rollback()
                logger.error(f"Error applying discount: {e}")
                return {'success': False, 'error': str(e)}