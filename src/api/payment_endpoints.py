"""
Payment and Subscription API Endpoints
Handles subscription creation, management, and webhook processing
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel, EmailStr
from decimal import Decimal
import logging

from ..auth.middleware import get_current_user
from ..payments.payment_service import payment_service, PaymentProcessor
from ..database.connection import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

# Request/Response Models
class CreateSubscriptionRequest(BaseModel):
    plan_name: str  # 'daily', 'weekly', 'monthly', 'season'
    payment_data: Dict[str, Any]  # Payment method details
    referral_code: Optional[str] = None

class CancelSubscriptionRequest(BaseModel):
    immediate: bool = False

class UpgradeSubscriptionRequest(BaseModel):
    new_plan: str

class SubscriptionResponse(BaseModel):
    success: bool
    subscription_id: Optional[str] = None
    customer_vault_id: Optional[str] = None
    transaction_id: Optional[str] = None
    amount_cents: Optional[int] = None
    plan: Optional[str] = None
    expires_at: Optional[str] = None
    processor_used: Optional[str] = None
    error: Optional[str] = None

@router.get("/pricing")
async def get_pricing():
    """Get pricing information for all subscription plans"""
    try:
        pricing = payment_service.get_pricing_info()
        return {"success": True, "pricing": pricing}
    except Exception as e:
        logger.error(f"Pricing fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch pricing")

@router.post("/subscribe", response_model=SubscriptionResponse)
async def create_subscription(
    request: CreateSubscriptionRequest,
    current_user: dict = Depends(get_current_user),
    client_ip: str = Header(None, alias="X-Forwarded-For")
):
    """Create new subscription for user"""
    try:
        result = await payment_service.create_subscription(
            user_id=current_user["user_id"],
            payment_data=request.payment_data,
            plan_name=request.plan_name,
            referral_code=request.referral_code,
            ip_address=client_ip
        )
        
        if result["success"]:
            return SubscriptionResponse(**result)
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Subscription creation failed"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscription creation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/subscription")
async def get_current_subscription(current_user: dict = Depends(get_current_user)):
    """Get user's current subscription"""
    try:
        subscription = await payment_service.get_user_subscription(current_user["user_id"])
        
        if subscription:
            return {"success": True, "subscription": subscription}
        else:
            return {"success": True, "subscription": None}
            
    except Exception as e:
        logger.error(f"Subscription fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch subscription")

@router.post("/subscription/cancel")
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Cancel user's subscription"""
    try:
        # Get current subscription
        subscription = await payment_service.get_user_subscription(current_user["user_id"])
        if not subscription:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        result = await payment_service.cancel_subscription(
            user_id=current_user["user_id"],
            subscription_id=subscription["id"],
            immediate=request.immediate
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Cancellation failed"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscription cancellation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/subscription/upgrade")
async def upgrade_subscription(
    request: UpgradeSubscriptionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Upgrade user's subscription"""
    try:
        result = await payment_service.upgrade_subscription(
            user_id=current_user["user_id"],
            new_plan=request.new_plan
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Upgrade failed"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscription upgrade failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/subscription/features/{feature}")
async def check_feature_access(
    feature: str,
    current_user: dict = Depends(get_current_user)
):
    """Check if user has access to specific feature"""
    try:
        subscription = await payment_service.get_user_subscription(current_user["user_id"])
        has_access = payment_service.has_feature_access(subscription, feature)
        
        return {
            "success": True,
            "feature": feature,
            "has_access": has_access,
            "subscription_tier": subscription["tier"] if subscription else None
        }
        
    except Exception as e:
        logger.error(f"Feature access check failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to check feature access")

@router.post("/webhooks/nmi")
async def nmi_webhook(request: Request):
    """Handle NMI webhook events"""
    try:
        payload = await request.body()
        signature = request.headers.get("X-NMI-Signature", "")
        
        result = await payment_service.handle_webhook(
            payload=payload.decode('utf-8'),
            signature=signature,
            processor=PaymentProcessor.NMI
        )
        
        if result["success"]:
            return JSONResponse(content={"status": "success"}, status_code=200)
        else:
            logger.error(f"NMI webhook failed: {result.get('error')}")
            return JSONResponse(content={"status": "error"}, status_code=400)
            
    except Exception as e:
        logger.error(f"NMI webhook processing failed: {e}")
        return JSONResponse(content={"status": "error"}, status_code=500)

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    try:
        payload = await request.body()
        signature = request.headers.get("Stripe-Signature", "")
        
        result = await payment_service.handle_webhook(
            payload=payload.decode('utf-8'),
            signature=signature,
            processor=PaymentProcessor.STRIPE
        )
        
        if result["success"]:
            return JSONResponse(content={"status": "success"}, status_code=200)
        else:
            logger.error(f"Stripe webhook failed: {result.get('error')}")
            return JSONResponse(content={"status": "error"}, status_code=400)
            
    except Exception as e:
        logger.error(f"Stripe webhook processing failed: {e}")
        return JSONResponse(content={"status": "error"}, status_code=500)

@router.get("/analytics")
async def get_subscription_analytics(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """Get subscription analytics (admin only)"""
    try:
        # Check if user is admin (you'll need to implement this check)
        # For now, we'll allow all authenticated users
        
        analytics = await payment_service.get_subscription_analytics(days=days)
        return {"success": True, "analytics": analytics}
        
    except Exception as e:
        logger.error(f"Analytics fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")

@router.post("/process-renewals")
async def process_renewals(current_user: dict = Depends(get_current_user)):
    """Process subscription renewals (admin only - typically called by scheduler)"""
    try:
        # This should be restricted to admin users or system processes
        result = await payment_service.process_subscription_renewals()
        return result
        
    except Exception as e:
        logger.error(f"Renewal processing failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process renewals")

@router.get("/refund/{transaction_id}")
async def process_refund(
    transaction_id: str,
    amount_cents: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """Process refund for transaction (admin only)"""
    try:
        # This should be restricted to admin users
        result = await payment_service.process_refund(
            transaction_id=transaction_id,
            amount=Decimal(amount_cents / 100) if amount_cents else None,
            processor=PaymentProcessor.NMI  # Default to NMI
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Refund processing failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to process refund")