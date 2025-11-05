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
        prompt = f"""Summarize this iGaming news article in EXACTLY 2-3 SHORT sentences.
Extract only the most important facts:
- Who is involved (company/person names)
- What happened (main event/announcement)
- Why it matters (impact/significance)

Be concise and factual. No fluff. Use **bold** for company names.

Article title: {title}
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
            article_text = f"""
Title: {article.title}
Source: {article.source}
Link: {article.link}
Summary: {article.summary or article.content[:200] if article.content else 'No content available'}
"""
            formatted_articles.append(article_text)

        articles_text = "\n".join(formatted_articles)

        # Create prompt for OpenAI
        prompt = f"""You are an iGaming industry analyst. Create a professional daily digest from these news articles.

For EACH article you discuss:
1. Write the title in **bold**
2. Add a brief 1-2 sentence summary
3. IMMEDIATELY after the summary, add a new line with: [Read original →](article-link)

Group articles by topics (regulations, M&A, product launches, markets, technology).

Format example:
**Article Title Here**
Brief 1-2 sentence summary of the article content and key points.
[Read original →](https://example.com/article)

**Another Article Title**
Another brief summary here.
[Read original →](https://example.com/article2)

Articles to include:
{articles_text}

Remember: ALWAYS include the [Read original →](link) after EACH article summary."""

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

        # Append source links section to ensure links are always included
        sources_section = "\n\n---\n\n## 📰 Source Articles\n\n"
        for i, article in enumerate(articles, 1):
            sources_section += f"{i}. [{article.title}]({article.link}) - *{article.source}*\n"

        digest_with_sources = digest + sources_section

        logger.info(f"Successfully created daily digest with {len(articles)} articles")
        return digest_with_sources

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


def create_linkedin_article(digest_content: str) -> str:
    """
    Generate professional LinkedIn article from daily digest

    Args:
        digest_content: Daily digest markdown content

    Returns:
        LinkedIn-ready article text (800-1000 words)

    Raises:
        Exception: If API call fails or client not initialized
    """
    if not client:
        raise Exception("OpenAI API client not initialized. Please set OPENAI_API_KEY in .env file")

    if not digest_content:
        logger.warning("No digest content provided for article generation")
        return "No digest content available for article generation."

    try:
        logger.info("Generating LinkedIn article from digest")

        # Create prompt for OpenAI
        prompt = f"""You are a professional iGaming industry journalist writing for LinkedIn.

Transform this daily digest into a comprehensive, engaging LinkedIn article (800-1000 words).

Structure:
1. **Compelling headline** - Make it attention-grabbing and relevant
2. **Hook paragraph** - Why this matters to iGaming professionals
3. **Main story** - Lead with the most important development with context and analysis
4. **Key developments by category** - Group related news:
   - Regulations & Compliance
   - Mergers & Acquisitions
   - Product Launches & Innovation
   - Market Expansion & Growth
5. **Industry implications** - What this means for the sector
6. **Concluding thoughts** - Forward-looking perspective

Style:
- Professional but conversational tone
- Use storytelling and narrative flow
- Add insights and context beyond the facts
- Include relevant data/numbers when available
- Engage the reader with questions or observations
- Use markdown formatting (**bold** for emphasis, ## for headers)

Digest content:
{digest_content}

Write a complete LinkedIn article ready to publish. Make it insightful and valuable for industry professionals."""

        # Call OpenAI API
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            max_tokens=1200,  # Allows ~800-1000 words
            temperature=0.7,   # Slightly creative for engaging content
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Extract article from response
        article = response.choices[0].message.content

        logger.info("Successfully generated LinkedIn article")
        return article

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
        logger.error(f"Unexpected error during article generation: {e}")
        raise Exception(f"Failed to generate article: {str(e)}")


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
