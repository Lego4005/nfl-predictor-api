"""
Subscription API Endpoints
Implements the specific endpoints required by Task 3.3
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, Field
from decimal import Decimal
import logging
from datetime import datetime

from ..auth.middleware import get_current_user
from ..payments.payment_service import payment_service, PaymentProcessor
from ..database.connection import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/subscriptions", tags=["subscriptions"])

# Request/Response Models
class SubscriptionPackage(BaseModel):
    """Subscription package information"""
    name: str
    display_name: str
    price: float
    duration: str
    features: List[str]
    savings: Optional[str] = None
    recommended: bool = False

class PurchaseSubscriptionRequest(BaseModel):
    """Request model for purchasing subscription"""
    package_name: str = Field(..., description="Package name: daily, weekly, monthly, season")
    payment_method: Dict[str, Any] = Field(..., description="Payment method details")
    referral_code: Optional[str] = Field(None, description="Optional referral code")
    billing_address: Optional[Dict[str, str]] = Field(None, description="Billing address")

class CurrentSubscriptionResponse(BaseModel):
    """Current subscription information"""
    id: str
    package: str
    display_name: str
    status: str
    starts_at: str
    expires_at: Optional[str]
    auto_renew: bool
    features: List[str]
    amount_paid: float
    next_billing_date: Optional[str] = None

class CancelSubscriptionRequest(BaseModel):
    """Request model for cancelling subscription"""
    reason: Optional[str] = Field(None, description="Cancellation reason")
    immediate: bool = Field(False, description="Cancel immediately or at period end")

@router.get("/packages", response_model=Dict[str, Any])
async def get_subscription_packages():
    """
    Get all available subscription packages
    
    Returns:
        Dict containing all subscription packages with pricing and features
    """
    try:
        # Get pricing information from payment service
        pricing_info = payment_service.get_pricing_info()
        
        packages = []
        for package_name, package_data in pricing_info.items():
            # Calculate savings for each package
            savings_info = payment_service.calculate_savings(package_name)
            
            package = SubscriptionPackage(
                name=package_name,
                display_name=package_data['name'],
                price=package_data['price'],
                duration=package_data['duration'],
                features=package_data['features'],
                savings=package_data.get('savings'),
                recommended=(package_name == 'monthly')  # Mark monthly as recommended
            )
            packages.append(package.dict())
        
        # Add package comparison data
        comparison = {
            'daily_vs_weekly': f"Save ${(12.99 * 7 - 29.99):.2f} with weekly",
            'weekly_vs_monthly': f"Save ${(29.99 * 4.3 - 99.99):.2f} with monthly", 
            'monthly_vs_season': f"Save ${(99.99 * 6 - 299.99):.2f} with season"
        }
        
        return {
            "success": True,
            "packages": packages,
            "comparison": comparison,
            "currency": "USD",
            "tax_note": "Prices shown exclude applicable taxes"
        }
        
    except Exception as e:
        logger.error(f"Failed to get subscription packages: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve subscription packages")

@router.post("/purchase", response_model=Dict[str, Any])
async def purchase_subscription(
    request: PurchaseSubscriptionRequest,
    current_user: dict = Depends(get_current_user),
    client_ip: str = Header(None, alias="X-Forwarded-For"),
    user_agent: str = Header(None, alias="User-Agent")
):
    """
    Purchase a new subscription
    
    Args:
        request: Purchase request with package and payment details
        current_user: Authenticated user information
        client_ip: Client IP address for fraud detection
        user_agent: User agent for device tracking
    
    Returns:
        Dict containing subscription creation result
    """
    try:
        # Validate package name
        valid_packages = ['daily', 'weekly', 'monthly', 'season']
        if request.package_name not in valid_packages:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid package. Must be one of: {', '.join(valid_packages)}"
            )
        
        # Check if user already has active subscription
        existing_subscription = await payment_service.get_user_subscription(current_user["user_id"])
        if existing_subscription and existing_subscription['status'] in ['active', 'trial']:
            raise HTTPException(
                status_code=409,
                detail="User already has an active subscription. Please cancel current subscription first."
            )
        
        # Create subscription
        result = await payment_service.create_subscription(
            user_id=current_user["user_id"],
            payment_data=request.payment_method,
            plan_name=request.package_name,
            referral_code=request.referral_code,
            ip_address=client_ip
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": "Subscription created successfully",
                "subscription": {
                    "id": result["subscription_id"],
                    "package": result["plan"],
                    "amount_paid": result["amount_cents"] / 100,
                    "expires_at": result.get("expires_at"),
                    "processor": result["processor_used"]
                },
                "next_steps": [
                    "Your subscription is now active",
                    "Access premium features immediately",
                    "Check your email for receipt and details"
                ]
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Subscription creation failed")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscription purchase failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during subscription purchase")

@router.get("/current", response_model=Dict[str, Any])
async def get_current_subscription(current_user: dict = Depends(get_current_user)):
    """
    Get user's current active subscription
    
    Args:
        current_user: Authenticated user information
    
    Returns:
        Dict containing current subscription details or null if no active subscription
    """
    try:
        subscription = await payment_service.get_user_subscription(current_user["user_id"])
        
        if not subscription:
            return {
                "success": True,
                "subscription": None,
                "message": "No active subscription found",
                "available_packages": "/api/v1/subscriptions/packages"
            }
        
        # Format subscription data
        current_sub = CurrentSubscriptionResponse(
            id=subscription["id"],
            package=subscription["tier"],
            display_name=subscription["display_name"],
            status=subscription["status"],
            starts_at=subscription["starts_at"],
            expires_at=subscription.get("expires_at"),
            auto_renew=subscription["auto_renew"],
            features=subscription["features"],
            amount_paid=subscription["amount_paid_cents"] / 100
        )
        
        # Add additional context
        response_data = {
            "success": True,
            "subscription": current_sub.dict(),
            "billing_info": {
                "next_billing_date": subscription.get("expires_at") if subscription["auto_renew"] else None,
                "billing_cycle": subscription["tier"],
                "auto_renew_enabled": subscription["auto_renew"]
            }
        }
        
        # Add upgrade suggestions if applicable
        if subscription["tier"] in ['daily', 'weekly']:
            response_data["upgrade_suggestions"] = {
                "message": "Upgrade to save money on longer subscriptions",
                "recommendations": [
                    {"package": "monthly", "savings": "Save up to $289.71 vs weekly"},
                    {"package": "season", "savings": "Save up to $299.96 vs monthly"}
                ]
            }
        
        return response_data
        
    except Exception as e:
        logger.error(f"Failed to get current subscription: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve subscription information")

@router.post("/cancel", response_model=Dict[str, Any])
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Cancel user's current subscription
    
    Args:
        request: Cancellation request with reason and timing
        current_user: Authenticated user information
    
    Returns:
        Dict containing cancellation result
    """
    try:
        # Get current subscription
        subscription = await payment_service.get_user_subscription(current_user["user_id"])
        if not subscription:
            raise HTTPException(status_code=404, detail="No active subscription found to cancel")
        
        if subscription['status'] not in ['active', 'trial']:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot cancel subscription with status: {subscription['status']}"
            )
        
        # Cancel subscription
        result = await payment_service.cancel_subscription(
            user_id=current_user["user_id"],
            subscription_id=subscription["id"],
            immediate=request.immediate
        )
        
        if result["success"]:
            cancellation_message = (
                "Subscription cancelled immediately" if request.immediate 
                else f"Subscription will end on {result.get('expires_at', 'the current billing period end')}"
            )
            
            return {
                "success": True,
                "message": cancellation_message,
                "cancellation": {
                    "cancelled_at": datetime.utcnow().isoformat(),
                    "effective_date": result.get("expires_at"),
                    "immediate": request.immediate,
                    "reason": request.reason,
                    "refund_eligible": request.immediate and subscription["tier"] in ["monthly", "season"]
                },
                "next_steps": [
                    "You'll retain access until the end of your billing period" if not request.immediate else "Access has been terminated immediately",
                    "You can resubscribe at any time",
                    "Contact support if you need assistance"
                ]
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Cancellation failed")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Subscription cancellation failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during cancellation")

