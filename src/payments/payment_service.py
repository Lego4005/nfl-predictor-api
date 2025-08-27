"""
Unified Payment Service
Supports NMI (primary) and Stripe (backup) payment processing
Integrates with database models for subscription management
"""

import os
import logging
from typing import Dict, Optional, Union, List
from decimal import Decimal
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .nmi_client import NMISubscriptionManager, NMIClient
from ..database.models import (
    User, Subscription, SubscriptionTier, Payment, 
    Referral, Affiliate, AuditLog
)
from ..database.connection import get_db

logger = logging.getLogger(__name__)

class PaymentProcessor(Enum):
    NMI = "nmi"
    STRIPE = "stripe"

class PaymentService:
    """Unified payment service supporting multiple processors with database integration"""
    
    def __init__(self):
        self.primary_processor = PaymentProcessor.NMI
        self.nmi_manager = NMISubscriptionManager()
        
        # Initialize Stripe as backup (optional)
        self.stripe_client = None
        if os.getenv('STRIPE_SECRET_KEY'):
            try:
                import stripe
                stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
                self.stripe_client = stripe
                logger.info("Stripe initialized as backup payment processor")
            except ImportError:
                logger.warning("Stripe not available (package not installed)")
    
    def _log_audit_event(self, db: Session, user_id: str, action: str, 
                        resource_type: str = None, resource_id: str = None, 
                        details: Dict = None, ip_address: str = None):
        """Log audit event for payment actions"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                ip_address=ip_address
            )
            db.add(audit_log)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
    
    def _get_or_create_subscription_tiers(self, db: Session) -> Dict[str, SubscriptionTier]:
        """Get or create subscription tiers"""
        tiers = {}
        
        tier_definitions = [
            {
                'name': 'free_trial',
                'display_name': '7-Day Free Trial',
                'price_cents': 0,
                'duration_days': 7,
                'features': ['basic_predictions', 'live_accuracy', 'email_alerts']
            },
            {
                'name': 'daily',
                'display_name': '1 Day Access',
                'price_cents': 1299,  # $12.99
                'duration_days': 1,
                'features': ['real_time_predictions', 'basic_props', 'live_accuracy']
            },
            {
                'name': 'weekly',
                'display_name': '1 Week Access',
                'price_cents': 2999,  # $29.99
                'duration_days': 7,
                'features': ['real_time_predictions', 'live_accuracy', 'email_alerts', 'basic_analytics']
            },
            {
                'name': 'monthly',
                'display_name': '1 Month Access',
                'price_cents': 9999,  # $99.99
                'duration_days': 30,
                'features': ['all_weekly_features', 'advanced_analytics', 'full_props', 'data_export']
            },
            {
                'name': 'season',
                'display_name': 'Full Season + Playoffs',
                'price_cents': 29999,  # $299.99
                'duration_days': 180,
                'features': ['all_monthly_features', 'playoff_predictions', 'priority_support', 'api_access']
            }
        ]
        
        for tier_def in tier_definitions:
            tier = db.query(SubscriptionTier).filter_by(name=tier_def['name']).first()
            if not tier:
                tier = SubscriptionTier(**tier_def)
                db.add(tier)
                db.commit()
                db.refresh(tier)
            tiers[tier_def['name']] = tier
        
        return tiers
    
    async def create_subscription(self, user_id: str, payment_data: Dict, 
                                plan_name: str, referral_code: str = None,
                                processor: Optional[PaymentProcessor] = None,
                                ip_address: str = None) -> Dict:
        """Create subscription with full database integration"""
        processor = processor or self.primary_processor
        
        with get_db() as db:
            try:
                # Get user and validate
                user = db.query(User).filter_by(id=user_id).first()
                if not user:
                    return {'success': False, 'error': 'User not found'}
                
                # Get subscription tiers
                tiers = self._get_or_create_subscription_tiers(db)
                tier = tiers.get(plan_name)
                if not tier:
                    return {'success': False, 'error': f'Invalid plan: {plan_name}'}
                
                # Check for existing active subscription
                existing_sub = db.query(Subscription).filter(
                    and_(
                        Subscription.user_id == user_id,
                        Subscription.status.in_(['active', 'trial']),
                        or_(
                            Subscription.expires_at.is_(None),
                            Subscription.expires_at > datetime.utcnow()
                        )
                    )
                ).first()
                
                if existing_sub:
                    return {'success': False, 'error': 'User already has active subscription'}
                
                # Process referral if provided
                affiliate = None
                if referral_code:
                    affiliate = db.query(Affiliate).filter_by(
                        referral_code=referral_code, 
                        is_active=True
                    ).first()
                
                # Prepare user data for payment processor
                user_data = {
                    'first_name': user.first_name or '',
                    'last_name': user.last_name or '',
                    'email': user.email,
                    'phone': user.phone or '',
                    'address': user.address or '',
                    'city': user.city or '',
                    'state': user.state or '',
                    'zip_code': user.zip_code or ''
                }
                
                # Process payment
                if processor == PaymentProcessor.NMI:
                    payment_result = await self._create_nmi_subscription_with_db(
                        db, user, tier, user_data, payment_data, affiliate, ip_address
                    )
                elif processor == PaymentProcessor.STRIPE and self.stripe_client:
                    payment_result = await self._create_stripe_subscription_with_db(
                        db, user, tier, user_data, payment_data, affiliate, ip_address
                    )
                else:
                    raise ValueError(f"Processor {processor.value} not available")
                
                return payment_result
                
            except Exception as e:
                logger.error(f"Subscription creation failed with {processor.value}: {e}")
                db.rollback()
                
                # Try backup processor if primary fails
                if processor == PaymentProcessor.NMI and self.stripe_client:
                    logger.info("Attempting fallback to Stripe...")
                    try:
                        return await self._create_stripe_subscription_with_db(
                            db, user, tier, user_data, payment_data, affiliate, ip_address
                        )
                    except Exception as backup_error:
                        logger.error(f"Backup processor also failed: {backup_error}")
                        db.rollback()
                
                return {
                    'success': False,
                    'error': str(e),
                    'processor_used': processor.value
                }
    
    async def _create_nmi_subscription_with_db(self, db: Session, user: User, tier: SubscriptionTier,
                                              user_data: Dict, payment_data: Dict, 
                                              affiliate: Optional[Affiliate] = None,
                                              ip_address: str = None) -> Dict:
        """Create subscription using NMI with database integration"""
        try:
            # Create NMI subscription
            nmi_result = await self.nmi_manager.create_subscription(
                user_data, payment_data, tier.name
            )
            
            if not nmi_result['success']:
                return nmi_result
            
            # Calculate subscription dates
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=tier.duration_days) if tier.duration_days else None
            
            # Create database subscription record
            subscription = Subscription(
                user_id=user.id,
                tier_id=tier.id,
                status='active',
                starts_at=start_date,
                expires_at=end_date,
                stripe_subscription_id=nmi_result.get('subscription_id'),  # Store NMI subscription ID
                stripe_customer_id=nmi_result.get('customer_vault_id'),    # Store NMI customer vault ID
                auto_renew=tier.name not in ['daily'],  # Daily is one-time
                amount_paid_cents=tier.price_cents
            )
            db.add(subscription)
            db.flush()  # Get subscription ID
            
            # Create payment record
            payment = Payment(
                user_id=user.id,
                subscription_id=subscription.id,
                stripe_payment_intent_id=nmi_result.get('transaction_id'),
                amount_cents=tier.price_cents,
                currency='USD',
                status='succeeded',
                payment_method='nmi',
                metadata={
                    'nmi_customer_vault_id': nmi_result.get('customer_vault_id'),
                    'nmi_subscription_id': nmi_result.get('subscription_id'),
                    'plan_name': tier.name
                }
            )
            db.add(payment)
            
            # Handle referral if applicable
            if affiliate:
                # Calculate commission (30% of first payment)
                commission_cents = int(tier.price_cents * affiliate.commission_rate)
                
                referral = Referral(
                    affiliate_id=affiliate.id,
                    referred_user_id=user.id,
                    referral_code=affiliate.referral_code,
                    conversion_date=datetime.utcnow(),
                    subscription_id=subscription.id,
                    commission_earned_cents=commission_cents,
                    status='converted',
                    click_data={'ip_address': ip_address}
                )
                db.add(referral)
                
                # Update affiliate stats
                affiliate.total_referrals += 1
                affiliate.pending_earnings_cents += commission_cents
                
            # Log audit event
            self._log_audit_event(
                db, str(user.id), 'subscription_created',
                'subscription', str(subscription.id),
                {
                    'tier': tier.name,
                    'amount_cents': tier.price_cents,
                    'processor': 'nmi',
                    'referral_code': affiliate.referral_code if affiliate else None
                },
                ip_address
            )
            
            db.commit()
            
            return {
                'success': True,
                'subscription_id': str(subscription.id),
                'customer_vault_id': nmi_result.get('customer_vault_id'),
                'nmi_subscription_id': nmi_result.get('subscription_id'),
                'transaction_id': nmi_result.get('transaction_id'),
                'amount_cents': tier.price_cents,
                'plan': tier.name,
                'expires_at': end_date.isoformat() if end_date else None,
                'processor_used': 'nmi'
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"NMI subscription creation failed: {e}")
            raise
    
    async def _create_stripe_subscription_with_db(self, db: Session, user: User, tier: SubscriptionTier,
                                                 user_data: Dict, payment_data: Dict,
                                                 affiliate: Optional[Affiliate] = None,
                                                 ip_address: str = None) -> Dict:
        """Create subscription using Stripe with database integration"""
        if not self.stripe_client:
            raise Exception("Stripe not configured")
        
        try:
            # Create Stripe customer
            customer = self.stripe_client.Customer.create(
                email=user_data['email'],
                name=f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip(),
                payment_method=payment_data['payment_method_id']
            )
            
            # Map plan names to Stripe price IDs
            stripe_prices = {
                'daily': os.getenv('STRIPE_DAILY_PRICE_ID'),
                'weekly': os.getenv('STRIPE_WEEKLY_PRICE_ID'),
                'monthly': os.getenv('STRIPE_MONTHLY_PRICE_ID'),
                'season': os.getenv('STRIPE_SEASON_PRICE_ID')
            }
            
            price_id = stripe_prices.get(tier.name)
            if not price_id:
                raise ValueError(f"Stripe price ID not configured for plan: {tier.name}")
            
            # Create Stripe subscription
            stripe_subscription = self.stripe_client.Subscription.create(
                customer=customer.id,
                items=[{'price': price_id}],
                payment_behavior='default_incomplete',
                expand=['latest_invoice.payment_intent']
            )
            
            # Calculate subscription dates
            start_date = datetime.utcnow()
            end_date = start_date + timedelta(days=tier.duration_days) if tier.duration_days else None
            
            # Create database subscription record
            subscription = Subscription(
                user_id=user.id,
                tier_id=tier.id,
                status='active',
                starts_at=start_date,
                expires_at=end_date,
                stripe_subscription_id=stripe_subscription.id,
                stripe_customer_id=customer.id,
                auto_renew=tier.name not in ['daily'],
                amount_paid_cents=tier.price_cents
            )
            db.add(subscription)
            db.flush()
            
            # Create payment record
            payment = Payment(
                user_id=user.id,
                subscription_id=subscription.id,
                stripe_payment_intent_id=stripe_subscription.latest_invoice.payment_intent.id,
                amount_cents=tier.price_cents,
                currency='USD',
                status='pending',  # Will be updated via webhook
                payment_method='stripe',
                metadata={
                    'stripe_customer_id': customer.id,
                    'stripe_subscription_id': stripe_subscription.id,
                    'plan_name': tier.name
                }
            )
            db.add(payment)
            
            # Handle referral if applicable
            if affiliate:
                commission_cents = int(tier.price_cents * affiliate.commission_rate)
                
                referral = Referral(
                    affiliate_id=affiliate.id,
                    referred_user_id=user.id,
                    referral_code=affiliate.referral_code,
                    subscription_id=subscription.id,
                    commission_earned_cents=commission_cents,
                    status='pending',  # Will be updated when payment succeeds
                    click_data={'ip_address': ip_address}
                )
                db.add(referral)
            
            # Log audit event
            self._log_audit_event(
                db, str(user.id), 'subscription_created',
                'subscription', str(subscription.id),
                {
                    'tier': tier.name,
                    'amount_cents': tier.price_cents,
                    'processor': 'stripe',
                    'referral_code': affiliate.referral_code if affiliate else None
                },
                ip_address
            )
            
            db.commit()
            
            return {
                'success': True,
                'subscription_id': str(subscription.id),
                'customer_id': customer.id,
                'stripe_subscription_id': stripe_subscription.id,
                'client_secret': stripe_subscription.latest_invoice.payment_intent.client_secret,
                'amount_cents': tier.price_cents,
                'plan': tier.name,
                'expires_at': end_date.isoformat() if end_date else None,
                'processor_used': 'stripe'
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Stripe subscription creation failed: {e}")
            raise
    
    async def cancel_subscription(self, subscription_id: str, processor: PaymentProcessor) -> bool:
        """Cancel subscription"""
        try:
            if processor == PaymentProcessor.NMI:
                return await self.nmi_manager.cancel_subscription(subscription_id)
            elif processor == PaymentProcessor.STRIPE and self.stripe_client:
                subscription = self.stripe_client.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
                return subscription.cancel_at_period_end
            else:
                raise ValueError(f"Processor {processor.value} not available")
                
        except Exception as e:
            logger.error(f"Subscription cancellation failed: {e}")
            return False
    
    async def process_refund(self, transaction_id: str, amount: Optional[Decimal] = None, 
                           processor: PaymentProcessor = PaymentProcessor.NMI) -> Dict:
        """Process refund"""
        try:
            if processor == PaymentProcessor.NMI:
                result = await self.nmi_manager.nmi_client.process_refund(transaction_id, amount)
                return {
                    'success': result.status == 'approved',
                    'refund_id': result.transaction_id,
                    'amount': result.amount,
                    'processor_used': 'nmi'
                }
            elif processor == PaymentProcessor.STRIPE and self.stripe_client:
                refund = self.stripe_client.Refund.create(
                    payment_intent=transaction_id,
                    amount=int(amount * 100) if amount else None  # Stripe uses cents
                )
                return {
                    'success': refund.status == 'succeeded',
                    'refund_id': refund.id,
                    'amount': Decimal(refund.amount) / 100,
                    'processor_used': 'stripe'
                }
            else:
                raise ValueError(f"Processor {processor.value} not available")
                
        except Exception as e:
            logger.error(f"Refund processing failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_pricing_info(self) -> Dict:
        """Get pricing information for all plans"""
        return {
            'daily': {
                'name': '1 Day Access',
                'price': 12.99,
                'duration': '1 day',
                'features': ['Real-time predictions', 'Basic props', 'Live accuracy'],
                'savings': None
            },
            'weekly': {
                'name': '1 Week Access',
                'price': 29.99,
                'duration': '7 days',
                'features': ['Real-time predictions', 'Live accuracy', 'Email alerts'],
                'savings': 'Save $61.94 vs daily'
            },
            'monthly': {
                'name': '1 Month Access',
                'price': 99.99,
                'duration': '30 days',
                'features': ['All weekly features', 'Advanced analytics', 'Full props'],
                'savings': 'Save $289.71 vs weekly'
            },
            'season': {
                'name': 'Full Season + Playoffs',
                'price': 299.99,
                'duration': '180 days',
                'features': ['All monthly features', 'Playoff predictions', 'Data export'],
                'savings': 'Save $299.96 vs monthly'
            }
        }
    
    def calculate_savings(self, plan_name: str) -> Dict:
        """Calculate savings compared to shorter plans"""
        pricing = self.get_pricing_info()
        plan = pricing.get(plan_name)
        
        if not plan:
            return {}
        
        savings = {}
        
        if plan_name == 'weekly':
            daily_cost = pricing['daily']['price'] * 7
            savings['vs_daily'] = daily_cost - plan['price']
            
        elif plan_name == 'monthly':
            weekly_cost = pricing['weekly']['price'] * 4.3  # ~4.3 weeks per month
            daily_cost = pricing['daily']['price'] * 30
            savings['vs_weekly'] = weekly_cost - plan['price']
            savings['vs_daily'] = daily_cost - plan['price']
            
        elif plan_name == 'season':
            monthly_cost = pricing['monthly']['price'] * 6  # 6 months
            weekly_cost = pricing['weekly']['price'] * 26  # ~26 weeks
            savings['vs_monthly'] = monthly_cost - plan['price']
            savings['vs_weekly'] = weekly_cost - plan['price']
        
        return savings
    
    async def handle_webhook(self, payload: str, signature: str, processor: PaymentProcessor) -> Dict:
        """Handle webhook from payment processor with database updates"""
        with get_db() as db:
            try:
                if processor == PaymentProcessor.NMI:
                    return await self._handle_nmi_webhook(db, payload, signature)
                elif processor == PaymentProcessor.STRIPE and self.stripe_client:
                    return await self._handle_stripe_webhook(db, payload, signature)
                else:
                    return {'success': False, 'error': f'Processor {processor.value} not available'}
                    
            except Exception as e:
                logger.error(f"Webhook handling failed: {e}")
                db.rollback()
                return {'success': False, 'error': str(e)}
    
    async def _handle_nmi_webhook(self, db: Session, payload: str, signature: str) -> Dict:
        """Handle NMI webhook events"""
        # Verify NMI webhook
        if not self.nmi_manager.nmi_client.verify_webhook(payload, signature):
            return {'success': False, 'error': 'Invalid signature'}
        
        # Parse NMI webhook data
        webhook_data = {}
        for line in payload.split('&'):
            if '=' in line:
                key, value = line.split('=', 1)
                webhook_data[key] = value
        
        event_type = webhook_data.get('type', 'unknown')
        logger.info(f"Processing NMI webhook: {event_type}")
        
        try:
            if event_type == 'recurring_payment_success':
                await self._handle_nmi_payment_success(db, webhook_data)
            elif event_type == 'recurring_payment_failed':
                await self._handle_nmi_payment_failed(db, webhook_data)
            elif event_type == 'subscription_cancelled':
                await self._handle_nmi_subscription_cancelled(db, webhook_data)
            elif event_type == 'refund_processed':
                await self._handle_nmi_refund(db, webhook_data)
            
            db.commit()
            return {
                'success': True,
                'processor': 'nmi',
                'event_type': event_type,
                'processed': True
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"NMI webhook processing failed: {e}")
            raise
    
    async def _handle_nmi_payment_success(self, db: Session, webhook_data: Dict):
        """Handle successful NMI payment"""
        subscription_id = webhook_data.get('subscription_id')
        transaction_id = webhook_data.get('transaction_id')
        amount = Decimal(webhook_data.get('amount', '0'))
        
        # Find subscription by NMI subscription ID
        subscription = db.query(Subscription).filter_by(
            stripe_subscription_id=subscription_id  # We store NMI ID in this field
        ).first()
        
        if subscription:
            # Create payment record
            payment = Payment(
                user_id=subscription.user_id,
                subscription_id=subscription.id,
                stripe_payment_intent_id=transaction_id,
                amount_cents=int(amount * 100),
                currency='USD',
                status='succeeded',
                payment_method='nmi',
                metadata=webhook_data
            )
            db.add(payment)
            
            # Extend subscription if recurring
            if subscription.auto_renew and subscription.tier.duration_days:
                subscription.expires_at = datetime.utcnow() + timedelta(days=subscription.tier.duration_days)
            
            # Update referral commission if applicable
            referral = db.query(Referral).filter_by(
                subscription_id=subscription.id,
                status='pending'
            ).first()
            
            if referral:
                referral.status = 'converted'
                referral.conversion_date = datetime.utcnow()
                
                # Update affiliate earnings
                affiliate = referral.affiliate
                affiliate.pending_earnings_cents += referral.commission_earned_cents
    
    async def _handle_nmi_payment_failed(self, db: Session, webhook_data: Dict):
        """Handle failed NMI payment"""
        subscription_id = webhook_data.get('subscription_id')
        
        subscription = db.query(Subscription).filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if subscription:
            # Create failed payment record
            payment = Payment(
                user_id=subscription.user_id,
                subscription_id=subscription.id,
                amount_cents=subscription.tier.price_cents,
                currency='USD',
                status='failed',
                payment_method='nmi',
                metadata=webhook_data
            )
            db.add(payment)
            
            # Mark subscription as past due
            subscription.status = 'past_due'
    
    async def _handle_nmi_subscription_cancelled(self, db: Session, webhook_data: Dict):
        """Handle NMI subscription cancellation"""
        subscription_id = webhook_data.get('subscription_id')
        
        subscription = db.query(Subscription).filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if subscription:
            subscription.status = 'cancelled'
            subscription.auto_renew = False
    
    async def _handle_nmi_refund(self, db: Session, webhook_data: Dict):
        """Handle NMI refund"""
        transaction_id = webhook_data.get('original_transaction_id')
        refund_amount = Decimal(webhook_data.get('refund_amount', '0'))
        
        # Find original payment
        payment = db.query(Payment).filter_by(
            stripe_payment_intent_id=transaction_id
        ).first()
        
        if payment:
            # Create refund payment record
            refund_payment = Payment(
                user_id=payment.user_id,
                subscription_id=payment.subscription_id,
                stripe_payment_intent_id=webhook_data.get('refund_transaction_id'),
                amount_cents=-int(refund_amount * 100),  # Negative for refund
                currency='USD',
                status='refunded',
                payment_method='nmi',
                metadata=webhook_data
            )
            db.add(refund_payment)
            
            # Update original payment status
            payment.status = 'refunded'
    
    async def _handle_stripe_webhook(self, db: Session, payload: str, signature: str) -> Dict:
        """Handle Stripe webhook events"""
        endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        event = self.stripe_client.Webhook.construct_event(
            payload, signature, endpoint_secret
        )
        
        event_type = event['type']
        logger.info(f"Processing Stripe webhook: {event_type}")
        
        try:
            if event_type == 'invoice.payment_succeeded':
                await self._handle_stripe_payment_success(db, event['data']['object'])
            elif event_type == 'invoice.payment_failed':
                await self._handle_stripe_payment_failed(db, event['data']['object'])
            elif event_type == 'customer.subscription.deleted':
                await self._handle_stripe_subscription_cancelled(db, event['data']['object'])
            elif event_type == 'charge.dispute.created':
                await self._handle_stripe_chargeback(db, event['data']['object'])
            
            db.commit()
            return {
                'success': True,
                'processor': 'stripe',
                'event_type': event_type,
                'processed': True
            }
            
        except Exception as e:
            db.rollback()
            logger.error(f"Stripe webhook processing failed: {e}")
            raise
    
    async def _handle_stripe_payment_success(self, db: Session, invoice_data: Dict):
        """Handle successful Stripe payment"""
        subscription_id = invoice_data.get('subscription')
        
        subscription = db.query(Subscription).filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if subscription:
            # Update payment status
            payment = db.query(Payment).filter_by(
                stripe_payment_intent_id=invoice_data.get('payment_intent'),
                status='pending'
            ).first()
            
            if payment:
                payment.status = 'succeeded'
                
                # Update referral if applicable
                referral = db.query(Referral).filter_by(
                    subscription_id=subscription.id,
                    status='pending'
                ).first()
                
                if referral:
                    referral.status = 'converted'
                    referral.conversion_date = datetime.utcnow()
                    
                    affiliate = referral.affiliate
                    affiliate.pending_earnings_cents += referral.commission_earned_cents
    
    async def _handle_stripe_payment_failed(self, db: Session, invoice_data: Dict):
        """Handle failed Stripe payment"""
        subscription_id = invoice_data.get('subscription')
        
        subscription = db.query(Subscription).filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if subscription:
            subscription.status = 'past_due'
    
    async def _handle_stripe_subscription_cancelled(self, db: Session, subscription_data: Dict):
        """Handle Stripe subscription cancellation"""
        stripe_subscription_id = subscription_data.get('id')
        
        subscription = db.query(Subscription).filter_by(
            stripe_subscription_id=stripe_subscription_id
        ).first()
        
        if subscription:
            subscription.status = 'cancelled'
            subscription.auto_renew = False
    
    async def _handle_stripe_chargeback(self, db: Session, dispute_data: Dict):
        """Handle Stripe chargeback/dispute"""
        charge_id = dispute_data.get('charge')
        
        # Find payment by charge ID and mark as disputed
        payment = db.query(Payment).filter_by(
            stripe_payment_intent_id=charge_id
        ).first()
        
        if payment:
            payment.status = 'disputed'
            payment.metadata = {**payment.metadata, 'dispute_data': dispute_data}

    async def get_user_subscription(self, user_id: str) -> Optional[Dict]:
        """Get user's current active subscription"""
        with get_db() as db:
            subscription = db.query(Subscription).filter(
                and_(
                    Subscription.user_id == user_id,
                    Subscription.status.in_(['active', 'trial', 'past_due']),
                    or_(
                        Subscription.expires_at.is_(None),
                        Subscription.expires_at > datetime.utcnow()
                    )
                )
            ).first()
            
            if not subscription:
                return None
            
            return {
                'id': str(subscription.id),
                'tier': subscription.tier.name,
                'display_name': subscription.tier.display_name,
                'status': subscription.status,
                'starts_at': subscription.starts_at.isoformat(),
                'expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None,
                'auto_renew': subscription.auto_renew,
                'features': subscription.tier.features,
                'amount_paid_cents': subscription.amount_paid_cents
            }
    
    async def cancel_subscription(self, user_id: str, subscription_id: str, 
                                immediate: bool = False) -> Dict:
        """Cancel user subscription"""
        with get_db() as db:
            try:
                subscription = db.query(Subscription).filter(
                    and_(
                        Subscription.id == subscription_id,
                        Subscription.user_id == user_id,
                        Subscription.status.in_(['active', 'trial', 'past_due'])
                    )
                ).first()
                
                if not subscription:
                    return {'success': False, 'error': 'Subscription not found'}
                
                # Cancel with payment processor
                processor_success = False
                if subscription.stripe_subscription_id:
                    if subscription.stripe_customer_id and len(subscription.stripe_customer_id) > 20:
                        # This is likely a Stripe subscription
                        try:
                            self.stripe_client.Subscription.modify(
                                subscription.stripe_subscription_id,
                                cancel_at_period_end=not immediate
                            )
                            processor_success = True
                        except Exception as e:
                            logger.error(f"Stripe cancellation failed: {e}")
                    else:
                        # This is likely an NMI subscription
                        try:
                            processor_success = await self.nmi_manager.cancel_subscription(
                                subscription.stripe_subscription_id
                            )
                        except Exception as e:
                            logger.error(f"NMI cancellation failed: {e}")
                
                # Update database regardless of processor response
                if immediate:
                    subscription.status = 'cancelled'
                    subscription.expires_at = datetime.utcnow()
                else:
                    subscription.auto_renew = False
                
                # Log audit event
                self._log_audit_event(
                    db, user_id, 'subscription_cancelled',
                    'subscription', subscription_id,
                    {'immediate': immediate, 'processor_success': processor_success}
                )
                
                db.commit()
                
                return {
                    'success': True,
                    'cancelled_immediately': immediate,
                    'expires_at': subscription.expires_at.isoformat() if subscription.expires_at else None
                }
                
            except Exception as e:
                db.rollback()
                logger.error(f"Subscription cancellation failed: {e}")
                return {'success': False, 'error': str(e)}
    
    async def upgrade_subscription(self, user_id: str, new_plan: str) -> Dict:
        """Upgrade user subscription to new plan"""
        with get_db() as db:
            try:
                # Get current subscription
                current_sub = db.query(Subscription).filter(
                    and_(
                        Subscription.user_id == user_id,
                        Subscription.status.in_(['active', 'trial']),
                        or_(
                            Subscription.expires_at.is_(None),
                            Subscription.expires_at > datetime.utcnow()
                        )
                    )
                ).first()
                
                if not current_sub:
                    return {'success': False, 'error': 'No active subscription found'}
                
                # Get new tier
                tiers = self._get_or_create_subscription_tiers(db)
                new_tier = tiers.get(new_plan)
                if not new_tier:
                    return {'success': False, 'error': f'Invalid plan: {new_plan}'}
                
                # Check if it's actually an upgrade
                if new_tier.price_cents <= current_sub.tier.price_cents:
                    return {'success': False, 'error': 'New plan must be higher tier'}
                
                # Calculate prorated amount
                if current_sub.expires_at:
                    days_remaining = (current_sub.expires_at - datetime.utcnow()).days
                    if days_remaining > 0:
                        # Calculate credit from current subscription
                        daily_rate_current = current_sub.tier.price_cents / current_sub.tier.duration_days
                        credit_cents = int(daily_rate_current * days_remaining)
                        
                        # Calculate prorated charge
                        upgrade_charge_cents = new_tier.price_cents - credit_cents
                    else:
                        upgrade_charge_cents = new_tier.price_cents
                else:
                    upgrade_charge_cents = new_tier.price_cents
                
                # Process upgrade payment if needed
                if upgrade_charge_cents > 0:
                    # For now, we'll create a new subscription
                    # In production, you'd want to handle prorated billing properly
                    pass
                
                # Update current subscription
                current_sub.status = 'cancelled'
                current_sub.expires_at = datetime.utcnow()
                
                # Create new subscription
                new_subscription = Subscription(
                    user_id=user_id,
                    tier_id=new_tier.id,
                    status='active',
                    starts_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(days=new_tier.duration_days) if new_tier.duration_days else None,
                    auto_renew=new_tier.name not in ['daily'],
                    amount_paid_cents=upgrade_charge_cents
                )
                db.add(new_subscription)
                
                # Log audit event
                self._log_audit_event(
                    db, user_id, 'subscription_upgraded',
                    'subscription', str(new_subscription.id),
                    {
                        'old_tier': current_sub.tier.name,
                        'new_tier': new_tier.name,
                        'upgrade_charge_cents': upgrade_charge_cents
                    }
                )
                
                db.commit()
                
                return {
                    'success': True,
                    'new_subscription_id': str(new_subscription.id),
                    'upgrade_charge_cents': upgrade_charge_cents,
                    'new_tier': new_tier.name,
                    'expires_at': new_subscription.expires_at.isoformat() if new_subscription.expires_at else None
                }
                
            except Exception as e:
                db.rollback()
                logger.error(f"Subscription upgrade failed: {e}")
                return {'success': False, 'error': str(e)}
    
    async def get_subscription_analytics(self, days: int = 30) -> Dict:
        """Get subscription analytics for business intelligence"""
        with get_db() as db:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                # New subscriptions
                new_subs = db.query(Subscription).filter(
                    Subscription.created_at >= cutoff_date
                ).count()
                
                # Revenue
                total_revenue = db.query(Payment).filter(
                    and_(
                        Payment.created_at >= cutoff_date,
                        Payment.status == 'succeeded'
                    )
                ).with_entities(Payment.amount_cents).all()
                
                revenue_cents = sum(payment.amount_cents for payment in total_revenue)
                
                # Cancellations
                cancellations = db.query(Subscription).filter(
                    and_(
                        Subscription.updated_at >= cutoff_date,
                        Subscription.status == 'cancelled'
                    )
                ).count()
                
                # Active subscriptions by tier
                active_by_tier = db.query(
                    SubscriptionTier.name,
                    db.func.count(Subscription.id)
                ).join(Subscription).filter(
                    Subscription.status.in_(['active', 'trial'])
                ).group_by(SubscriptionTier.name).all()
                
                return {
                    'period_days': days,
                    'new_subscriptions': new_subs,
                    'revenue_cents': revenue_cents,
                    'revenue_dollars': revenue_cents / 100,
                    'cancellations': cancellations,
                    'active_by_tier': dict(active_by_tier),
                    'churn_rate': (cancellations / max(new_subs, 1)) * 100
                }
                
            except Exception as e:
                logger.error(f"Analytics query failed: {e}")
                return {'error': str(e)}
    
    def has_feature_access(self, user_subscription: Dict, feature: str) -> bool:
        """Check if user has access to specific feature"""
        if not user_subscription:
            return False
        
        if user_subscription['status'] not in ['active', 'trial']:
            return False
        
        # Check if subscription is expired
        if user_subscription.get('expires_at'):
            expires_at = datetime.fromisoformat(user_subscription['expires_at'].replace('Z', '+00:00'))
            if expires_at <= datetime.utcnow():
                return False
        
        # Check feature access
        features = user_subscription.get('features', [])
        return feature in features
    
    async def process_subscription_renewals(self) -> Dict:
        """Process subscription renewals (run as scheduled task)"""
        with get_db() as db:
            try:
                # Find subscriptions expiring in next 24 hours
                tomorrow = datetime.utcnow() + timedelta(days=1)
                expiring_subs = db.query(Subscription).filter(
                    and_(
                        Subscription.status == 'active',
                        Subscription.auto_renew == True,
                        Subscription.expires_at <= tomorrow,
                        Subscription.expires_at > datetime.utcnow()
                    )
                ).all()
                
                renewed_count = 0
                failed_count = 0
                
                for subscription in expiring_subs:
                    try:
                        # Attempt to process renewal payment
                        if subscription.stripe_customer_id:
                            # Process renewal based on processor type
                            if len(subscription.stripe_customer_id) > 20:
                                # Stripe renewal (handled automatically)
                                renewed_count += 1
                            else:
                                # NMI renewal (handled by recurring billing)
                                renewed_count += 1
                        
                        # Extend subscription
                        subscription.expires_at = datetime.utcnow() + timedelta(
                            days=subscription.tier.duration_days
                        )
                        
                    except Exception as e:
                        logger.error(f"Renewal failed for subscription {subscription.id}: {e}")
                        subscription.status = 'past_due'
                        failed_count += 1
                
                db.commit()
                
                return {
                    'success': True,
                    'processed': len(expiring_subs),
                    'renewed': renewed_count,
                    'failed': failed_count
                }
                
            except Exception as e:
                db.rollback()
                logger.error(f"Renewal processing failed: {e}")
                return {'success': False, 'error': str(e)}

# Global payment service instance
payment_service = PaymentService()