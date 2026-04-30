# src/crawler.py
import requests
import time
from collections import deque
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse


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
        self.headers = {"User-Agent": "UniversityCrawler/1.0 (Educational Project)"}

    def _normalise_url(self, url: str) -> str:
        """
        Normalise a URL by:
        - Removing query parameters (?sort=asc etc)
        - Removing fragments (#section)
        - Enforcing a consistent trailing slash
        This prevents the same page being crawled multiple times.
        """
        parsed = urlparse(url)
        # Rebuild URL without query string or fragment
        normalised = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            "",   # params
            "",   # query — stripped
            ""    # fragment — stripped
        ))
        # Enforce trailing slash for consistency
        if not normalised.endswith("/"):
            normalised += "/"
        return normalised

    def _is_valid_url(self, url: str) -> bool:
        """
        Check the URL belongs to the same domain as base_url.
        Also filters out non-HTTP schemes like mailto: and javascript:
        We don't want to crawl outside quotes.toscrape.com
        """
        parsed = urlparse(url)
        base_parsed = urlparse(self.base_url)
        return (
            parsed.netloc == base_parsed.netloc and
            parsed.scheme in ("http", "https") and
            parsed.path != base_parsed.path  # ignore links that resolve to base
        )

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
            # Normalise — removes fragments, query params, enforces trailing slash
            full_url = self._normalise_url(full_url)
            if self._is_valid_url(full_url):
                links.append(full_url)
        return links

    def crawl(self) -> dict[str, str]:
        """
        Crawl the entire website using BFS (breadth-first search).
        Uses deque for O(1) popleft instead of O(n) list.pop(0).
        Returns a dict of {url: html_text} for every page visited.
        """
        pages: dict[str, str] = {}
        # deque is more efficient than list for BFS queue
        queue: deque[str] = deque([self._normalise_url(self.base_url)])
        # Track queued URLs separately to prevent duplicates entering queue
        queued: set[str] = {self._normalise_url(self.base_url)}

        while queue:
            url = queue.popleft()  # O(1) with deque vs O(n) with list

            if url in self.visited:
                continue

            try:
                print(f"Crawling: {url}")
                response = requests.get(url, timeout=10, headers=self.headers)
                response.raise_for_status()  # raises error for 4xx/5xx responses

                self.visited.add(url)
                pages[url] = response.text

                # Find new links and only add if not already queued or visited
                new_links = self._get_links(response.text, url)
                for link in new_links:
                    if link not in self.visited and link not in queued:
                        queue.append(link)
                        queued.add(link)

            except (requests.RequestException, Exception) as e:
                print(f"Error fetching {url}: {e}")

            # Always wait — even if the request failed
            time.sleep(self.politeness_delay)

        return pages