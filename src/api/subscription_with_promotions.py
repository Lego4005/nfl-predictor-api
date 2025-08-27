"""
Enhanced Subscription Endpoints with Promotional Integration
Integrates discount codes and offers with subscription purchases
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Optional
from pydantic import BaseModel
import logging

from ..auth.middleware import get_current_user
from ..promotions.service import PromotionalService
from ..payments.payment_service import payment_service
from ..database.connection import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/subscriptions", tags=["enhanced-subscriptions"])

# Enhanced Request Models
class EnhancedPurchaseRequest(BaseModel):
    package_name: str
    payment_method: Dict
    discount_code: Optional[str] = None
    offer_id: Optional[str] = None
    referral_code: Optional[str] = None

promotional_service = PromotionalService()

@router.post("/purchase-with-promotions")
async def purchase_subscription_with_promotions(
    request: EnhancedPurchaseRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Purchase subscription with discount codes and promotional offers
    """
    try:
        # Get base pricing
        pricing_info = payment_service.get_pricing_info()
        package_info = pricing_info.get(request.package_name)
        
        if not package_info:
            raise HTTPException(status_code=400, detail="Invalid package name")
        
        original_amount_cents = int(package_info['price'] * 100)
        final_amount_cents = original_amount_cents
        applied_promotions = []
        
        # Apply discount code if provided
        if request.discount_code:
            discount_result = promotional_service.calculate_discount(
                original_amount_cents,
                request.discount_code,
                current_user['user_id'],
                request.package_name
            )
            
            if discount_result['valid']:
                discount_applied = discount_result['discount_applied']
                final_amount_cents = discount_applied['final_amount_cents']
                
                applied_promotions.append({
                    'type': 'discount_code',
                    'code': request.discount_code,
                    'discount_amount': discount_applied['discount_amount_cents'] / 100,
                    'savings_percentage': discount_applied['savings_percentage']
                })
            else:
                return {
                    'success': False,
                    'error': discount_result['error'],
                    'error_code': discount_result['error_code']
                }
        
        # Apply subscription offer if provided
        if request.offer_id:
            # TODO: Implement offer application logic
            pass
        
        # Create subscription with final pricing
        subscription_result = await payment_service.create_subscription(
            user_id=current_user['user_id'],
            payment_data=request.payment_method,
            plan_name=request.package_name,
            referral_code=request.referral_code
        )
        
        if not subscription_result['success']:
            return subscription_result
        
        # Record discount usage if discount was applied
        if request.discount_code and applied_promotions:
            usage_result = promotional_service.apply_discount(
                request.discount_code,
                current_user['user_id'],
                subscription_result['subscription_id'],
                original_amount_cents,
                final_amount_cents,
                request.package_name
            )
            
            if not usage_result['success']:
                logger.error(f"Failed to record discount usage: {usage_result['error']}")
        
        return {
            'success': True,
            'subscription': subscription_result,
            'pricing': {
                'original_amount': original_amount_cents / 100,
                'final_amount': final_amount_cents / 100,
                'total_savings': (original_amount_cents - final_amount_cents) / 100,
                'applied_promotions': applied_promotions
            },
            'message': 'Subscription created successfully with promotions applied!'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error purchasing subscription with promotions: {e}")
        raise HTTPException(status_code=500, detail="Failed to process subscription purchase")

@router.get("/pricing-with-promotions")
async def get_pricing_with_promotions(
    current_user: dict = Depends(get_current_user),
    discount_code: Optional[str] = None
):
    """
    Get subscription pricing with available promotions applied
    """
    try:
        base_pricing = payment_service.get_pricing_info()
        enhanced_pricing = {}
        
        for package_name, package_info in base_pricing.items():
            original_price = package_info['price']
            package_pricing = {
                'name': package_info['name'],
                'original_price': original_price,
                'final_price': original_price,
                'savings': 0,
                'savings_percentage': 0,
                'features': package_info['features'],
                'duration': package_info['duration'],
                'promotions_applied': []
            }
            
            # Apply discount code if provided
            if discount_code:
                discount_result = promotional_service.calculate_discount(
                    int(original_price * 100),
                    discount_code,
                    current_user['user_id'],
                    package_name
                )
                
                if discount_result['valid']:
                    discount_applied = discount_result['discount_applied']
                    package_pricing['final_price'] = discount_applied['final_amount_cents'] / 100
                    package_pricing['savings'] = discount_applied['discount_amount_cents'] / 100
                    package_pricing['savings_percentage'] = discount_applied['savings_percentage']
                    package_pricing['promotions_applied'].append({
                        'type': 'discount_code',
                        'code': discount_code,
                        'description': f"Save ${package_pricing['savings']:.2f}"
                    })
            
            enhanced_pricing[package_name] = package_pricing
        
        return {
            'success': True,
            'pricing': enhanced_pricing,
            'discount_code_applied': discount_code if discount_code else None,
            'message': 'Pricing calculated with available promotions'
        }
        
    except Exception as e:
        logger.error(f"Error getting pricing with promotions: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate promotional pricing")

@router.get("/available-promotions")
async def get_available_promotions(current_user: dict = Depends(get_current_user)):
    """
    Get all available promotions for the current user
    """
    try:
        # Get available offers (from promotions_public.py logic)
        with get_db() as db:
            from ..promotions.models import SubscriptionOffer, DiscountCode
            from datetime import datetime
            
            current_time = datetime.utcnow()
            
            # Get active offers
            offers = db.query(SubscriptionOffer).filter(
                SubscriptionOffer.is_active == True,
                SubscriptionOffer.valid_from <= current_time,
                SubscriptionOffer.valid_until >= current_time
            ).limit(5).all()
            
            # Get public discount codes (without revealing the actual codes)
            discount_hints = db.query(DiscountCode).filter(
                DiscountCode.is_active == True,
                DiscountCode.is_public == True,
                DiscountCode.valid_from <= current_time,
                DiscountCode.valid_until >= current_time
            ).limit(3).all()
            
            available_offers = []
            for offer in offers:
                available_offers.append({
                    'id': str(offer.id),
                    'name': offer.name,
                    'description': offer.description,
                    'offer_type': offer.offer_type,
                    'base_tier': offer.base_tier,
                    'savings_percentage': float(offer.savings_percentage),
                    'is_featured': offer.is_featured
                })
            
            discount_opportunities = []
            for discount in discount_hints:
                discount_opportunities.append({
                    'description': discount.description,
                    'discount_type': discount.discount_type,
                    'discount_value': float(discount.discount_value),
                    'applicable_tiers': discount.applicable_tiers or ['all'],
                    'hint': 'Check promotional emails or contact support for discount codes'
                })
            
            return {
                'success': True,
                'available_offers': available_offers,
                'discount_opportunities': discount_opportunities,
                'loyalty_info': {
                    'message': 'Subscribe for 6+ months to unlock loyalty discounts',
                    'tiers': {
                        'silver': '5% discount after 6 months',
                        'gold': '10% discount after 12 months',
                        'platinum': '15% discount after 24 months'
                    }
                }
            }
            
    except Exception as e:
        logger.error(f"Error getting available promotions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve available promotions")