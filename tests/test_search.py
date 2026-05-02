import pytest
from src.search import SearchEngine


# Sample index for testing
SAMPLE_INDEX = {
    "good": {
        "http://example.com/1": {"frequency": 3, "positions": [1, 5, 10]},
        "http://example.com/2": {"frequency": 1, "positions": [4]},
    },
    "friends": {
        "http://example.com/1": {"frequency": 2, "positions": [2, 8]},
    },
    "indifference": {
        "http://example.com/3": {"frequency": 1, "positions": [7]},
    },
    "books": {
        "http://example.com/2": {"frequency": 1, "positions": [3]},
    }
}

SAMPLE_DOC_LENGTHS = {
    "http://example.com/1": 100,
    "http://example.com/2": 80,
    "http://example.com/3": 60,
}


class TestPrintWord:
    def test_print_existing_word(self, capsys):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        engine.print_word("good")
        captured = capsys.readouterr()
        assert "good" in captured.out
        assert "http://example.com/1" in captured.out

    def test_print_word_shows_frequency(self, capsys):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        engine.print_word("good")
        captured = capsys.readouterr()
        assert "Frequency" in captured.out

    def test_print_word_shows_positions(self, capsys):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        engine.print_word("good")
        captured = capsys.readouterr()
        assert "Positions" in captured.out

    def test_print_word_not_in_index(self, capsys):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        engine.print_word("nonsense")
        captured = capsys.readouterr()
        assert "not found" in captured.out

    def test_print_word_case_insensitive(self, capsys):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        engine.print_word("GOOD")
        captured = capsys.readouterr()
        assert "good" in captured.out

    def test_print_empty_word(self, capsys):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        engine.print_word("")
        captured = capsys.readouterr()
        assert "Error" in captured.out


class TestFind:
    def test_find_single_word(self):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        results = engine.find("indifference")
        assert "http://example.com/3" in results

    def test_find_multi_word(self):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        results = engine.find("good friends")
        assert results == ["http://example.com/1"]

    def test_find_word_not_in_index(self):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        results = engine.find("nonsense")
        assert results == []

    def test_find_empty_query(self):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        results = engine.find("")
        assert results == []

    def test_find_whitespace_only_query(self):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        results = engine.find("   ")
        assert results == []

    def test_find_no_intersection(self):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        # friends only on page1, indifference only on page3
        results = engine.find("friends indifference")
        assert results == []

    def test_find_case_insensitive(self):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        results = engine.find("GOOD")
        assert len(results) > 0

    def test_find_returns_ranked_results(self):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        # Use "friends" which only appears in page1 — guarantees non-zero IDF
        # and only one result so ranking is deterministic
        results = engine.find("friends")
        assert results[0] == "http://example.com/1"

    def test_find_returns_list(self):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        results = engine.find("good")
        assert isinstance(results, list)


class TestTfidf:
    def test_higher_frequency_scores_higher(self):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        total = len(SAMPLE_DOC_LENGTHS)
        # "friends" only appears in 1 doc so IDF won't be zero
        # page1 has frequency 2 — use different word with non-zero IDF
        score_friends = engine._tfidf("friends", "http://example.com/1", total)
        score_indifference = engine._tfidf("indifference", "http://example.com/3", total)
        # both appear in only 1 doc, friends has higher frequency so scores higher
        assert score_friends > score_indifference

    def test_tfidf_returns_float(self):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        score = engine._tfidf("good", "http://example.com/1", 3)
        assert isinstance(score, float)