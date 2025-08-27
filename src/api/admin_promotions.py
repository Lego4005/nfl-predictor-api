"""
Admin Promotional Management API
Allows admins to create and manage discount codes, campaigns, and offers
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from pydantic import BaseModel, Field
import logging

from ..auth.middleware import get_current_user
from ..promotions.service import PromotionalService
from ..promotions.models import (
    PromotionalCampaign, DiscountCode, SubscriptionOffer, 
    DiscountUsage, OfferRedemption
)
from ..database.connection import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/promotions", tags=["admin-promotions"])

# Request Models
class CreateCampaignRequest(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    campaign_type: str = Field(..., regex="^(seasonal|launch|retention|acquisition)$")
    start_date: datetime
    end_date: datetime
    max_total_uses: Optional[int] = None
    target_audience: str = Field("all", regex="^(new_users|existing_users|churned_users|all)$")
    target_tiers: List[str] = Field(default_factory=list)

class CreateDiscountCodeRequest(BaseModel):
    campaign_id: Optional[str] = None
    code: str = Field(..., max_length=50)
    description: Optional[str] = None
    discount_type: str = Field(..., regex="^(percentage|fixed_amount|free_trial|upgrade)$")
    discount_value: float = Field(..., gt=0)
    applicable_tiers: List[str] = Field(default_factory=list)
    minimum_tier: Optional[str] = None
    max_uses: Optional[int] = None
    max_uses_per_user: int = Field(1, ge=1)
    valid_from: datetime
    valid_until: datetime
    first_time_users_only: bool = False
    requires_minimum_purchase: Optional[float] = None
    stackable: bool = False
    is_public: bool = True

class CreateOfferRequest(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    offer_type: str = Field(..., regex="^(bundle|extended_trial|loyalty_discount|upgrade_incentive)$")
    base_tier: str = Field(..., regex="^(daily|weekly|monthly|season)$")
    offer_price_cents: int = Field(..., gt=0)
    bonus_features: List[str] = Field(default_factory=list)
    extended_duration_days: int = Field(0, ge=0)
    valid_from: datetime
    valid_until: datetime
    max_redemptions: Optional[int] = None
    target_user_types: List[str] = Field(default_factory=list)
    requires_code: bool = False
    associated_code: Optional[str] = None
    is_featured: bool = False

# Response Models
class CampaignResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    campaign_type: str
    start_date: datetime
    end_date: datetime
    is_active: bool
    current_total_uses: int
    max_total_uses: Optional[int]
    conversion_rate: Optional[float]
    total_revenue_impact: float

promotional_service = PromotionalService()

# Campaign Management
@router.post("/campaigns")
async def create_campaign(
    request: CreateCampaignRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new promotional campaign (admin only)"""
    try:
        # TODO: Add admin permission check
        
        with get_db() as db:
            campaign = PromotionalCampaign(
                name=request.name,
                description=request.description,
                campaign_type=request.campaign_type,
                start_date=request.start_date,
                end_date=request.end_date,
                max_total_uses=request.max_total_uses,
                target_audience=request.target_audience,
                target_tiers=request.target_tiers,
                created_by=current_user['user_id']
            )
            
            db.add(campaign)
            db.commit()
            db.refresh(campaign)
            
            return {
                "success": True,
                "campaign": {
                    "id": str(campaign.id),
                    "name": campaign.name,
                    "campaign_type": campaign.campaign_type,
                    "start_date": campaign.start_date.isoformat(),
                    "end_date": campaign.end_date.isoformat(),
                    "is_active": campaign.is_active
                },
                "message": "Campaign created successfully"
            }
            
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        raise HTTPException(status_code=500, detail="Failed to create campaign")

