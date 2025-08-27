"""
Public Promotional API Endpoints
Allows users to validate discount codes and view available offers
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel
import logging

from ..auth.middleware import get_current_user
from ..promotions.service import PromotionalService
from ..promotions.models import SubscriptionOffer, DiscountCode
from ..database.connection import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/promotions", tags=["promotions"])

# Request Models
class ValidateDiscountRequest(BaseModel):
    code: str
    tier: str  # Subscription tier to apply discount to

class ApplyDiscountRequest(BaseModel):
    code: str
    tier: str
    original_amount_cents: int

promotional_service = PromotionalService()

@router.post("/validate-discount")
async def validate_discount_code(
    request: ValidateDiscountRequest,
    current_user: dict = Depends(get_current_user)
):
    """Validate a discount code for the current user"""
    try:
        validation_result = promotional_service.validate_discount_code(
            request.code,
            current_user['user_id'],
            request.tier
        )
        
        if validation_result['valid']:
            return {
                "success": True,
                "valid": True,
                "discount": validation_result['discount'],
                "message": "Discount code is valid and can be applied"
            }
        else:
            return {
                "success": True,
                "valid": False,
                "error": validation_result['error'],
                "error_code": validation_result['error_code']
            }
            
    except Exception as e:
        logger.error(f"Error validating discount code: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate discount code")

@router.post("/calculate-discount")
async def calculate_discount_amount(
    request: ApplyDiscountRequest,
    current_user: dict = Depends(get_current_user)
):
    """Calculate the discount amount for a subscription"""
    try:
        calculation_result = promotional_service.calculate_discount(
            request.original_amount_cents,
            request.code,
            current_user['user_id'],
            request.tier
        )
        
        if calculation_result['valid']:
            discount_applied = calculation_result['discount_applied']
            return {
                "success": True,
                "valid": True,
                "pricing": {
                    "original_amount": request.original_amount_cents / 100,
                    "discount_amount": discount_applied['discount_amount_cents'] / 100,
                    "final_amount": discount_applied['final_amount_cents'] / 100,
                    "savings_percentage": discount_applied['savings_percentage'],
                    "discount_type": discount_applied['type'],
                    "trial_days": discount_applied.get('trial_days', 0)
                },
                "message": f"You save ${discount_applied['discount_amount_cents'] / 100:.2f} with this discount!"
            }
        else:
            return {
                "success": True,
                "valid": False,
                "error": calculation_result['error'],
                "error_code": calculation_result['error_code']
            }
            
    except Exception as e:
        logger.error(f"Error calculating discount: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate discount")

@router.get("/offers")
async def get_available_offers(
    current_user: dict = Depends(get_current_user),
    featured_only: bool = Query(False),
    offer_type: Optional[str] = Query(None)
):
    """Get available subscription offers for the current user"""
    try:
        with get_db() as db:
            current_time = datetime.utcnow()
            
            query = db.query(SubscriptionOffer).filter(
                SubscriptionOffer.is_active == True,
                SubscriptionOffer.valid_from <= current_time,
                SubscriptionOffer.valid_until >= current_time
            )
            
            if featured_only:
                query = query.filter(SubscriptionOffer.is_featured == True)
            
            if offer_type:
                query = query.filter(SubscriptionOffer.offer_type == offer_type)
            
            # Check if max redemptions reached
            query = query.filter(
                db.or_(
                    SubscriptionOffer.max_redemptions.is_(None),
                    SubscriptionOffer.current_redemptions < SubscriptionOffer.max_redemptions
                )
            )
            
            offers = query.order_by(SubscriptionOffer.savings_percentage.desc()).all()
            
            offer_list = []
            for offer in offers:
                # Check if user is eligible (simplified logic)
                user_eligible = True  # TODO: Add user eligibility logic
                
                if user_eligible:
                    offer_list.append({
                        "id": str(offer.id),
                        "name": offer.name,
                        "description": offer.description,
                        "offer_type": offer.offer_type,
                        "base_tier": offer.base_tier,
                        "pricing": {
                            "original_price": offer.original_price_cents / 100,
                            "offer_price": offer.offer_price_cents / 100,
                            "savings": offer.savings_cents / 100,
                            "savings_percentage": float(offer.savings_percentage)
                        },
                        "bonus_features": offer.bonus_features,
                        "extended_duration_days": offer.extended_duration_days,
                        "valid_until": offer.valid_until.isoformat(),
                        "is_featured": offer.is_featured,
                        "requires_code": offer.requires_code,
                        "associated_code": offer.associated_code if not offer.requires_code else None,
                        "redemptions_left": (offer.max_redemptions - offer.current_redemptions) if offer.max_redemptions else None
                    })
            
            return {
                "success": True,
                "offers": offer_list,
                "total": len(offer_list),
                "message": f"Found {len(offer_list)} available offers"
            }
            
    except Exception as e:
        logger.error(f"Error getting offers: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve offers")

@router.get("/offers/{offer_id}")
async def get_offer_details(
    offer_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get detailed information about a specific offer"""
    try:
        with get_db() as db:
            offer = db.query(SubscriptionOffer).filter_by(
                id=offer_id,
                is_active=True
            ).first()
            
            if not offer:
                raise HTTPException(status_code=404, detail="Offer not found or no longer available")
            
            # Check if offer is still valid
            current_time = datetime.utcnow()
            if current_time < offer.valid_from or current_time > offer.valid_until:
                raise HTTPException(status_code=410, detail="Offer has expired")
            
            # Check if max redemptions reached
            if offer.max_redemptions and offer.current_redemptions >= offer.max_redemptions:
                raise HTTPException(status_code=410, detail="Offer redemption limit reached")
            
            return {
                "success": True,
                "offer": {
                    "id": str(offer.id),
                    "name": offer.name,
                    "description": offer.description,
                    "offer_type": offer.offer_type,
                    "base_tier": offer.base_tier,
                    "pricing": {
                        "original_price": offer.original_price_cents / 100,
                        "offer_price": offer.offer_price_cents / 100,
                        "savings": offer.savings_cents / 100,
                        "savings_percentage": float(offer.savings_percentage)
                    },
                    "features": {
                        "base_features": f"All {offer.base_tier} subscription features",
                        "bonus_features": offer.bonus_features,
                        "extended_duration_days": offer.extended_duration_days
                    },
                    "validity": {
                        "valid_from": offer.valid_from.isoformat(),
                        "valid_until": offer.valid_until.isoformat(),
                        "days_remaining": (offer.valid_until - current_time).days
                    },
                    "availability": {
                        "max_redemptions": offer.max_redemptions,
                        "current_redemptions": offer.current_redemptions,
                        "redemptions_left": (offer.max_redemptions - offer.current_redemptions) if offer.max_redemptions else None
                    },
                    "requirements": {
                        "requires_code": offer.requires_code,
                        "associated_code": offer.associated_code if not offer.requires_code else "Code required",
                        "target_user_types": offer.target_user_types
                    }
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting offer details: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve offer details")

@router.get("/active-discounts")
async def get_active_discount_codes(
    current_user: dict = Depends(get_current_user),
    public_only: bool = Query(True)
):
    """Get list of currently active public discount codes"""
    try:
        with get_db() as db:
            current_time = datetime.utcnow()
            
            query = db.query(DiscountCode).filter(
                DiscountCode.is_active == True,
                DiscountCode.valid_from <= current_time,
                DiscountCode.valid_until >= current_time
            )
            
            if public_only:
                query = query.filter(DiscountCode.is_public == True)
            
            # Only show codes that haven't reached max usage
            query = query.filter(
                db.or_(
                    DiscountCode.max_uses.is_(None),
                    DiscountCode.current_uses < DiscountCode.max_uses
                )
            )
            
            codes = query.order_by(DiscountCode.discount_value.desc()).limit(10).all()
            
            code_list = []
            for code in codes:
                # Don't show the actual code for security, just the benefits
                code_list.append({
                    "id": str(code.id),
                    "description": code.description,
                    "discount_type": code.discount_type,
                    "discount_value": float(code.discount_value),
                    "discount_display": f"{code.discount_value}% off" if code.discount_type == 'percentage' else f"${code.discount_value} off",
                    "applicable_tiers": code.applicable_tiers if code.applicable_tiers else ["all"],
                    "valid_until": code.valid_until.isoformat(),
                    "days_remaining": (code.valid_until - current_time).days,
                    "first_time_users_only": code.first_time_users_only,
                    "usage_remaining": (code.max_uses - code.current_uses) if code.max_uses else "Unlimited"
                })
            
            return {
                "success": True,
                "active_discounts": code_list,
                "total": len(code_list),
                "message": "Contact support or check promotional emails for discount codes"
            }
            
    except Exception as e:
        logger.error(f"Error getting active discounts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve active discounts")