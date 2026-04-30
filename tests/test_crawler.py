# tests/test_crawler.py
import pytest
from unittest.mock import patch, MagicMock
from src.crawler import Crawler


class TestNormaliseUrl:
    def test_removes_query_params(self):
        c = Crawler("https://quotes.toscrape.com/")
        result = c._normalise_url("https://quotes.toscrape.com/page/2/?sort=asc")
        assert "sort" not in result

    def test_removes_fragments(self):
        c = Crawler("https://quotes.toscrape.com/")
        result = c._normalise_url("https://quotes.toscrape.com/page/1/#section")
        assert "#" not in result

    def test_enforces_trailing_slash(self):
        c = Crawler("https://quotes.toscrape.com/")
        result = c._normalise_url("https://quotes.toscrape.com/page/2")
        assert result.endswith("/")

    def test_keeps_trailing_slash_if_present(self):
        c = Crawler("https://quotes.toscrape.com/")
        result = c._normalise_url("https://quotes.toscrape.com/page/2/")
        assert result == "https://quotes.toscrape.com/page/2/"


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

    def test_no_links_returns_empty(self):
        c = Crawler("https://quotes.toscrape.com/")
        html = "<html><body><p>No links here</p></body></html>"
        links = c._get_links(html, "https://quotes.toscrape.com/")
        assert links == []

    def test_no_fragments_in_results(self):
        c = Crawler("https://quotes.toscrape.com/")
        html = '<a href="/page/1/#section">Link</a>'
        links = c._get_links(html, "https://quotes.toscrape.com/")
        for link in links:
            assert "#" not in link


class TestCrawl:
    @patch("src.crawler.time.sleep")
    @patch("src.crawler.requests.get")
    def test_crawl_returns_pages(self, mock_get, mock_sleep):
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

        mock_sleep.assert_called_with(6)

    @patch("src.crawler.time.sleep")
    @patch("src.crawler.requests.get")
    def test_crawl_handles_network_error(self, mock_get, mock_sleep):
        mock_get.side_effect = Exception("Network error")

        c = Crawler("https://quotes.toscrape.com/")
        pages = c.crawl()

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

        # Should only be called once despite self-link
        assert mock_get.call_count == 1

    @patch("src.crawler.time.sleep")
    @patch("src.crawler.requests.get")
    def test_no_duplicate_urls_in_queue(self, mock_get, mock_sleep):
        mock_response = MagicMock()
        # Two links to the same page from one page
        mock_response.text = '''
            <a href="/page/2/">Next</a>
            <a href="/page/2/">Next again</a>
        '''
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        c = Crawler("https://quotes.toscrape.com/")
        c.crawl()

        # Page 2 should only be fetched once despite appearing twice
        urls_fetched = [call[0][0] for call in mock_get.call_args_list]
        assert urls_fetched.count("https://quotes.toscrape.com/page/2/") <= 1

    @patch("src.crawler.time.sleep")
    @patch("src.crawler.requests.get")
    def test_user_agent_header_sent(self, mock_get, mock_sleep):
        mock_response = MagicMock()
        mock_response.text = "<html><body></body></html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        c = Crawler("https://quotes.toscrape.com/")
        c.crawl()

        # Check User-Agent header was included in the request
        call_kwargs = mock_get.call_args[1]
        assert "User-Agent" in call_kwargs["headers"]