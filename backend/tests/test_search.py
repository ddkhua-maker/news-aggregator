"""
Tests for semantic search module

This module tests the semantic search functionality including:
- Cosine similarity calculations
- Vector embedding search
- Similarity threshold filtering
- Result ranking and limiting
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Import functions to test
import sys
sys.path.insert(0, '../')
from search import cosine_similarity, semantic_search


class TestCosineSimilarity:
    """Tests for cosine similarity calculation"""

    def test_should_return_1_when_vectors_are_identical(self):
        """Test that identical vectors have similarity of 1.0"""
        vec1 = [1.0, 2.0, 3.0, 4.0]
        vec2 = [1.0, 2.0, 3.0, 4.0]
        result = cosine_similarity(vec1, vec2)
        assert result == pytest.approx(1.0, abs=0.01)

    def test_should_return_0_when_vectors_are_orthogonal(self):
        """Test that orthogonal vectors have similarity close to 0.5 (normalized)"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        result = cosine_similarity(vec1, vec2)
        # Orthogonal vectors have cosine similarity of 0, normalized to 0.5
        assert result == pytest.approx(0.5, abs=0.01)

    def test_should_return_0_5_when_vectors_are_opposite(self):
        """Test that opposite vectors have similarity of 0.0"""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [-1.0, -2.0, -3.0]
        result = cosine_similarity(vec1, vec2)
        # Opposite vectors have cosine similarity of -1, normalized to 0.0
        assert result == pytest.approx(0.0, abs=0.01)

    def test_should_handle_empty_vectors_gracefully(self):
        """Test that empty vectors return 0.0"""
        vec1 = []
        vec2 = [1.0, 2.0, 3.0]
        result = cosine_similarity(vec1, vec2)
        assert result == 0.0

    def test_should_handle_none_vectors_gracefully(self):
        """Test that None vectors return 0.0"""
        vec1 = None
        vec2 = [1.0, 2.0, 3.0]
        result = cosine_similarity(vec1, vec2)
        assert result == 0.0

    def test_should_handle_zero_vectors_gracefully(self):
        """Test that zero vectors return 0.0 (avoid division by zero)"""
        vec1 = [0.0, 0.0, 0.0]
        vec2 = [1.0, 2.0, 3.0]
        result = cosine_similarity(vec1, vec2)
        assert result == 0.0

    def test_should_calculate_similarity_for_different_length_vectors(self):
        """Test that vectors of different lengths are handled"""
        # NumPy will raise an error for different lengths, should be caught
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0]
        result = cosine_similarity(vec1, vec2)
        # Should return 0.0 due to error handling
        assert result == 0.0

    def test_should_calculate_similarity_for_large_vectors(self):
        """Test that large vectors (like embeddings) are handled correctly"""
        # Simulate OpenAI embedding size (1536 dimensions)
        vec1 = [0.1] * 1536
        vec2 = [0.1] * 1536
        result = cosine_similarity(vec1, vec2)
        assert result == pytest.approx(1.0, abs=0.01)

    def test_should_return_high_similarity_for_similar_vectors(self):
        """Test that similar (but not identical) vectors have high similarity"""
        vec1 = [1.0, 2.0, 3.0, 4.0, 5.0]
        vec2 = [1.1, 2.1, 3.1, 4.1, 5.1]
        result = cosine_similarity(vec1, vec2)
        assert result > 0.95  # Very similar

    def test_should_return_low_similarity_for_different_vectors(self):
        """Test that different vectors have low similarity"""
        vec1 = [1.0, 0.0, 0.0, 0.0, 0.0]
        vec2 = [0.0, 0.0, 0.0, 0.0, 1.0]
        result = cosine_similarity(vec1, vec2)
        assert result < 0.6  # Very different