@router.get("/campaigns")
async def list_campaigns(
    current_user: dict = Depends(get_current_user),
    active_only: bool = Query(False),
    campaign_type: Optional[str] = Query(None),
    limit: int = Query(20, le=100)
):
    """List promotional campaigns"""
    try:
        with get_db() as db:
            query = db.query(PromotionalCampaign)
            
            if active_only:
                query = query.filter(PromotionalCampaign.is_active == True)
            
            if campaign_type:
                query = query.filter(PromotionalCampaign.campaign_type == campaign_type)
            
            campaigns = query.order_by(PromotionalCampaign.created_at.desc()).limit(limit).all()
            
            campaign_list = []
            for campaign in campaigns:
                campaign_list.append({
                    "id": str(campaign.id),
                    "name": campaign.name,
                    "description": campaign.description,
                    "campaign_type": campaign.campaign_type,
                    "start_date": campaign.start_date.isoformat(),
                    "end_date": campaign.end_date.isoformat(),
                    "is_active": campaign.is_active,
                    "current_total_uses": campaign.current_total_uses,
                    "max_total_uses": campaign.max_total_uses,
                    "conversion_rate": float(campaign.conversion_rate) if campaign.conversion_rate else None,
                    "total_revenue_impact": float(campaign.total_revenue_impact),
                    "discount_codes_count": len(campaign.discount_codes)
                })
            
            return {
                "success": True,
                "campaigns": campaign_list,
                "total": len(campaign_list)
            }
            
    except Exception as e:
        logger.error(f"Error listing campaigns: {e}")
        raise HTTPException(status_code=500, detail="Failed to list campaigns")# D
