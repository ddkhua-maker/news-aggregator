"""
Tests for RSS parser module

This module tests the RSS feed parsing functionality including:
- HTML content cleaning
- RSS feed parsing
- Source name extraction
- Article data extraction
"""
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import functions to test
from rss_parser import clean_html, extract_source_name, parse_single_feed


class TestCleanHTML:
    """Tests for HTML cleaning function"""

    def test_should_remove_html_tags_when_present(self):
        """Test that HTML tags are completely removed"""
        html = "<p>Test content</p>"
        result = clean_html(html)
        assert result == "Test content"
        assert "<" not in result
        assert ">" not in result

    def test_should_remove_nested_html_tags_when_present(self):
        """Test that nested HTML tags are removed"""
        html = "<div><p>Test <strong>content</strong></p></div>"
        result = clean_html(html)
        assert result == "Test content"

    def test_should_unescape_html_entities_when_present(self):
        """Test that HTML entities like &nbsp; are unescaped"""
        html = "Test&nbsp;content&amp;more"
        result = clean_html(html)
        assert result == "Test content&more"

    def test_should_unescape_special_characters_when_present(self):
        """Test unescaping of special characters"""
        html = "&lt;tag&gt; &quot;quoted&quot;"
        result = clean_html(html)
        assert result == "<tag> \"quoted\""

    def test_should_return_empty_string_when_input_is_none(self):
        """Test edge case with None input"""
        result = clean_html(None)
        assert result == ""

    def test_should_return_empty_string_when_input_is_empty(self):
        """Test edge case with empty string"""
        result = clean_html("")
        assert result == ""

    def test_should_remove_script_tags_with_content(self):
        """Test that script tags and their content are removed"""
        html = "<p>Content</p><script>alert('test')</script>"
        result = clean_html(html)
        assert "script" not in result.lower()
        assert "alert" not in result.lower()
        assert "Content" in result

    def test_should_remove_style_tags_with_content(self):
        """Test that style tags and their content are removed"""
        html = "<p>Content</p><style>body { color: red; }</style>"
        result = clean_html(html)
        assert "style" not in result.lower()
        assert "color" not in result.lower()
        assert "Content" in result

    def test_should_collapse_multiple_spaces_when_present(self):
        """Test that multiple spaces are collapsed into one"""
        html = "Test    content   with    spaces"
        result = clean_html(html)
        assert result == "Test content with spaces"

    def test_should_trim_leading_and_trailing_whitespace(self):
        """Test that leading/trailing whitespace is removed"""
        html = "   Test content   "
        result = clean_html(html)
        assert result == "Test content"


class TestExtractSourceName:
    """Tests for source name extraction function"""

    def test_should_extract_yogonet_europe_when_url_contains_europe(self):
        """Test extraction of Yogonet Europe source"""
        url = "https://www.yogonet.com/international/europe/rss.xml"
        result = extract_source_name(url)
        assert result == "Yogonet Europe"

    def test_should_extract_yogonet_us_when_url_contains_united_states(self):
        """Test extraction of Yogonet US source"""
        url = "https://www.yogonet.com/international/united-states/rss.xml"
        result = extract_source_name(url)
        assert result == "Yogonet US"

    def test_should_extract_european_gaming_when_domain_matches(self):
        """Test extraction of European Gaming source"""
        url = "https://europeangaming.eu/portal/feed/"
        result = extract_source_name(url)
        assert result == "European Gaming"

    def test_should_extract_igaming_business_when_domain_matches(self):
        """Test extraction of iGaming Business source"""
        url = "https://igamingbusiness.com/company-news/feed/"
        result = extract_source_name(url)
        assert result == "iGaming Business"

    def test_should_extract_domain_name_when_no_special_pattern(self):
        """Test fallback to domain name extraction"""
        url = "https://example.com/feed/"
        result = extract_source_name(url)
        assert result == "Example"  # Domain name capitalized

    def test_should_handle_invalid_url_gracefully(self):
        """Test that invalid URLs don't crash the function"""
        url = "not-a-valid-url"
        result = extract_source_name(url)
        assert isinstance(result, str)
        assert len(result) > 0


