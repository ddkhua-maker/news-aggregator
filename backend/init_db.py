"""
Database initialization script
Run this script to initialize the database tables on first deployment

Usage:
    python init_db.py
"""
import sys
import logging
from database import init_db, test_connection
from config import DATABASE_URL, ENVIRONMENT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Initialize database tables"""
    logger.info("=" * 60)
    logger.info("Database Initialization Script")
    logger.info("=" * 60)
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Database URL: {DATABASE_URL}")
    logger.info("=" * 60)

    try:
        # Test connection first
        logger.info("Testing database connection...")
        if not test_connection():
            logger.error("Database connection test failed!")
            logger.error("Please check your DATABASE_URL configuration")
            sys.exit(1)

        logger.info("✓ Database connection successful")

        # Initialize database tables
        logger.info("Creating database tables...")
        init_db()
        logger.info("✓ Database tables created successfully")

        logger.info("=" * 60)
        logger.info("Database initialization complete!")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"Database initialization failed: {e}")
        logger.error("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
