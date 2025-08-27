"""
NMI (Network Merchants Inc.) Payment Processing Client
Handles subscription billing, customer vault, and recurring payments
"""

import os
import requests
import hashlib
import hmac
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass
from decimal import Decimal

logger = logging.getLogger(__name__)

@dataclass
class NMICustomer:
    """NMI Customer data"""
    customer_vault_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None

@dataclass
class NMISubscription:
    """NMI Subscription data"""
    subscription_id: str
    customer_vault_id: str
    plan_id: str
    amount: Decimal
    frequency: str  # 'daily', 'weekly', 'monthly'
    status: str
    next_charge_date: datetime
    created_date: datetime

@dataclass
class NMITransaction:
    """NMI Transaction result"""
    transaction_id: str
    response_code: str
    response_text: str
    auth_code: Optional[str]
    amount: Decimal
    status: str  # 'approved', 'declined', 'error'

class NMIClient:
    """NMI API Client for payment processing"""
    
    def __init__(self):
        self.api_url = os.getenv('NMI_API_URL', 'https://secure.nmi.com/api/transact.php')
        self.username = os.getenv('NMI_USERNAME')
        self.password = os.getenv('NMI_PASSWORD')
        self.security_key = os.getenv('NMI_SECURITY_KEY')
        
        if not all([self.username, self.password]):
            raise ValueError("NMI credentials not configured. Set NMI_USERNAME and NMI_PASSWORD")
    
    def _make_request(self, data: Dict) -> Dict:
        """Make API request to NMI"""
        # Add authentication
        data.update({
            'username': self.username,
            'password': self.password,
        })
        
        try:
            response = requests.post(self.api_url, data=data, timeout=30)
            response.raise_for_status()
            
            # Parse response (NMI returns URL-encoded data)
            result = {}
            for line in response.text.split('&'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    result[key] = value
            
            logger.info(f"NMI API Response: {result.get('response', 'unknown')}")
            return result
            
        except requests.RequestException as e:
            logger.error(f"NMI API request failed: {e}")
            raise
    
    async def create_customer_vault(self, customer_data: Dict, payment_data: Dict) -> NMICustomer:
        """Create customer vault entry"""
        data = {
            'type': 'add_customer',
            'customer_vault': 'add_customer',
            'first_name': customer_data.get('first_name', ''),
            'last_name': customer_data.get('last_name', ''),
            'email': customer_data.get('email', ''),
            'phone': customer_data.get('phone', ''),
            'address1': customer_data.get('address', ''),
            'city': customer_data.get('city', ''),
            'state': customer_data.get('state', ''),
            'zip': customer_data.get('zip_code', ''),
            'ccnumber': payment_data.get('card_number'),
            'ccexp': payment_data.get('expiry_date'),  # MMYY format
            'cvv': payment_data.get('cvv'),
        }
        
        result = self._make_request(data)
        
        if result.get('response') == '1':  # Success
            return NMICustomer(
                customer_vault_id=result.get('customer_vault_id'),
                first_name=customer_data.get('first_name', ''),
                last_name=customer_data.get('last_name', ''),
                email=customer_data.get('email', ''),
                phone=customer_data.get('phone'),
                address=customer_data.get('address'),
                city=customer_data.get('city'),
                state=customer_data.get('state'),
                zip_code=customer_data.get('zip_code')
            )
        else:
            error_msg = result.get('responsetext', 'Unknown error')
            raise Exception(f"Failed to create customer vault: {error_msg}")
    
    async def process_sale(self, customer_vault_id: str, amount: Decimal, 
                          order_description: str = None) -> NMITransaction:
        """Process a one-time sale"""
        data = {
            'type': 'sale',
            'customer_vault_id': customer_vault_id,
            'amount': str(amount),
            'orderid': f"NFL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'orderdescription': order_description or 'NFL Prediction Subscription',
        }
        
        result = self._make_request(data)
        
        return NMITransaction(
            transaction_id=result.get('transactionid', ''),
            response_code=result.get('response', ''),
            response_text=result.get('responsetext', ''),
            auth_code=result.get('authcode'),
            amount=amount,
            status='approved' if result.get('response') == '1' else 'declined'
        )
    
    async def create_subscription(self, customer_vault_id: str, plan_data: Dict) -> NMISubscription:
        """Create recurring subscription"""
        # Map our plan frequencies to NMI format
        frequency_map = {
            'daily': {'day_frequency': '1'},
            'weekly': {'day_frequency': '7'},
            'monthly': {'month_frequency': '1'},
            'season': {'month_frequency': '6'}  # 6 months for season
        }
        
        frequency_data = frequency_map.get(plan_data['frequency'], {'month_frequency': '1'})
        
        data = {
            'type': 'add_subscription',
            'customer_vault_id': customer_vault_id,
            'amount': str(plan_data['amount']),
            'plan_id': plan_data['plan_id'],
            'start_date': plan_data.get('start_date', datetime.now().strftime('%Y%m%d')),
            **frequency_data
        }
        
        result = self._make_request(data)
        
        if result.get('response') == '1':
            return NMISubscription(
                subscription_id=result.get('subscription_id'),
                customer_vault_id=customer_vault_id,
                plan_id=plan_data['plan_id'],
                amount=plan_data['amount'],
                frequency=plan_data['frequency'],
                status='active',
                next_charge_date=datetime.now() + timedelta(days=1),
                created_date=datetime.now()
            )
        else:
            error_msg = result.get('responsetext', 'Unknown error')
            raise Exception(f"Failed to create subscription: {error_msg}")
    
    async def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel recurring subscription"""
        data = {
            'type': 'delete_subscription',
            'subscription_id': subscription_id
        }
        
        result = self._make_request(data)
        return result.get('response') == '1'
    
    async def update_subscription(self, subscription_id: str, updates: Dict) -> bool:
        """Update subscription details"""
        data = {
            'type': 'update_subscription',
            'subscription_id': subscription_id,
            **updates
        }
        
        result = self._make_request(data)
        return result.get('response') == '1'
    
    async def get_customer_vault(self, customer_vault_id: str) -> Optional[Dict]:
        """Get customer vault information"""
        data = {
            'type': 'customer_vault',
            'customer_vault_id': customer_vault_id,
            'report_type': 'customer_vault'
        }
        
        result = self._make_request(data)
        
        if result.get('response') == '1':
            return result
        return None
    
    async def process_refund(self, transaction_id: str, amount: Optional[Decimal] = None) -> NMITransaction:
        """Process refund for a transaction"""
        data = {
            'type': 'refund',
            'transactionid': transaction_id,
        }
        
        if amount:
            data['amount'] = str(amount)
        
        result = self._make_request(data)
        
        return NMITransaction(
            transaction_id=result.get('transactionid', ''),
            response_code=result.get('response', ''),
            response_text=result.get('responsetext', ''),
            auth_code=result.get('authcode'),
            amount=amount or Decimal('0'),
            status='approved' if result.get('response') == '1' else 'declined'
        )
    
    def verify_webhook(self, payload: str, signature: str) -> bool:
        """Verify webhook signature"""
        if not self.security_key:
            logger.warning("NMI security key not configured, skipping webhook verification")
            return True
        
        expected_signature = hmac.new(
            self.security_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)

class NMISubscriptionManager:
    """High-level subscription management using NMI"""
    
    def __init__(self):
        self.nmi_client = NMIClient()
        
        # Subscription plan mapping
        self.plans = {
            'daily': {
                'plan_id': 'NFL_DAILY',
                'amount': Decimal('12.99'),
                'frequency': 'daily',
                'description': '1 Day NFL Predictions Access'
            },
            'weekly': {
                'plan_id': 'NFL_WEEKLY',
                'amount': Decimal('29.99'),
                'frequency': 'weekly',
                'description': '1 Week NFL Predictions Access'
            },
            'monthly': {
                'plan_id': 'NFL_MONTHLY',
                'amount': Decimal('99.99'),
                'frequency': 'monthly',
                'description': '1 Month NFL Predictions Access'
            },
            'season': {
                'plan_id': 'NFL_SEASON',
                'amount': Decimal('299.99'),
                'frequency': 'season',
                'description': 'Full Season + Playoffs Access'
            }
        }
    
    async def create_subscription(self, user_data: Dict, payment_data: Dict, 
                                plan_name: str) -> Dict:
        """Create complete subscription with customer vault and recurring billing"""
        try:
            # Get plan details
            plan = self.plans.get(plan_name)
            if not plan:
                raise ValueError(f"Invalid plan: {plan_name}")
            
            # Create customer vault
            customer = await self.nmi_client.create_customer_vault(user_data, payment_data)
            logger.info(f"Created customer vault: {customer.customer_vault_id}")
            
            # Process initial payment
            initial_payment = await self.nmi_client.process_sale(
                customer.customer_vault_id,
                plan['amount'],
                plan['description']
            )
            
            if initial_payment.status != 'approved':
                raise Exception(f"Initial payment failed: {initial_payment.response_text}")
            
            # Create recurring subscription (if not one-time)
            subscription = None
            if plan_name != 'daily':  # Daily is one-time, others are recurring
                subscription = await self.nmi_client.create_subscription(
                    customer.customer_vault_id,
                    plan
                )
                logger.info(f"Created subscription: {subscription.subscription_id}")
            
            return {
                'success': True,
                'customer_vault_id': customer.customer_vault_id,
                'subscription_id': subscription.subscription_id if subscription else None,
                'transaction_id': initial_payment.transaction_id,
                'amount': plan['amount'],
                'plan': plan_name
            }
            
        except Exception as e:
            logger.error(f"Subscription creation failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel subscription"""
        return await self.nmi_client.cancel_subscription(subscription_id)
    
    async def process_upgrade(self, old_subscription_id: str, new_plan: str, 
                            customer_vault_id: str) -> Dict:
        """Upgrade subscription to new plan"""
        try:
            # Cancel old subscription
            await self.nmi_client.cancel_subscription(old_subscription_id)
            
            # Create new subscription
            plan = self.plans[new_plan]
            subscription = await self.nmi_client.create_subscription(
                customer_vault_id,
                plan
            )
            
            return {
                'success': True,
                'subscription_id': subscription.subscription_id,
                'plan': new_plan
            }
            
        except Exception as e:
            logger.error(f"Subscription upgrade failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }