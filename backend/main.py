"""
FastAPI main application
News Aggregator API endpoints with security hardening
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field, field_validator
import logging
import os

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Absolute imports (required for Railway deployment)
from database import get_db, init_db
from config import CORS_ORIGINS, RSS_FEEDS, DEBUG_MODE
from models import Article, DigestEntry
from rss_parser import parse_all_feeds, save_articles_to_db, extract_source_name
from openai_summarizer import process_new_articles, create_daily_digest
from search import semantic_search

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="iGaming News Aggregator API",
    description="API for aggregating and summarizing iGaming news from multiple sources",
    version="1.0.0",
    debug=DEBUG_MODE
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# CORS middleware - secure configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # From config, environment-based
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only needed methods
    allow_headers=["Content-Type", "Accept"],  # Restrict headers
)

# Get the absolute path to frontend directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

# Mount static files for frontend
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
async def startup_event():
    """
    Initialize database on application startup
    """
    init_db()
    logger.info("Database initialized successfully")
    logger.info(f"Application started in {os.getenv('ENVIRONMENT', 'development')} mode")
    logger.info(f"CORS origins: {CORS_ORIGINS}")


@app.get("/")
async def read_root():
    """
    Serve the frontend index.html at root
    """
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    # Fallback to API health check if frontend not found
    return {"status": "healthy", "service": "iGaming News Aggregator", "note": "Frontend not found"}


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring
    """
    return {"status": "healthy", "service": "iGaming News Aggregator"}


@app.get("/api/articles")
@limiter.limit("120/hour")  # Rate limit: 120 requests per hour
async def get_articles(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    source: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get articles with pagination and optional filtering

    Args:
        limit: Maximum number of articles to return (1-100)
        offset: Number of articles to skip (>=0)
        source: Filter by source name (optional)
        db: Database session

    Returns:
        JSON with articles list and metadata
    """
    try:
        # Input validation
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100"
            )

        if offset < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Offset must be non-negative"
            )

        # Build query
        query = db.query(Article)

        # Filter by source if provided (with validation)
        if source:
            # Whitelist validation - only allow known sources
            valid_sources = [extract_source_name(url) for url in RSS_FEEDS]
            if source not in valid_sources:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid source. Valid sources: {', '.join(valid_sources)}"
                )
            query = query.filter(Article.source == source)

        # Get total count
        total_count = query.count()

        # Order by published_date DESC, then by created_at DESC
        query = query.order_by(Article.published_date.desc().nullslast(), Article.created_at.desc())

        # Apply pagination
        articles = query.offset(offset).limit(limit).all()

        # Convert to dict (without embeddings to reduce response size)
        articles_data = [article.to_dict() for article in articles]
        # Remove embeddings from response
        for article in articles_data:
            article.pop('embedding', None)

        return {
            "status": "success",
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "articles": articles_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching articles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch articles"
        )


@app.post("/api/fetch-news")
@limiter.limit("10/hour")  # Rate limit: 10 requests per hour
async def fetch_news(request: Request, db: Session = Depends(get_db)):
    """
    Manually trigger RSS feed fetching and save articles to database

    Rate limited to prevent abuse and excessive RSS feed requests

    Args:
        db: Database session

    Returns:
        JSON with status and count of new articles
    """
    try:
        logger.info("Starting RSS feed fetch...")

        # Parse all feeds
        articles = parse_all_feeds()

        if not articles:
            return {
                "status": "success",
                "message": "No new articles found",
                "new_articles": 0,
                "total_parsed": 0
            }

        # Save to database
        new_articles_count = save_articles_to_db(articles, db)

        logger.info(f"RSS feed fetch complete. New articles: {new_articles_count}")

        return {
            "status": "success",
            "message": f"Successfully fetched and saved {new_articles_count} new articles",
            "new_articles": new_articles_count,
            "total_parsed": len(articles)
        }

    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch news"
        )


@app.post("/api/generate-summaries")
@limiter.limit("5/hour")  # Rate limit: 5 requests per hour (expensive operation)
async def generate_summaries(
    request: Request,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Generate summaries for articles without summaries using OpenAI API

    EXPENSIVE OPERATION - Rate limited to prevent API cost abuse

    Args:
        limit: Maximum number of articles to process (1-100)
        db: Database session

    Returns:
        JSON with status and count of summaries generated
    """
    try:
        # Input validation
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Limit must be between 1 and 100"
            )

        logger.info("Starting summary generation...")

        # Process new articles
        summaries_count = process_new_articles(db, limit=limit)

        logger.info(f"Summary generation complete. Summaries generated: {summaries_count}")

        return {
            "status": "success",
            "message": f"Successfully generated {summaries_count} summaries",
            "summaries_generated": summaries_count
        }

    except Exception as e:
        logger.error(f"Error generating summaries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate summaries"
        )


