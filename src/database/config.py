"""
Database configuration and connection management
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import logging

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration management"""
    
    def __init__(self):
        self.database_url = self._get_database_url()
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def _get_database_url(self) -> str:
        """Get database URL from environment variables"""
        # Production database URL
        database_url = os.getenv('DATABASE_URL')
        
        if database_url:
            # Handle Heroku postgres:// URLs
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            return database_url
        
        # For testing, use SQLite if no PostgreSQL is configured
        if os.getenv('USE_SQLITE', 'false').lower() == 'true':
            db_name = os.getenv('DB_NAME', 'nfl_predictor')
            return f"sqlite:///./{db_name}.db"
        
        # Development database configuration
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'nfl_predictor')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', 'password')
        
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    def _create_engine(self):
        """Create SQLAlchemy engine with optimized settings"""
        engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=os.getenv('DB_ECHO', 'false').lower() == 'true'
        )
        
        # Add connection event listeners
        @event.listens_for(engine, "connect")
        def set_database_pragma(dbapi_connection, connection_record):
            """Set database-specific settings on connection"""
            if 'postgresql' in str(engine.url):
                # PostgreSQL specific settings
                with dbapi_connection.cursor() as cursor:
                    cursor.execute("SET timezone TO 'UTC'")
            elif 'sqlite' in str(engine.url):
                # SQLite specific settings
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        
        return engine
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """Create all database tables"""
        from .models import Base
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        from .models import Base
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("All database tables dropped")

# Global database instance
db_config = DatabaseConfig()

# Dependency for FastAPI
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions"""
    with db_config.get_session() as session:
        yield session