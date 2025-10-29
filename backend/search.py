"""
Semantic search functionality using vector embeddings
"""
import numpy as np
from typing import List, Tuple
from sqlalchemy.orm import Session
import logging

try:
    from .models import Article
    from .openai_summarizer import generate_embedding
except ImportError:
    from models import Article
    from openai_summarizer import generate_embedding

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors

    Args:
        vec1: First vector (embedding)
        vec2: Second vector (embedding)

    Returns:
        Similarity score between 0 and 1 (1 = identical, 0 = completely different)
    """
    if not vec1 or not vec2:
        return 0.0

    try:
        # Convert to numpy arrays
        v1 = np.array(vec1)
        v2 = np.array(vec2)

        # Calculate cosine similarity
        # cosine_sim = (A · B) / (||A|| * ||B||)
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)

        # Avoid division by zero
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0

        similarity = dot_product / (norm_v1 * norm_v2)

        # Ensure result is between 0 and 1
        # Cosine similarity can be -1 to 1, we normalize to 0 to 1
        normalized_similarity = (similarity + 1) / 2

        return float(normalized_similarity)

    except Exception as e:
        logger.error(f"Error calculating cosine similarity: {e}")
        return 0.0


def semantic_search(
    query: str,
    db_session: Session,
    limit: int = 10,
    min_similarity: float = 0.65
) -> List[Tuple[Article, float]]:
    """
    Perform semantic search on articles using vector embeddings

    Args:
        query: Search query text
        db_session: Database session
        limit: Maximum number of results to return (default 10)
        min_similarity: Minimum similarity threshold (0.65 = 65% match)

    Returns:
        List of tuples (Article, similarity_score) sorted by similarity (highest first)
        Only returns results with similarity >= min_similarity
    """
    if not query or not query.strip():
        logger.warning("Empty search query provided")
        return []

    try:
        logger.info(f"Performing semantic search for: '{query[:50]}...'")

        # Generate embedding for the search query
        query_embedding = generate_embedding(query)

        if not query_embedding:
            logger.error("Failed to generate query embedding")
            return []

        # Get all articles that have embeddings
        articles_with_embeddings = db_session.query(Article).filter(
            Article.embedding.isnot(None)
        ).all()

        if not articles_with_embeddings:
            logger.warning("No articles with embeddings found in database")
            return []

        logger.info(f"Found {len(articles_with_embeddings)} articles with embeddings")

        # Calculate similarity scores for each article
        article_scores = []

        for article in articles_with_embeddings:
            try:
                # Article embedding is stored as JSON (list)
                article_embedding = article.embedding

                if not article_embedding:
                    continue

                # Calculate cosine similarity
                similarity = cosine_similarity(query_embedding, article_embedding)

                article_scores.append((article, similarity))

            except Exception as e:
                logger.error(f"Error calculating similarity for article {article.id}: {e}")
                continue

        # Sort by similarity score (highest first)
        article_scores.sort(key=lambda x: x[1], reverse=True)

        # Filter by minimum similarity threshold
        filtered_results = [
            (article, score) for article, score in article_scores
            if score >= min_similarity
        ]

        # Return top N results after filtering
        top_results = filtered_results[:limit]

        logger.info(f"Found {len(filtered_results)} results above threshold {min_similarity:.2f}")
        logger.info(f"Returning {len(top_results)} search results")

        if top_results:
            logger.info(f"Top result similarity: {top_results[0][1]:.4f} ({top_results[0][1]*100:.1f}%)")
            logger.info(f"Top result: {top_results[0][0].title[:50]}...")
        else:
            logger.info(f"No results found with similarity >= {min_similarity:.2f}")

        return top_results

    except Exception as e:
        logger.error(f"Error during semantic search: {e}")
        return []