iscount Code Management
@router.post("/discount-codes")
async def create_discount_code(
    request: CreateDiscountCodeRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new discount code"""
    try:
        with get_db() as db:
            # Check if code already exists
            existing_code = db.query(DiscountCode).filter_by(code=request.code.upper()).first()
            if existing_code:
                raise HTTPException(status_code=400, detail="Discount code already exists")
            
            # Validate campaign if provided
            campaign = None
            if request.campaign_id:
                campaign = db.query(PromotionalCampaign).filter_by(id=request.campaign_id).first()
                if not campaign:
                    raise HTTPException(status_code=404, detail="Campaign not found")
            
            discount_code = DiscountCode(
                campaign_id=request.campaign_id,
                code=request.code.upper(),
                description=request.description,
                discount_type=request.discount_type,
                discount_value=Decimal(str(request.discount_value)),
                applicable_tiers=request.applicable_tiers,
                minimum_tier=request.minimum_tier,
                max_uses=request.max_uses,
                max_uses_per_user=request.max_uses_per_user,
                valid_from=request.valid_from,
                valid_until=request.valid_until,
                first_time_users_only=request.first_time_users_only,
                requires_minimum_purchase=Decimal(str(request.requires_minimum_purchase)) if request.requires_minimum_purchase else None,
                stackable=request.stackable,
                is_public=request.is_public,
                created_by=current_user['user_id']
            )
            
            db.add(discount_code)
            db.commit()
            db.refresh(discount_code)
            
            return {
                "success": True,
                "discount_code": {
                    "id": str(discount_code.id),
                    "code": discount_code.code,
                    "discount_type": discount_code.discount_type,
                    "discount_value": float(discount_code.discount_value),
                    "valid_from": discount_code.valid_from.isoformat(),
                    "valid_until": discount_code.valid_until.isoformat(),
                    "max_uses": discount_code.max_uses,
                    "current_uses": discount_code.current_uses,
                    "is_active": discount_code.is_active
                },
                "message": "Discount code created successfully"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating discount code: {e}")
        raise HTTPException(status_code=500, detail="Failed to create discount code")

@router.get("/discount-codes")
async def list_discount_codes(
    current_user: dict = Depends(get_current_user),
    active_only: bool = Query(False),
    campaign_id: Optional[str] = Query(None),
    discount_type: Optional[str] = Query(None),
    limit: int = Query(50, le=200)
):
    """List discount codes"""
    try:
        with get_db() as db:
            query = db.query(DiscountCode)
            
            if active_only:
                query = query.filter(DiscountCode.is_active == True)
            
            if campaign_id:
                query = query.filter(DiscountCode.campaign_id == campaign_id)
            
            if discount_type:
                query = query.filter(DiscountCode.discount_type == discount_type)
            
            codes = query.order_by(DiscountCode.created_at.desc()).limit(limit).all()
            
            code_list = []
            for code in codes:
                code_list.append({
                    "id": str(code.id),
                    "code": code.code,
                    "description": code.description,
                    "discount_type": code.discount_type,
                    "discount_value": float(code.discount_value),
                    "applicable_tiers": code.applicable_tiers,
                    "max_uses": code.max_uses,
                    "current_uses": code.current_uses,
                    "valid_from": code.valid_from.isoformat(),
                    "valid_until": code.valid_until.isoformat(),
                    "is_active": code.is_active,
                    "is_public": code.is_public,
                    "conversion_rate": float(code.conversion_rate) if code.conversion_rate else None,
                    "total_revenue_impact": float(code.total_revenue_impact),
                    "campaign_name": code.campaign.name if code.campaign else None
                })
            
            return {
                "success": True,
                "discount_codes": code_list,
                "total": len(code_list)
            }
            
    except Exception as e:
        logger.error(f"Error listing discount codes: {e}")
        raise HTTPException(status_code=500, detail="Failed to list discount codes")

@router.put("/discount-codes/{code_id}/toggle")
async def toggle_discount_code(
    code_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Toggle discount code active status"""
    try:
        with get_db() as db:
            discount_code = db.query(DiscountCode).filter_by(id=code_id).first()
            if not discount_code:
                raise HTTPException(status_code=404, detail="Discount code not found")
            
            discount_code.is_active = not discount_code.is_active
            db.commit()
            
            return {
                "success": True,
                "code": discount_code.code,
                "is_active": discount_code.is_active,
                "message": f"Discount code {'activated' if discount_code.is_active else 'deactivated'}"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling discount code: {e}")
        raise HTTPException(status_code=500, detail="Failed to toggle discount code")

# Subscription Offers
@router.post("/offers")
async def create_subscription_offer(
    request: CreateOfferRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new subscription offer"""
    try:
        with get_db() as db:
            # Calculate original price based on tier
            tier_prices = {
                'daily': 1299,    # $12.99
                'weekly': 2999,   # $29.99
                'monthly': 9999,  # $99.99
                'season': 29999   # $299.99
            }
            
            original_price_cents = tier_prices.get(request.base_tier, 0)
            if original_price_cents == 0:
                raise HTTPException(status_code=400, detail="Invalid base tier")
            
            savings_cents = original_price_cents - request.offer_price_cents
            savings_percentage = (savings_cents / original_price_cents) * 100
            
            offer = SubscriptionOffer(
                name=request.name,
                description=request.description,
                offer_type=request.offer_type,
                original_price_cents=original_price_cents,
                offer_price_cents=request.offer_price_cents,
                savings_cents=savings_cents,
                savings_percentage=Decimal(str(savings_percentage)),
                base_tier=request.base_tier,
                bonus_features=request.bonus_features,
                extended_duration_days=request.extended_duration_days,
                valid_from=request.valid_from,
                valid_until=request.valid_until,
                max_redemptions=request.max_redemptions,
                target_user_types=request.target_user_types,
                requires_code=request.requires_code,
                associated_code=request.associated_code,
                is_featured=request.is_featured,
                created_by=current_user['user_id']
            )
            
            db.add(offer)
            db.commit()
            db.refresh(offer)
            
            return {
                "success": True,
                "offer": {
                    "id": str(offer.id),
                    "name": offer.name,
                    "offer_type": offer.offer_type,
                    "base_tier": offer.base_tier,
                    "original_price": original_price_cents / 100,
                    "offer_price": request.offer_price_cents / 100,
                    "savings_percentage": float(savings_percentage),
                    "valid_from": offer.valid_from.isoformat(),
                    "valid_until": offer.valid_until.isoformat(),
                    "is_featured": offer.is_featured
                },
                "message": "Subscription offer created successfully"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subscription offer: {e}")
        raise HTTPException(status_code=500, detail="Failed to create subscription offer")