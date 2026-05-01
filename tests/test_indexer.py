# tests/test_indexer.py
import pytest
import json
from src.indexer import Indexer


# Sample HTML pages for testing
SIMPLE_HTML = """
<html><body>
    <p>Good thoughts lead to good actions</p>
</body></html>
"""

HTML_WITH_SCRIPTS = """
<html>
    <head><script>var x = 1;</script></head>
    <body>
        <style>.good { color: red; }</style>
        <p>Good thoughts</p>
    </body>
</html>
"""

MULTI_PAGE = {
    "http://page1.com": "<html><body><p>good friends</p></body></html>",
    "http://page2.com": "<html><body><p>good books</p></body></html>",
}


class TestExtractText:
    def test_extracts_visible_text(self):
        idx = Indexer()
        text = idx._extract_text(SIMPLE_HTML)
        assert "good" in text.lower()

    def test_removes_script_tags(self):
        idx = Indexer()
        text = idx._extract_text(HTML_WITH_SCRIPTS)
        assert "var" not in text

    def test_removes_style_tags(self):
        idx = Indexer()
        text = idx._extract_text(HTML_WITH_SCRIPTS)
        assert "color" not in text

    def test_empty_html_returns_string(self):
        idx = Indexer()
        text = idx._extract_text("<html><body></body></html>")
        assert isinstance(text, str)


class TestTokenise:
    def test_lowercases_words(self):
        idx = Indexer()
        tokens = idx._tokenise("Hello WORLD Good")
        assert tokens == ["hello", "world", "good"]

    def test_strips_punctuation(self):
        idx = Indexer()
        tokens = idx._tokenise("it's good, really!")
        assert "good" in tokens
        assert "really" in tokens

    def test_strips_numbers(self):
        idx = Indexer()
        tokens = idx._tokenise("page 123 good")
        assert "123" not in tokens
        assert "good" in tokens

    def test_empty_string_returns_empty_list(self):
        idx = Indexer()
        tokens = idx._tokenise("")
        assert tokens == []

    def test_only_numbers_returns_empty(self):
        idx = Indexer()
        tokens = idx._tokenise("123 456 789")
        assert tokens == []


class TestBuild:
    def test_build_creates_index(self):
        idx = Indexer()
        idx.build({"http://example.com": SIMPLE_HTML})
        assert "good" in idx.index

    def test_build_records_correct_frequency(self):
        idx = Indexer()
        idx.build({"http://example.com": SIMPLE_HTML})
        # "good" appears twice in SIMPLE_HTML
        assert idx.index["good"]["http://example.com"]["frequency"] == 2

    def test_build_records_positions(self):
        idx = Indexer()
        idx.build({"http://example.com": SIMPLE_HTML})
        positions = idx.index["good"]["http://example.com"]["positions"]
        assert len(positions) == 2

    def test_build_multiple_pages(self):
        idx = Indexer()
        idx.build(MULTI_PAGE)
        # "good" should appear in both pages
        assert "http://page1.com" in idx.index["good"]
        assert "http://page2.com" in idx.index["good"]

    def test_build_word_only_on_one_page(self):
        idx = Indexer()
        idx.build(MULTI_PAGE)
        # "friends" only on page1
        assert "http://page1.com" in idx.index["friends"]
        assert "http://page2.com" not in idx.index["friends"]

    def test_build_is_case_insensitive(self):
        idx = Indexer()
        idx.build({"http://example.com": "<html><body>Good GOOD good</body></html>"})
        assert idx.index["good"]["http://example.com"]["frequency"] == 3

    def test_build_empty_pages_gives_empty_index(self):
        idx = Indexer()
        idx.build({})
        assert idx.index == {}

    def test_script_content_not_indexed(self):
        idx = Indexer()
        idx.build({"http://example.com": HTML_WITH_SCRIPTS})
        assert "var" not in idx.index


class TestSaveLoad:
    def test_save_creates_file(self, tmp_path):
        idx = Indexer()
        idx.build({"http://example.com": SIMPLE_HTML})
        path = str(tmp_path / "index.json")
        idx.save(path)
        assert (tmp_path / "index.json").exists()

    def test_save_creates_valid_json(self, tmp_path):
        idx = Indexer()
        idx.build({"http://example.com": SIMPLE_HTML})
        path = str(tmp_path / "index.json")
        idx.save(path)
        with open(path) as f:
            data = json.load(f)
        # index is now nested under "index" key
        assert "good" in data["index"]
        assert "doc_lengths" in data

    def test_load_restores_index(self, tmp_path):
        idx = Indexer()
        idx.build({"http://example.com": SIMPLE_HTML})
        path = str(tmp_path / "index.json")
        idx.save(path)

        idx2 = Indexer()
        idx2.load(path)
        assert "good" in idx2.index

    def test_load_missing_file_raises_error(self):
        idx = Indexer()
        with pytest.raises(FileNotFoundError):
            idx.load("/nonexistent/path/index.json")

    def test_save_and_load_preserves_frequency(self, tmp_path):
        idx = Indexer()
        idx.build({"http://example.com": SIMPLE_HTML})
        path = str(tmp_path / "index.json")
        idx.save(path)

        idx2 = Indexer()
        idx2.load(path)
        assert idx2.index["good"]["http://example.com"]["frequency"] == 2

    def test_save_creates_parent_directories(self, tmp_path):
        idx = Indexer()
        idx.build({"http://example.com": SIMPLE_HTML})
        # nested path that doesn't exist yet
        path = str(tmp_path / "nested" / "dir" / "index.json")
        idx.save(path)
        assert (tmp_path / "nested" / "dir" / "index.json").exists()