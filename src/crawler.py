import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class Crawler:
    def __init__(self, base_url: str, politeness_delay: int = 6):
        """
        Initialise the crawler.
        base_url: the starting URL to crawl from
        politeness_delay: seconds to wait between requests (min 6 as per spec)
        """
        self.base_url = base_url
        self.politeness_delay = politeness_delay
        self.visited: set[str] = set()

    def _is_valid_url(self, url: str) -> bool:
        """
        Check the URL belongs to the same domain as base_url.
        We don't want to crawl outside quotes.toscrape.com
        """
        parsed = urlparse(url)
        base_parsed = urlparse(self.base_url)
        return parsed.netloc == base_parsed.netloc

    def _get_links(self, html: str, current_url: str) -> list[str]:
        """
        Extract all valid internal links from a page.
        html: raw HTML string
        current_url: the URL this HTML came from (needed to resolve relative links)
        """
        soup = BeautifulSoup(html, "html.parser")
        links = []
        for tag in soup.find_all("a", href=True):
            # Convert relative URLs like /page/2/ to full URLs
            full_url = urljoin(current_url, tag["href"])
            # Remove fragments e.g. /page/1/#section
            full_url = full_url.split("#")[0]
            if self._is_valid_url(full_url) and full_url not in self.visited:
                links.append(full_url)
        return links

    def crawl(self) -> dict[str, str]:
        """
        Crawl the entire website using BFS (breadth-first search).
        Returns a dict of {url: html_text} for every page visited.
        """
        pages: dict[str, str] = {}
        queue = [self.base_url]

        while queue:
            url = queue.pop(0)

            if url in self.visited:
                continue

            try:
                print(f"Crawling: {url}")
                response = requests.get(url, timeout=10)
                response.raise_for_status()  # raises error for 4xx/5xx responses

                self.visited.add(url)
                pages[url] = response.text

                # Find new links on this page and add to queue
                new_links = self._get_links(response.text, url)
                queue.extend(new_links)

            except (requests.RequestException, Exception) as e:
                print(f"Error fetching {url}: {e}")

            # Always wait, even if the request failed
            time.sleep(self.politeness_delay)

        return pages