class TestParseSingleFeed:
    """Tests for RSS feed parsing function"""

    @patch('rss_parser.feedparser.parse')
    def test_should_parse_feed_when_valid_url(self, mock_parse, sample_rss_entry):
        """Test successful feed parsing with valid URL"""
        # Arrange
        mock_parse.return_value = Mock(
            entries=[sample_rss_entry],
            bozo=False
        )

        # Act
        result = parse_single_feed("https://example.com/feed")

        # Assert
        assert len(result) == 1
        assert result[0]["title"] == "Test Article Title"
        assert result[0]["link"] == "https://example.com/article"
        assert "source" in result[0]

    @patch('rss_parser.feedparser.parse')
    def test_should_return_empty_list_when_no_entries(self, mock_parse):
        """Test that empty feed returns empty list"""
        # Arrange
        mock_parse.return_value = Mock(entries=[], bozo=False)

        # Act
        result = parse_single_feed("https://example.com/feed")

        # Assert
        assert result == []

    @patch('rss_parser.feedparser.parse')
    def test_should_limit_articles_when_max_articles_set(self, mock_parse, sample_rss_entry):
        """Test that max_articles parameter limits results"""
        # Arrange
        mock_parse.return_value = Mock(
            entries=[sample_rss_entry] * 20,  # 20 entries
            bozo=False
        )

        # Act
        result = parse_single_feed("https://example.com/feed", max_articles=5)

        # Assert
        assert len(result) == 5

    @patch('rss_parser.feedparser.parse')
    def test_should_clean_html_content_when_parsing(self, mock_parse):
        """Test that HTML content is cleaned during parsing"""
        # Arrange
        entry = Mock()
        entry.title = "Test"
        entry.link = "https://example.com/article"
        entry.description = "<p>Content with <strong>HTML</strong></p>"
        entry.published = "Mon, 01 Jan 2024 12:00:00 GMT"

        mock_parse.return_value = Mock(entries=[entry], bozo=False)

        # Act
        result = parse_single_feed("https://example.com/feed")

        # Assert
        assert len(result) == 1
        assert "<p>" not in result[0]["content"]
        assert "<strong>" not in result[0]["content"]
        assert "Content with HTML" in result[0]["content"]

    @patch('rss_parser.feedparser.parse')
    def test_should_skip_article_when_no_link(self, mock_parse):
        """Test that articles without links are skipped"""
        # Arrange
        entry = Mock()
        entry.title = "Test"
        entry.link = ""  # Empty link
        entry.description = "Content"

        mock_parse.return_value = Mock(entries=[entry], bozo=False)

        # Act
        result = parse_single_feed("https://example.com/feed")

        # Assert
        assert result == []

    @patch('rss_parser.feedparser.parse')
    def test_should_truncate_content_when_exceeds_250_chars(self, mock_parse):
        """Test that content is truncated to 250 characters"""
        # Arrange
        long_content = "A" * 300  # 300 characters
        entry = Mock()
        entry.title = "Test"
        entry.link = "https://example.com/article"
        entry.description = long_content
        entry.published = "Mon, 01 Jan 2024 12:00:00 GMT"

        mock_parse.return_value = Mock(entries=[entry], bozo=False)

        # Act
        result = parse_single_feed("https://example.com/feed")

        # Assert
        assert len(result[0]["content"]) == 253  # 250 + "..."
        assert result[0]["content"].endswith("...")

    @patch('rss_parser.feedparser.parse')
    def test_should_handle_parse_exception_gracefully(self, mock_parse):
        """Test that parsing exceptions are handled gracefully"""
        # Arrange
        mock_parse.side_effect = Exception("Network error")

        # Act
        result = parse_single_feed("https://example.com/feed")

        # Assert
        assert result == []

    @patch('rss_parser.feedparser.parse')
    def test_should_parse_published_date_when_present(self, mock_parse, sample_rss_entry):
        """Test that published date is parsed correctly"""
        # Arrange
        mock_parse.return_value = Mock(entries=[sample_rss_entry], bozo=False)

        # Act
        result = parse_single_feed("https://example.com/feed")

        # Assert
        assert result[0]["published_date"] is not None
