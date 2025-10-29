"""
OpenAI API integration for generating article summaries and embeddings
"""
from openai import OpenAI, APIError, APIConnectionError, RateLimitError
from typing import Optional, List
from sqlalchemy.orm import Session
import logging
import time

try:
    from .config import OPENAI_API_KEY, OPENAI_MODEL, EMBEDDING_MODEL, SUMMARY_MAX_TOKENS
    from .models import Article
except ImportError:
    from config import OPENAI_API_KEY, OPENAI_MODEL, EMBEDDING_MODEL, SUMMARY_MAX_TOKENS
    from models import Article

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def summarize_single_article(title: str, content: str) -> str:
    """
    Summarize a single article using OpenAI API

    Args:
        title: Article title
        content: Article content/description

    Returns:
        Generated summary text

    Raises:
        Exception: If API call fails or client not initialized
    """
    if not client:
        raise Exception("OpenAI API client not initialized. Please set OPENAI_API_KEY in .env file")

    if not content:
        logger.warning(f"No content provided for article: {title}")
        return "No content available for summarization."

    try:
        logger.info(f"Generating summary for article: {title[:50]}...")

        # Create prompt for OpenAI
        prompt = f"""Summarize this iGaming news article in 2-3 clear sentences. Focus on key facts.

Use simple formatting:
- Use **bold** for company names or important terms
- Keep it concise and readable
- No HTML tags

Article: {title}

Content: {content}"""

        # Call OpenAI API
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            max_tokens=SUMMARY_MAX_TOKENS,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Extract summary from response
        summary = response.choices[0].message.content

        logger.info(f"Successfully generated summary for: {title[:50]}...")
        return summary

    except RateLimitError as e:
        logger.error(f"Rate limit exceeded: {e}")
        raise Exception("API rate limit exceeded. Please try again later.")
    except APIConnectionError as e:
        logger.error(f"API connection error: {e}")
        raise Exception("Failed to connect to OpenAI API. Please check your internet connection.")
    except APIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise Exception(f"OpenAI API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during summarization: {e}")
        raise Exception(f"Failed to generate summary: {str(e)}")


def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding vector for text using OpenAI embeddings API

    Args:
        text: Text to embed (article title + content)

    Returns:
        Embedding vector as list of floats

    Raises:
        Exception: If API call fails or client not initialized
    """
    if not client:
        raise Exception("OpenAI API client not initialized. Please set OPENAI_API_KEY in .env file")

    if not text:
        logger.warning("No text provided for embedding generation")
        return []

    try:
        # Truncate text to prevent token limit issues (max ~8000 tokens for text-embedding-3-small)
        max_chars = 30000  # Conservative limit
        truncated_text = text[:max_chars] if len(text) > max_chars else text

        logger.info(f"Generating embedding for text ({len(truncated_text)} chars)...")

        # Call OpenAI embeddings API
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=truncated_text
        )

        # Extract embedding vector
        embedding = response.data[0].embedding

        logger.info(f"Successfully generated embedding (dim={len(embedding)})")
        return embedding

    except RateLimitError as e:
        logger.error(f"Rate limit exceeded: {e}")
        raise Exception("API rate limit exceeded. Please try again later.")
    except APIConnectionError as e:
        logger.error(f"API connection error: {e}")
        raise Exception("Failed to connect to OpenAI API. Please check your internet connection.")
    except APIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise Exception(f"OpenAI API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during embedding generation: {e}")
        raise Exception(f"Failed to generate embedding: {str(e)}")


def create_daily_digest(articles: List[Article]) -> str:
    """
    Create a daily digest from multiple articles using OpenAI API

    Args:
        articles: List of Article objects from database

    Returns:
        Formatted daily digest text

    Raises:
        Exception: If API call fails or client not initialized
    """
    if not client:
        raise Exception("OpenAI API client not initialized. Please set OPENAI_API_KEY in .env file")

    if not articles:
        logger.warning("No articles provided for daily digest")
        return "No articles available for today's digest."

    try:
        logger.info(f"Creating daily digest from {len(articles)} articles")

        # Format articles for the prompt
        formatted_articles = []
        for i, article in enumerate(articles, 1):
            article_text = f"{i}. **{article.title}** (Source: {article.source})\n"
            if article.summary:
                article_text += f"   Summary: {article.summary}\n"
            elif article.content:
                # Use first 500 chars of content if no summary
                article_text += f"   Content: {article.content[:500]}...\n"
            formatted_articles.append(article_text)

        articles_text = "\n".join(formatted_articles)

        # Create prompt for OpenAI
        prompt = f"""You are an iGaming industry analyst. Create a professional daily digest from these news articles. Group by topics (regulations, mergers, product launches, etc). Highlight the most important developments. Keep it concise but informative.

Articles:
{articles_text}"""

        # Call OpenAI API
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            max_tokens=4000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Extract digest from response
        digest = response.choices[0].message.content

        logger.info(f"Successfully created daily digest with {len(articles)} articles")
        return digest

    except RateLimitError as e:
        logger.error(f"Rate limit exceeded: {e}")
        raise Exception("API rate limit exceeded. Please try again later.")
    except APIConnectionError as e:
        logger.error(f"API connection error: {e}")
        raise Exception("Failed to connect to OpenAI API. Please check your internet connection.")
    except APIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise Exception(f"OpenAI API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during digest creation: {e}")
        raise Exception(f"Failed to create daily digest: {str(e)}")


def process_new_articles(db_session: Session, limit: int = 50) -> int:
    """
    Process new articles without summaries and generate summaries + embeddings for them

    Args:
        db_session: Database session
        limit: Maximum number of articles to process

    Returns:
        Number of articles successfully processed
    """
    if not client:
        logger.error("OpenAI API client not initialized")
        return 0

    try:
        # Fetch articles without summaries or embeddings
        articles_without_summary = db_session.query(Article).filter(
            (Article.summary.is_(None) | (Article.summary == "")) |
            (Article.embedding.is_(None))
        ).limit(limit).all()

        if not articles_without_summary:
            logger.info("No new articles to process")
            return 0

        logger.info(f"Processing {len(articles_without_summary)} articles")

        processed_count = 0

        for article in articles_without_summary:
            try:
                # Generate summary if missing
                if not article.summary:
                    summary = summarize_single_article(article.title, article.content)
                    article.summary = summary
                    logger.info(f"Generated summary for: {article.title[:50]}...")

                # Generate embedding if missing
                if not article.embedding:
                    # Combine title and content for embedding
                    text_for_embedding = f"{article.title}\n\n{article.content or ''}"
                    embedding = generate_embedding(text_for_embedding)
                    article.embedding = embedding
                    logger.info(f"Generated embedding for: {article.title[:50]}...")

                # Save to database
                db_session.commit()

                processed_count += 1
                logger.info(f"Processed article {processed_count}/{len(articles_without_summary)}: {article.title[:50]}...")

                # Small delay to respect rate limits
                time.sleep(0.5)

            except RateLimitError as e:
                logger.warning(f"Rate limit hit after {processed_count} articles. Stopping processing.")
                db_session.rollback()
                break
            except Exception as e:
                logger.error(f"Failed to process article {article.id}: {e}")
                db_session.rollback()
                # Continue with next article
                continue

        logger.info(f"Successfully processed {processed_count} articles")
        return processed_count

    except Exception as e:
        logger.error(f"Error in process_new_articles: {e}")
        db_session.rollback()
        return 0
