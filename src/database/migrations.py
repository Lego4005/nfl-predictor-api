"""
Database migration utilities and seed data
"""

from sqlalchemy.orm import Session
from .models import SubscriptionTier, AdminUser, User
from .config import db_config
import logging
import bcrypt
import uuid

logger = logging.getLogger(__name__)

def create_subscription_tiers(session: Session):
    """Create default subscription tiers"""
    tiers = [
        {
            'name': 'free_trial',
            'display_name': 'Free Trial',
            'price_cents': 0,
            'duration_days': 7,
            'features': ['sample_predictions', 'basic_accuracy', 'limited_access'],
            'is_active': True,
            'is_admin_granted': False
        },
        {
            'name': 'daily',
            'display_name': '1 Day Access',
            'price_cents': 1299,  # $12.99
            'duration_days': 1,
            'features': ['real_time_predictions', 'basic_props', 'live_accuracy'],
            'is_active': True,
            'is_admin_granted': False
        },
        {
            'name': 'weekly',
            'display_name': '1 Week Access',
            'price_cents': 2999,  # $29.99
            'duration_days': 7,
            'features': ['real_time_predictions', 'basic_props', 'live_accuracy', 'email_alerts'],
            'is_active': True,
            'is_admin_granted': False
        },
        {
            'name': 'monthly',
            'display_name': '1 Month Access',
            'price_cents': 9999,  # $99.99
            'duration_days': 30,
            'features': ['all_weekly', 'advanced_analytics', 'full_props', 'priority_email_alerts'],
            'is_active': True,
            'is_admin_granted': False
        },
        {
            'name': 'season',
            'display_name': 'Full Season + Playoffs',
            'price_cents': 29999,  # $299.99
            'duration_days': 180,
            'features': ['all_monthly', 'playoff_predictions', 'data_export', 'priority_support'],
            'is_active': True,
            'is_admin_granted': False
        },
        {
            'name': 'friends_family',
            'display_name': 'Friends & Family',
            'price_cents': 0,
            'duration_days': 180,  # Admin configurable
            'features': ['all_season', 'special_access'],
            'is_active': True,
            'is_admin_granted': True
        },
        {
            'name': 'beta_tester',
            'display_name': 'Beta Tester',
            'price_cents': 0,
            'duration_days': 365,  # Extended access
            'features': ['all_season', 'beta_features', 'feedback_tools'],
            'is_active': True,
            'is_admin_granted': True
        },
        {
            'name': 'premium_analytics',
            'display_name': 'Premium Analytics Add-on',
            'price_cents': 4999,  # $49.99/month
            'duration_days': 30,
            'features': ['advanced_analytics', 'custom_reports', 'api_access'],
            'is_active': True,
            'is_admin_granted': False
        }
    ]
    
    for tier_data in tiers:
        # Check if tier already exists
        existing_tier = session.query(SubscriptionTier).filter_by(name=tier_data['name']).first()
        if not existing_tier:
            tier = SubscriptionTier(**tier_data)
            session.add(tier)
            logger.info(f"Created subscription tier: {tier_data['display_name']}")
    
    session.commit()
    logger.info("Subscription tiers created successfully")

def create_admin_user(session: Session, email: str, password: str, role: str = 'super_admin'):
    """Create an admin user"""
    # Check if user already exists
    existing_user = session.query(User).filter_by(email=email).first()
    if existing_user:
        logger.warning(f"User with email {email} already exists")
        return existing_user
    
    # Hash password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create user
    user = User(
        email=email,
        password_hash=password_hash,
        first_name='Admin',
        last_name='User',
        email_verified=True,
        is_active=True
    )
    session.add(user)
    session.flush()  # Get user ID
    
    # Create admin user
    admin_user = AdminUser(
        user_id=user.id,
        role=role,
        permissions=[
            'user_management',
            'subscription_management',
            'free_access_grants',
            'affiliate_management',
            'analytics_access',
            'system_administration'
        ],
        is_active=True
    )
    session.add(admin_user)
    session.commit()
    
    logger.info(f"Created admin user: {email} with role: {role}")
    return user

def seed_database():
    """Seed database with initial data"""
    logger.info("Starting database seeding...")
    
    with db_config.get_session() as session:
        # Create subscription tiers
        create_subscription_tiers(session)
        
        # Create default admin user (change password in production!)
        admin_email = "admin@nflpredictor.com"
        admin_password = "admin123"  # Change this!
        create_admin_user(session, admin_email, admin_password)
        
        logger.info("Database seeding completed successfully")

def run_migrations():
    """Run database migrations"""
    logger.info("Running database migrations...")
    
    # Create all tables
    db_config.create_tables()
    
    # Seed initial data
    seed_database()
    
    logger.info("Database migrations completed successfully")

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run migrations
    run_migrations()