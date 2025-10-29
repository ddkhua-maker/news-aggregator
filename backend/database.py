"""
Database setup and session management
Supports both SQLite (development) and PostgreSQL (production)
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
import logging

try:
    from .models import Base
    from .config import DATABASE_URL
except ImportError:
    from models import Base
    from config import DATABASE_URL

logger = logging.getLogger(__name__)

# Determine database type from DATABASE_URL
is_sqlite = "sqlite" in DATABASE_URL
is_postgres = "postgresql" in DATABASE_URL

# Create database engine with appropriate settings
if is_postgres:
    # PostgreSQL production settings
    logger.info("Using PostgreSQL database")
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,  # Maximum number of connections
        max_overflow=20,  # Allow up to 20 overflow connections
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,  # Recycle connections after 1 hour
        echo=False  # Disable SQL echo in production
    )
elif is_sqlite:
    # SQLite development settings
    logger.info("Using SQLite database (development mode)")
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
else:
    # Fallback - use SQLite
    logger.warning(f"Unknown database type in DATABASE_URL: {DATABASE_URL}")
    logger.warning("Falling back to SQLite")
    engine = create_engine(
        "sqlite:///./news_aggregator.db",
        connect_args={"check_same_thread": False}
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize database - create all tables
    This is safe to call multiple times (won't recreate existing tables)
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")

        # Log database info
        if is_postgres:
            logger.info("PostgreSQL connection pool configured: pool_size=10, max_overflow=20")
        elif is_sqlite:
            logger.info(f"SQLite database: {DATABASE_URL}")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def get_db() -> Session:
    """
    Dependency function to get database session
    Yields a database session and closes it after use

    Usage in FastAPI:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            # Use db here
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection():
    """
    Test database connection
    Returns True if connection successful, False otherwise
    """
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False