@router.get("/history", response_model=Dict[str, Any])
async def get_subscription_history(
    current_user: dict = Depends(get_current_user),
    limit: int = 10
):
    """
    Get user's subscription history
    
    Args:
        current_user: Authenticated user information
        limit: Maximum number of records to return
    
    Returns:
        Dict containing subscription history
    """
    try:
        # This would typically query the database for historical subscriptions
        # For now, we'll return the current subscription as history
        current_subscription = await payment_service.get_user_subscription(current_user["user_id"])
        
        history = []
        if current_subscription:
            history.append({
                "id": current_subscription["id"],
                "package": current_subscription["tier"],
                "status": current_subscription["status"],
                "started_at": current_subscription["starts_at"],
                "ended_at": current_subscription.get("expires_at"),
                "amount_paid": current_subscription["amount_paid_cents"] / 100
            })
        
        return {
            "success": True,
            "history": history,
            "total_count": len(history),
            "total_spent": sum(item["amount_paid"] for item in history)
        }
        
    except Exception as e:
        logger.error(f"Failed to get subscription history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve subscription history")

@router.get("/features", response_model=Dict[str, Any])
async def get_subscription_features(current_user: dict = Depends(get_current_user)):
    """
    Get features available to user based on their subscription
    
    Args:
        current_user: Authenticated user information
    
    Returns:
        Dict containing available features and access levels
    """
    try:
        subscription = await payment_service.get_user_subscription(current_user["user_id"])
        
        # Define all possible features
        all_features = {
            'basic_predictions': 'Basic game predictions',
            'real_time_predictions': 'Real-time prediction updates',
            'basic_props': 'Basic player props',
            'full_props': 'Full player props suite',
            'live_accuracy': 'Live accuracy tracking',
            'email_alerts': 'Email notifications',
            'basic_analytics': 'Basic performance analytics',
            'advanced_analytics': 'Advanced analytics dashboard',
            'data_export': 'Data export (CSV/PDF)',
            'playoff_predictions': 'Playoff predictions',
            'priority_support': 'Priority customer support',
            'api_access': 'API access for developers'
        }
        
        if not subscription or subscription['status'] not in ['active', 'trial']:
            # Free tier features
            available_features = ['basic_predictions', 'live_accuracy']
        else:
            available_features = subscription.get('features', [])
        
        # Build feature access map
        feature_access = {}
        for feature_key, feature_name in all_features.items():
            feature_access[feature_key] = {
                'name': feature_name,
                'available': feature_key in available_features,
                'tier_required': _get_minimum_tier_for_feature(feature_key)
            }
        
        return {
            "success": True,
            "current_tier": subscription["tier"] if subscription else "free",
            "features": feature_access,
            "upgrade_info": {
                "message": "Upgrade your subscription to unlock more features",
                "upgrade_url": "/api/v1/subscriptions/packages"
            } if subscription and subscription["tier"] in ["daily", "weekly"] else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get subscription features: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve feature information")

def _get_minimum_tier_for_feature(feature: str) -> str:
    """Get the minimum subscription tier required for a feature"""
    feature_tiers = {
        'basic_predictions': 'free',
        'live_accuracy': 'free',
        'real_time_predictions': 'daily',
        'basic_props': 'daily',
        'email_alerts': 'weekly',
        'basic_analytics': 'weekly',
        'full_props': 'monthly',
        'advanced_analytics': 'monthly',
        'data_export': 'monthly',
        'playoff_predictions': 'season',
        'priority_support': 'season',
        'api_access': 'season'
    }
    return feature_tiers.get(feature, 'season')

@router.get("/status", response_model=Dict[str, Any])
async def get_subscription_status(current_user: dict = Depends(get_current_user)):
    """
    Get detailed subscription status including billing and access information
    
    Args:
        current_user: Authenticated user information
    
    Returns:
        Dict containing comprehensive subscription status
    """
    try:
        subscription = await payment_service.get_user_subscription(current_user["user_id"])
        
        if not subscription:
            return {
                "success": True,
                "status": "no_subscription",
                "message": "No active subscription",
                "access_level": "free",
                "trial_available": True,
                "recommendations": [
                    "Start with our 7-day free trial",
                    "Choose the plan that fits your needs",
                    "Cancel anytime with no commitment"
                ]
            }
        
        # Calculate days remaining
        days_remaining = None
        if subscription.get("expires_at"):
            expires_at = datetime.fromisoformat(subscription["expires_at"].replace('Z', '+00:00'))
            days_remaining = max(0, (expires_at - datetime.utcnow()).days)
        
        status_info = {
            "success": True,
            "status": subscription["status"],
            "subscription_id": subscription["id"],
            "package": subscription["tier"],
            "display_name": subscription["display_name"],
            "access_level": subscription["tier"],
            "billing": {
                "amount_paid": subscription["amount_paid_cents"] / 100,
                "currency": "USD",
                "auto_renew": subscription["auto_renew"],
                "next_billing_date": subscription.get("expires_at") if subscription["auto_renew"] else None,
                "days_remaining": days_remaining
            },
            "access": {
                "features_count": len(subscription["features"]),
                "features": subscription["features"],
                "unlimited_access": subscription["tier"] == "season"
            }
        }
        
        # Add warnings or notifications
        if days_remaining is not None:
            if days_remaining <= 3:
                status_info["notifications"] = [
                    f"Your subscription expires in {days_remaining} days",
                    "Renew now to continue uninterrupted access"
                ]
            elif days_remaining <= 7:
                status_info["notifications"] = [
                    f"Your subscription expires in {days_remaining} days"
                ]
        
        return status_info
        
    except Exception as e:
        logger.error(f"Failed to get subscription status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve subscription status")