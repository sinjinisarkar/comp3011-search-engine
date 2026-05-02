import re
import json
from pathlib import Path
from bs4 import BeautifulSoup


class Indexer:
    def __init__(self):
        """Initialise the indexer with an empty index."""
        self.index: dict = {}
        self.doc_lengths: dict[str, int] = {}  # tracks token count per page

    def _extract_text(self, html: str) -> str:
        """
        Extract only visible text from HTML.
        Removes script tags, style tags, and HTML markup.
        """
        soup = BeautifulSoup(html, "html.parser")
        # Remove script and style elements — we don't want to index JS/CSS
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator=" ")

    def _tokenise(self, text: str) -> list[str]:
        """
        Convert raw text into a list of lowercase words.
        Strips punctuation and numbers — letters only.
        Case insensitive as per spec ('Good' == 'good').
        """
        text = text.lower()
        words = re.findall(r'[a-z]+', text)
        return words

    def build(self, pages: dict[str, str]) -> None:
        """
        Build the inverted index from crawled pages.

        Index structure (dictionary of dictionaries):
        {
            "word": {
                "url": {
                    "frequency": 3,
                    "positions": [5, 23, 47]
                }
            }
        }

        This is O(1) lookup by word then by URL — industry standard design.
        pages = {url: html_text}
        """
        self.index = {}

        for url, html in pages.items():
            text = self._extract_text(html)
            words = self._tokenise(text)
            self.doc_lengths[url] = len(words)

            for position, word in enumerate(words):
                # Add word to index if not seen before
                if word not in self.index:
                    self.index[word] = {}

                # Add URL entry for this word if not seen before
                if url not in self.index[word]:
                    self.index[word][url] = {
                        "frequency": 0,
                        "positions": []
                    }

                # Update frequency and positions
                self.index[word][url]["frequency"] += 1
                self.index[word][url]["positions"].append(position)

    def save(self, filepath: str) -> None:
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "index": self.index,
            "doc_lengths": self.doc_lengths
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Index saved to {filepath} ({len(self.index)} unique words)")

    def load(self, filepath: str) -> None:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(
                f"No index found at {filepath}. Run 'build' first."
            )
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.index = data["index"]
        self.doc_lengths = data["doc_lengths"]
        print(f"Index loaded from {filepath} ({len(self.index)} unique words)")