@app.post("/api/create-digest")
@limiter.limit("5/hour")  # Rate limit: 5 requests per hour
async def create_digest_endpoint(request: Request, db: Session = Depends(get_db)):
    """
    Create a daily digest for today's articles using OpenAI API

    Args:
        db: Database session

    Returns:
        JSON with status and digest content
    """
    try:
        today = date.today()
        logger.info(f"Creating daily digest for {today}...")

        # Check if digest already exists for today
        existing_digest = db.query(DigestEntry).filter(
            DigestEntry.digest_date == today
        ).first()

        if existing_digest:
            return {
                "status": "success",
                "message": "Digest already exists for today",
                "digest": existing_digest.content,
                "article_count": existing_digest.article_count,
                "digest_date": today.isoformat()
            }

        # Fetch today's articles (articles from the last 24 hours)
        from datetime import timedelta
        yesterday = datetime.now() - timedelta(days=1)

        articles = db.query(Article).filter(
            Article.created_at >= yesterday
        ).order_by(Article.published_date.desc()).all()

        if not articles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No articles found for today"
            )

        # Generate digest using OpenAI
        digest_content = create_daily_digest(articles)

        # Save to database
        digest_entry = DigestEntry(
            digest_date=today,
            content=digest_content,
            article_count=len(articles)
        )
        db.add(digest_entry)
        db.commit()
        db.refresh(digest_entry)

        logger.info(f"Daily digest created successfully for {today}")

        return {
            "status": "success",
            "message": f"Successfully created digest for {today}",
            "digest": digest_content,
            "article_count": len(articles),
            "digest_date": today.isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating digest: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create digest"
        )


@app.get("/api/digest/{digest_date}")
@limiter.limit("60/hour")  # Rate limit: 60 requests per hour
async def get_digest(request: Request, digest_date: str, db: Session = Depends(get_db)):
    """
    Get digest for a specific date

    Args:
        digest_date: Date in YYYY-MM-DD format
        db: Database session

    Returns:
        JSON with digest content
    """
    try:
        # Parse date with validation
        try:
            target_date = datetime.strptime(digest_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )

        # Fetch digest from database
        digest = db.query(DigestEntry).filter(
            DigestEntry.digest_date == target_date
        ).first()

        if not digest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No digest found for {digest_date}"
            )

        return {
            "status": "success",
            "digest": digest.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching digest: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch digest"
        )


@app.delete("/api/digest/{digest_date}")
@limiter.limit("10/hour")  # Rate limit: 10 requests per hour
async def delete_digest(request: Request, digest_date: str, db: Session = Depends(get_db)):
    """
    Delete digest for a specific date (allows regeneration)

    Args:
        digest_date: Date in YYYY-MM-DD format
        db: Database session

    Returns:
        JSON with status message
    """
    try:
        # Parse date with validation
        try:
            target_date = datetime.strptime(digest_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid date format. Use YYYY-MM-DD"
            )

        # Find and delete digest
        digest = db.query(DigestEntry).filter(
            DigestEntry.digest_date == target_date
        ).first()

        if not digest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No digest found for {digest_date}"
            )

        db.delete(digest)
        db.commit()

        logger.info(f"Deleted digest for {digest_date}")

        return {
            "status": "success",
            "message": f"Digest for {digest_date} deleted successfully. You can now recreate it."
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting digest: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete digest"
        )


@app.get("/api/sources")
@limiter.limit("60/hour")  # Rate limit: 60 requests per hour
async def get_sources(request: Request):
    """
    Get list of all RSS feed sources

    Returns:
        List of configured RSS feed sources
    """
    sources = [extract_source_name(feed_url) for feed_url in RSS_FEEDS]

    return {
        "status": "success",
        "count": len(sources),
        "sources": sources
    }


# Pydantic models for request bodies with validation
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Search query text")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results to return")

    @field_validator('query')
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        """Validate query is not empty after stripping whitespace"""
        if not v.strip():
            raise ValueError('Query cannot be empty or whitespace')
        return v.strip()


@app.post("/api/search")
@limiter.limit("60/hour")  # Rate limit: 60 requests per hour
async def search_articles(
    request: Request,
    search_request: SearchRequest,
    db: Session = Depends(get_db)
):
    """
    Semantic search for articles using vector embeddings

    Args:
        search_request: SearchRequest with query and optional limit
        db: Database session

    Returns:
        JSON with search results and similarity scores
    """
    try:
        query = search_request.query
        limit = search_request.limit

        logger.info(f"Searching for: '{query[:50]}...' (limit={limit})")

        # Perform semantic search
        results = semantic_search(query, db, limit=limit)

        if not results:
            return {
                "status": "success",
                "query": query,
                "count": 0,
                "results": [],
                "message": "No articles found with high enough relevance (>65% match)"
            }

        # Format results with similarity scores (without embeddings)
        formatted_results = []
        for article, similarity_score in results:
            article_dict = article.to_dict()
            article_dict.pop('embedding', None)  # Remove embedding from response
            article_dict["similarity_score"] = float(similarity_score)
            formatted_results.append(article_dict)

        logger.info(f"Found {len(formatted_results)} results for query: '{query[:50]}...'")

        return {
            "status": "success",
            "query": query,
            "count": len(formatted_results),
            "results": formatted_results
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


# Debug endpoint removed for security - uncomment only for development/staging
# @app.get("/api/debug/stats")
# async def debug_stats(db: Session = Depends(get_db)):
#     """Debug endpoint - ONLY enable in development"""
#     if os.getenv("ENVIRONMENT") == "production":
#         raise HTTPException(status_code=404, detail="Not found")
#     # ... debug code here ...


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
