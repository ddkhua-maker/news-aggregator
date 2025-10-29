"""
Pytest configuration and shared fixtures

This file contains pytest configuration and fixtures that are shared across all tests.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock


@pytest.fixture
def mock_db_session():
    """
    Provides a mock database session for testing

    Returns:
        Mock: A mock database session object
    """
    session = Mock()
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    return session


@pytest.fixture
def sample_rss_entry():
    """
    Provides a sample RSS feed entry for testing

    Returns:
        Mock: A mock RSS entry with typical fields
    """
    entry = Mock()
    entry.title = "Test Article Title"
    entry.link = "https://example.com/article"
    entry.description = "<p>Test article content with <strong>HTML</strong></p>"
    entry.summary = "Test summary"
    entry.published = "Mon, 01 Jan 2024 12:00:00 GMT"
    return entry


@pytest.fixture
def sample_article_data():
    """
    Provides sample article data for testing

    Returns:
        dict: A dictionary with article fields
    """
    return {
        "title": "Test Article",
        "link": "https://example.com/article",
        "source": "Test Source",
        "published_date": None,
        "content": "Test content for the article",
        "summary": None,
        "embedding": None
    }


@pytest.fixture
def sample_embedding():
    """
    Provides a sample embedding vector for testing

    Returns:
        list: A list of 1536 float values (OpenAI embedding dimension)
    """
    return [0.1] * 1536


@pytest.fixture
def mock_openai_client():
    """
    Provides a mock OpenAI client for testing

    Returns:
        Mock: A mock OpenAI client with common methods
    """
    client = Mock()

    # Mock chat completions
    client.chat = Mock()
    client.chat.completions = Mock()
    client.chat.completions.create = Mock()

    # Mock embeddings
    client.embeddings = Mock()
    client.embeddings.create = Mock()

    return client


@pytest.fixture
def mock_openai_response():
    """
    Provides a mock OpenAI API response for testing

    Returns:
        Mock: A mock response object
    """
    response = Mock()
    response.choices = [Mock()]
    response.choices[0].message = Mock()
    response.choices[0].message.content = "Test AI response"
    return response


@pytest.fixture
def mock_embedding_response():
    """
    Provides a mock OpenAI embedding response for testing

    Returns:
        Mock: A mock embedding response
    """
    response = Mock()
    response.data = [Mock()]
    response.data[0].embedding = [0.1] * 1536
    return response