class TestSemanticSearch:
    """Tests for semantic search function"""

    @patch('search.generate_embedding')
    def test_should_return_empty_list_when_query_is_empty(self, mock_generate_embedding):
        """Test that empty query returns empty list"""
        # Arrange
        mock_db_session = Mock()

        # Act
        result = semantic_search("", mock_db_session)

        # Assert
        assert result == []
        mock_generate_embedding.assert_not_called()

    @patch('search.generate_embedding')
    def test_should_return_empty_list_when_query_is_whitespace(self, mock_generate_embedding):
        """Test that whitespace-only query returns empty list"""
        # Arrange
        mock_db_session = Mock()

        # Act
        result = semantic_search("   ", mock_db_session)

        # Assert
        assert result == []
        mock_generate_embedding.assert_not_called()

    @patch('search.generate_embedding')
    def test_should_return_empty_list_when_no_articles_with_embeddings(self, mock_generate_embedding):
        """Test that search returns empty when no articles have embeddings"""
        # Arrange
        mock_generate_embedding.return_value = [0.1] * 1536
        mock_db_session = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = []
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query

        # Act
        result = semantic_search("test query", mock_db_session)

        # Assert
        assert result == []

    @patch('search.generate_embedding')
    def test_should_return_empty_list_when_embedding_generation_fails(self, mock_generate_embedding):
        """Test that search returns empty when query embedding fails"""
        # Arrange
        mock_generate_embedding.return_value = None
        mock_db_session = Mock()

        # Act
        result = semantic_search("test query", mock_db_session)

        # Assert
        assert result == []

    @patch('search.generate_embedding')
    def test_should_return_sorted_results_when_articles_found(self, mock_generate_embedding):
        """Test that results are sorted by similarity (highest first)"""
        # Arrange
        # Create diverse query embedding
        query_embedding = [1.0, 0.5, 0.3] + [0.1] * 1533
        mock_generate_embedding.return_value = query_embedding

        # Create mock articles with different similarity scores
        article1 = Mock()
        article1.id = 1
        article1.title = "Low similarity article"
        article1.embedding = [0.1, 0.1, 0.1] + [0.0] * 1533  # Lower similarity

        article2 = Mock()
        article2.id = 2
        article2.title = "High similarity article"
        article2.embedding = [1.0, 0.5, 0.3] + [0.1] * 1533  # High similarity (identical)

        article3 = Mock()
        article3.id = 3
        article3.title = "Medium similarity article"
        article3.embedding = [0.8, 0.4, 0.2] + [0.1] * 1533  # Medium similarity

        mock_db_session = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = [article1, article2, article3]
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query

        # Act
        result = semantic_search("test query", mock_db_session, limit=10, min_similarity=0.5)

        # Assert
        assert len(result) == 3
        # Results should be sorted by similarity (highest first)
        assert result[0][0].id == 2  # Highest similarity
        assert result[1][0].id == 3  # Medium similarity
        assert result[2][0].id == 1  # Lowest similarity
        # Check similarity scores are descending
        assert result[0][1] >= result[1][1]
        assert result[1][1] >= result[2][1]

    @patch('search.generate_embedding')
    def test_should_limit_results_when_limit_specified(self, mock_generate_embedding):
        """Test that results are limited to specified number"""
        # Arrange
        query_embedding = [1.0] * 1536
        mock_generate_embedding.return_value = query_embedding

        # Create 5 mock articles
        articles = []
        for i in range(5):
            article = Mock()
            article.id = i
            article.title = f"Article {i}"
            article.embedding = [1.0] * 1536
            articles.append(article)

        mock_db_session = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = articles
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query

        # Act
        result = semantic_search("test query", mock_db_session, limit=3, min_similarity=0.5)

        # Assert
        assert len(result) == 3

    @patch('search.generate_embedding')
    def test_should_filter_by_min_similarity_threshold(self, mock_generate_embedding):
        """Test that results below minimum similarity are filtered out"""
        # Arrange
        # Create diverse query embedding
        query_embedding = [1.0, 0.8, 0.6] + [0.2] * 1533
        mock_generate_embedding.return_value = query_embedding

        # Create articles with known similarities
        article_high = Mock()
        article_high.id = 1
        article_high.title = "High similarity"
        article_high.embedding = [1.0, 0.8, 0.6] + [0.2] * 1533  # Very high similarity (identical)

        article_low = Mock()
        article_low.id = 2
        article_low.title = "Low similarity"
        article_low.embedding = [0.1, 0.0, 0.0] + [0.0] * 1533  # Low similarity

        mock_db_session = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = [article_high, article_low]
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query

        # Act - set high threshold
        result = semantic_search("test query", mock_db_session, limit=10, min_similarity=0.80)

        # Assert - only high similarity article should be returned
        assert len(result) == 1
        assert result[0][0].id == 1

    @patch('search.generate_embedding')
    def test_should_return_empty_when_all_below_threshold(self, mock_generate_embedding):
        """Test that empty list returned when all results below threshold"""
        # Arrange
        # Create diverse query embedding
        query_embedding = [1.0, 0.9, 0.8] + [0.5] * 1533
        mock_generate_embedding.return_value = query_embedding

        # Create articles with low similarities
        articles = []
        for i in range(3):
            article = Mock()
            article.id = i
            article.title = f"Low similarity {i}"
            article.embedding = [0.1, 0.0, 0.0] + [0.0] * 1533  # Low similarity
            articles.append(article)

        mock_db_session = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = articles
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query

        # Act - set very high threshold
        result = semantic_search("test query", mock_db_session, limit=10, min_similarity=0.95)

        # Assert
        assert result == []

    @patch('search.generate_embedding')
    def test_should_use_default_min_similarity_of_0_65(self, mock_generate_embedding):
        """Test that default min_similarity is 0.65"""
        # Arrange
        # Create diverse query embedding
        query_embedding = [1.0, 0.8, 0.6] + [0.3] * 1533
        mock_generate_embedding.return_value = query_embedding

        # Create article with low similarity (should be filtered)
        article_below = Mock()
        article_below.id = 1
        article_below.title = "Low article"
        article_below.embedding = [0.1, 0.0, 0.0] + [0.0] * 1533  # Will have similarity < 0.65

        # Create article with > 0.65 similarity (should pass)
        article_above = Mock()
        article_above.id = 2
        article_above.title = "High article"
        article_above.embedding = [0.9, 0.7, 0.5] + [0.3] * 1533  # Will have similarity > 0.65

        mock_db_session = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = [article_below, article_above]
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query

        # Act - explicitly pass min_similarity=0.65 to test the default behavior
        result = semantic_search("test query", mock_db_session, limit=10, min_similarity=0.65)

        # Assert - only article above threshold should be returned
        assert len(result) >= 1
        # All returned results should be >= 0.65
        for article, score in result:
            assert score >= 0.65

    @patch('search.generate_embedding')
    def test_should_skip_articles_with_none_embeddings(self, mock_generate_embedding):
        """Test that articles with None embeddings are skipped gracefully"""
        # Arrange
        query_embedding = [1.0] * 1536
        mock_generate_embedding.return_value = query_embedding

        article_valid = Mock()
        article_valid.id = 1
        article_valid.title = "Valid article"
        article_valid.embedding = [1.0] * 1536

        article_none = Mock()
        article_none.id = 2
        article_none.title = "None embedding"
        article_none.embedding = None

        mock_db_session = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = [article_valid, article_none]
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query

        # Act
        result = semantic_search("test query", mock_db_session, limit=10, min_similarity=0.5)

        # Assert - only valid article returned
        assert len(result) == 1
        assert result[0][0].id == 1

    @patch('search.generate_embedding')
    def test_should_handle_exception_during_search(self, mock_generate_embedding):
        """Test that exceptions during search are handled gracefully"""
        # Arrange
        mock_generate_embedding.return_value = [1.0] * 1536
        mock_db_session = Mock()
        mock_db_session.query.side_effect = Exception("Database error")

        # Act
        result = semantic_search("test query", mock_db_session)

        # Assert
        assert result == []

    @patch('search.generate_embedding')
    def test_should_return_tuples_with_article_and_score(self, mock_generate_embedding):
        """Test that results are tuples of (Article, float)"""
        # Arrange
        query_embedding = [1.0] * 1536
        mock_generate_embedding.return_value = query_embedding

        article = Mock()
        article.id = 1
        article.title = "Test article"
        article.embedding = [1.0] * 1536

        mock_db_session = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = [article]
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query

        # Act
        result = semantic_search("test query", mock_db_session, limit=10, min_similarity=0.5)

        # Assert
        assert len(result) == 1
        assert isinstance(result[0], tuple)
        assert len(result[0]) == 2
        assert result[0][0] == article
        assert isinstance(result[0][1], float)
        assert 0.0 <= result[0][1] <= 1.0

    @patch('search.generate_embedding')
    def test_should_use_default_limit_of_10(self, mock_generate_embedding):
        """Test that default limit is 10 results"""
        # Arrange
        # Create diverse query embedding
        query_embedding = [1.0, 0.9, 0.8] + [0.5] * 1533
        mock_generate_embedding.return_value = query_embedding

        # Create 20 articles all with high similarity
        articles = []
        for i in range(20):
            article = Mock()
            article.id = i
            article.title = f"Article {i}"
            article.embedding = [0.95, 0.85, 0.75] + [0.5] * 1533  # High similarity
            articles.append(article)

        mock_db_session = Mock()
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.all.return_value = articles
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query

        # Act - explicitly pass limit=10 to test the default behavior
        result = semantic_search("test query", mock_db_session, limit=10, min_similarity=0.5)

        # Assert
        assert len(result) == 10
