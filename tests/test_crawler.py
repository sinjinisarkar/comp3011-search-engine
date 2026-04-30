# tests/test_crawler.py
import pytest
from unittest.mock import patch, MagicMock
from src.crawler import Crawler


class TestIsValidUrl:
    def test_same_domain_is_valid(self):
        c = Crawler("https://quotes.toscrape.com/")
        assert c._is_valid_url("https://quotes.toscrape.com/page/2/") == True

    def test_different_domain_is_invalid(self):
        c = Crawler("https://quotes.toscrape.com/")
        assert c._is_valid_url("https://google.com/") == False

    def test_subdomain_is_invalid(self):
        c = Crawler("https://quotes.toscrape.com/")
        assert c._is_valid_url("https://other.toscrape.com/") == False


class TestGetLinks:
    def test_extracts_internal_links(self):
        c = Crawler("https://quotes.toscrape.com/")
        html = '<a href="/page/2/">Next</a>'
        links = c._get_links(html, "https://quotes.toscrape.com/")
        assert "https://quotes.toscrape.com/page/2/" in links

    def test_ignores_external_links(self):
        c = Crawler("https://quotes.toscrape.com/")
        html = '<a href="https://google.com/">Google</a>'
        links = c._get_links(html, "https://quotes.toscrape.com/")
        assert "https://google.com/" not in links

    def test_removes_fragments(self):
        c = Crawler("https://quotes.toscrape.com/")
        html = '<a href="/page/1/#section">Link</a>'
        links = c._get_links(html, "https://quotes.toscrape.com/")
        assert "https://quotes.toscrape.com/page/1/" in links
        # make sure the fragment version is NOT in there
        for link in links:
            assert "#" not in link

    def test_no_links_returns_empty(self):
        c = Crawler("https://quotes.toscrape.com/")
        html = "<html><body><p>No links here</p></body></html>"
        links = c._get_links(html, "https://quotes.toscrape.com/")
        assert links == []


class TestCrawl:
    @patch("src.crawler.time.sleep")  # mock sleep so tests run instantly
    @patch("src.crawler.requests.get")
    def test_crawl_returns_pages(self, mock_get, mock_sleep):
        # Simulate a page with no links so crawl stops after 1 page
        mock_response = MagicMock()
        mock_response.text = "<html><body><p>hello</p></body></html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        c = Crawler("https://quotes.toscrape.com/")
        pages = c.crawl()

        assert len(pages) == 1
        assert "https://quotes.toscrape.com/" in pages

    @patch("src.crawler.time.sleep")
    @patch("src.crawler.requests.get")
    def test_crawl_respects_politeness_window(self, mock_get, mock_sleep):
        mock_response = MagicMock()
        mock_response.text = "<html><body><p>hello</p></body></html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        c = Crawler("https://quotes.toscrape.com/", politeness_delay=6)
        c.crawl()

        # sleep must always be called with 6 seconds
        mock_sleep.assert_called_with(6)

    @patch("src.crawler.time.sleep")
    @patch("src.crawler.requests.get")
    def test_crawl_handles_network_error(self, mock_get, mock_sleep):
        # Simulate a network failure
        mock_get.side_effect = Exception("Network error")

        c = Crawler("https://quotes.toscrape.com/")
        pages = c.crawl()

        # Should return empty dict, not crash
        assert pages == {}

    @patch("src.crawler.time.sleep")
    @patch("src.crawler.requests.get")
    def test_crawl_does_not_visit_same_url_twice(self, mock_get, mock_sleep):
        mock_response = MagicMock()
        # Page links back to itself
        mock_response.text = '<a href="/">Home</a>'
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        c = Crawler("https://quotes.toscrape.com/")
        c.crawl()

        # requests.get should only be called once despite the self-link
        assert mock_get.call_count == 1