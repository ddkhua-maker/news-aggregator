"""
RSS feed parser to fetch and parse articles from multiple sources
"""
import feedparser
import logging
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from email.utils import parsedate_to_datetime
import time
import re
from html import unescape

try:
    from .models import Article
    from .config import RSS_FEEDS, MAX_ARTICLES_PER_FEED
except ImportError:
    from models import Article
    from config import RSS_FEEDS, MAX_ARTICLES_PER_FEED

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_html(text: str) -> str:
    """
    Clean HTML content by removing tags and unescaping entities

    Args:
        text: Raw HTML text

    Returns:
        Cleaned plain text
    """
    if not text:
        return ""

    # Remove script and style tags with their content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Unescape HTML entities (&nbsp;, &amp;, &quot;, etc.)
    text = unescape(text)

    # Replace multiple spaces/newlines with single space
    text = re.sub(r'\s+', ' ', text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def parse_published_date(date_string: str) -> Optional[datetime]:
    """
    Parse various RSS date formats into datetime object

    Args:
        date_string: Date string from RSS feed

    Returns:
        datetime object or None if parsing fails
    """
    if not date_string:
        return None

    try:
        # Try parsing RFC 822 format (common in RSS feeds)
        return parsedate_to_datetime(date_string)
    except Exception as e:
        logger.warning(f"Failed to parse date '{date_string}': {e}")
        return None


def extract_source_name(feed_url: str) -> str:
    """
    Extract a readable source name from feed URL

    Args:
        feed_url: URL of the RSS feed

    Returns:
        Source name string
    """
    try:
        # Extract domain from URL
        if "yogonet.com" in feed_url:
            if "europe" in feed_url:
                return "Yogonet Europe"
            elif "united-states" in feed_url:
                return "Yogonet US"
            elif "latin-america" in feed_url:
                return "Yogonet Latin America"
            elif "asia" in feed_url:
                return "Yogonet Asia"
            elif "online-gaming" in feed_url:
                return "Yogonet Online Gaming"
        elif "europeangaming.eu" in feed_url:
            return "European Gaming"
        elif "igamingbusiness.com" in feed_url:
            return "iGaming Business"
        elif "cdcgamingreports.com" in feed_url:
            return "CDC Gaming Reports"
        elif "casinobeats.com" in feed_url:
            return "Casino Beats"
        elif "sbcnews.co.uk" in feed_url:
            return "SBC News"
        elif "slotbeats.com" in feed_url:
            return "Slot Beats"

        # Fallback: extract domain name
        from urllib.parse import urlparse
        domain = urlparse(feed_url).netloc
        return domain.replace("www.", "").split(".")[0].title()
    except Exception:
        return feed_url


def parse_single_feed(feed_url: str, max_articles: int = MAX_ARTICLES_PER_FEED) -> List[Dict]:
    """
    Parse a single RSS feed and extract articles

    Args:
        feed_url: URL of the RSS feed
        max_articles: Maximum number of articles to extract

    Returns:
        List of parsed article dictionaries
    """
    articles = []
    source_name = extract_source_name(feed_url)

    try:
        logger.info(f"Parsing feed: {source_name} ({feed_url})")

        # Parse the feed with timeout
        feed = feedparser.parse(feed_url)

        # Check for parsing errors
        if feed.bozo:
            logger.warning(f"Feed parsing warning for {source_name}: {feed.bozo_exception}")

        # Check if feed has entries
        if not feed.entries:
            logger.warning(f"No entries found in feed: {source_name}")
            return articles

        # Process entries (limit to max_articles)
        for entry in feed.entries[:max_articles]:
            try:
                # Extract article data
                article_data = {
                    "title": entry.get("title", "No title"),
                    "link": entry.get("link", ""),
                    "source": source_name,
                    "published_date": None,
                    "content": ""
                }

                # Skip if no link
                if not article_data["link"]:
                    logger.warning(f"Skipping article without link in {source_name}")
                    continue

                # Parse published date
                if hasattr(entry, "published"):
                    article_data["published_date"] = parse_published_date(entry.published)
                elif hasattr(entry, "updated"):
                    article_data["published_date"] = parse_published_date(entry.updated)

                # Extract content (try different fields)
                raw_content = ""
                if hasattr(entry, "content") and entry.content:
                    raw_content = entry.content[0].get("value", "")
                elif hasattr(entry, "summary"):
                    raw_content = entry.summary
                elif hasattr(entry, "description"):
                    raw_content = entry.description

                # Clean HTML tags and entities
                clean_content = clean_html(raw_content)

                # Limit to 250 characters
                if len(clean_content) > 250:
                    article_data["content"] = clean_content[:250] + "..."
                else:
                    article_data["content"] = clean_content

                articles.append(article_data)

            except Exception as e:
                logger.error(f"Error parsing entry in {source_name}: {e}")
                continue

        logger.info(f"Successfully parsed {len(articles)} articles from {source_name}")

    except Exception as e:
        logger.error(f"Error fetching feed {source_name}: {e}")

    return articles


def parse_all_feeds() -> List[Dict]:
    """
    Parse all configured RSS feeds

    Returns:
        Combined list of all parsed articles from all feeds
    """
    all_articles = []

    logger.info(f"Starting to parse {len(RSS_FEEDS)} RSS feeds")

    for feed_url in RSS_FEEDS:
        try:
            articles = parse_single_feed(feed_url, MAX_ARTICLES_PER_FEED)
            all_articles.extend(articles)

            # Small delay between feeds to be respectful
            time.sleep(0.5)

        except Exception as e:
            logger.error(f"Failed to parse feed {feed_url}: {e}")
            # Continue with next feed even if one fails
            continue

    logger.info(f"Finished parsing all feeds. Total articles: {len(all_articles)}")
    return all_articles


def save_articles_to_db(articles: List[Dict], db_session: Session) -> int:
    """
    Save parsed articles to database, avoiding duplicates

    Uses hybrid approach:
    1. In-memory deduplication to remove cross-feed duplicates
    2. Individual commits to prevent cascading failures

    Args:
        articles: List of article dictionaries from parser
        db_session: Database session

    Returns:
        Number of new articles saved
    """
    new_articles_count = 0

    logger.info(f"Attempting to save {len(articles)} articles to database")

    # STEP 1: Deduplicate within batch (prevents cross-feed duplicates)
    seen_links = set()
    unique_articles = []
    for article_data in articles:
        link = article_data["link"]
        if link not in seen_links:
            seen_links.add(link)
            unique_articles.append(article_data)
        else:
            logger.debug(f"Skipping duplicate within batch: {article_data['title'][:50]}...")

    duplicates_in_batch = len(articles) - len(unique_articles)
    if duplicates_in_batch > 0:
        logger.info(f"Removed {duplicates_in_batch} duplicate links within batch")

    # STEP 2: Save articles with individual commits
    for article_data in unique_articles:
        try:
            # Check if article already exists in database
            existing_article = db_session.query(Article).filter(
                Article.link == article_data["link"]
            ).first()

            if existing_article:
                logger.debug(f"Article already exists in DB: {article_data['title'][:50]}...")
                continue

            # Create new article
            new_article = Article(
                title=article_data["title"],
                link=article_data["link"],
                source=article_data["source"],
                published_date=article_data.get("published_date"),
                content=article_data.get("content", "")
            )

            db_session.add(new_article)
            db_session.commit()  # Commit immediately after each article
            new_articles_count += 1
            logger.debug(f"Saved new article: {article_data['title'][:50]}...")

        except IntegrityError as e:
            # Handle unique constraint violations (now properly caught)
            db_session.rollback()
            logger.warning(f"Duplicate article (DB constraint): {article_data.get('link', 'unknown')}")
            continue
        except Exception as e:
            db_session.rollback()
            logger.error(f"Error saving article '{article_data.get('title', 'unknown')}': {e}")
            continue

    logger.info(f"Successfully saved {new_articles_count} new articles to database")
    return new_articles_count
