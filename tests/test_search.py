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
    
    def test_find_deduplicates_query_terms(self):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        # "good good" should behave same as "good"
        results1 = engine.find("good")
        results2 = engine.find("good good")
        assert results1 == results2

    def test_find_rarest_word_first_optimisation(self):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        # "friends good" and "good friends" should return same results
        results1 = engine.find("good friends")
        results2 = engine.find("friends good")
        assert results1 == results2


class TestTfidf:
    def test_higher_frequency_scores_higher(self):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        # friends has frequency 2, indifference has frequency 1
        # both appear in only 1 doc so IDF is the same
        # friends should score higher due to higher frequency
        score_friends = engine._tfidf("friends", "http://example.com/1")
        score_indifference = engine._tfidf("indifference", "http://example.com/3")
        assert score_friends > score_indifference

    def test_tfidf_returns_float(self):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        score = engine._tfidf("good", "http://example.com/1")
        assert isinstance(score, float)

class TestSuggest:
    def test_suggest_returns_matching_words(self):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        results = engine.suggest("fri")
        assert "friends" in results

    def test_suggest_empty_prefix_returns_empty(self):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        results = engine.suggest("")
        assert results == []

    def test_suggest_no_match_returns_empty(self):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        results = engine.suggest("xyz")
        assert results == []

    def test_suggest_returns_max_five(self):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        results = engine.suggest("g")
        assert len(results) <= 5

    def test_suggest_case_insensitive(self):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        results = engine.suggest("FRI")
        assert "friends" in results

    def test_suggest_returns_sorted(self):
        engine = SearchEngine(SAMPLE_INDEX, SAMPLE_DOC_LENGTHS)
        results = engine.suggest("g")
        assert results == sorted(results)