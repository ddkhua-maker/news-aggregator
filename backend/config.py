"""
Configuration file for news aggregator
Contains RSS feed sources and application settings
"""
import os
from dotenv import load_dotenv

# Load .env only in development (Railway provides env vars directly)
if os.getenv("ENVIRONMENT") != "production":
    load_dotenv()

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development, staging, production

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate critical configuration
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable must be set")

# OpenAI Models
OPENAI_MODEL = "gpt-4o-mini"  # Model for article summaries
EMBEDDING_MODEL = "text-embedding-3-small"  # Model for semantic search

# Note: DATABASE_URL is handled in database.py with proper Railway PostgreSQL URL conversion

# RSS Feed Sources (iGaming news sites)
RSS_FEEDS = [
    "https://www.yogonet.com/international/europe/rss.xml",
    "https://www.yogonet.com/international/united-states/rss.xml",
    "https://www.yogonet.com/international/latin-america/rss.xml",
    "https://www.yogonet.com/international/asia/rss.xml",
    "https://www.yogonet.com/international/online-gaming/rss.xml",
    "https://europeangaming.eu/portal/feed/",
    "https://igamingbusiness.com/company-news/feed/",
    "https://cdcgamingreports.com/feed/",
    "https://casinobeats.com/feed/",
    "https://sbcnews.co.uk/feed/",
    "https://slotbeats.com/feed/"
]

# Application Settings (read from environment with defaults)
FETCH_INTERVAL_MINUTES = int(os.getenv("FETCH_INTERVAL_MINUTES", "30"))  # How often to fetch RSS feeds
MAX_ARTICLES_PER_FEED = int(os.getenv("MAX_ARTICLES_PER_FEED", "10"))   # Maximum articles to fetch per feed
SUMMARY_MAX_TOKENS = int(os.getenv("SUMMARY_MAX_TOKENS", "500"))     # Maximum tokens for OpenAI API summaries

# CORS Settings - Environment-based
if ENVIRONMENT == "production":
    # Production: Only allow specific domains
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")
    if not CORS_ORIGINS or CORS_ORIGINS == [""]:
        raise ValueError("CORS_ORIGINS must be set in .env for production")
elif ENVIRONMENT == "staging":
    # Staging: Allow staging domains + localhost
    CORS_ORIGINS = [
        os.getenv("FRONTEND_URL", "https://staging.your-domain.com"),
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
else:
    # Development: Allow localhost only
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

# Security Settings
DEBUG_MODE = ENVIRONMENT != "production"  # Disable debug in production

# Server Configuration
PORT = int(os.getenv("PORT", "8000"))  # Railway provides PORT env variable
HOST = os.getenv("HOST", "0.0.0.0")
