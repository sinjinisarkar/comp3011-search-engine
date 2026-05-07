# tests/test_main.py
from unittest.mock import patch, MagicMock
import pytest
from src.main import main


def run_main_with_inputs(inputs):
    """Helper to run main() with a list of simulated user inputs."""
    with patch("builtins.input", side_effect=inputs):
        try:
            main()
        except StopIteration:
            pass


class TestMainCLI:
    def test_quit_command(self):
        """Test that quit exits cleanly."""
        run_main_with_inputs(["quit"])

    def test_exit_command(self):
        """Test that exit also works."""
        run_main_with_inputs(["exit"])

    def test_empty_input_continues(self):
        """Test that empty input doesn't crash."""
        run_main_with_inputs(["", "quit"])

    def test_unknown_command(self, capsys):
        """Test that unknown commands show helpful message."""
        run_main_with_inputs(["unknowncommand", "quit"])
        captured = capsys.readouterr()
        assert "Unknown command" in captured.out

    def test_print_without_load(self, capsys):
        """Test print before loading index shows error."""
        run_main_with_inputs(["print good", "quit"])
        captured = capsys.readouterr()
        assert "No index loaded" in captured.out

    def test_find_without_load(self, capsys):
        """Test find before loading index shows error."""
        run_main_with_inputs(["find good", "quit"])
        captured = capsys.readouterr()
        assert "No index loaded" in captured.out

    def test_suggest_without_load(self, capsys):
        """Test suggest before loading index shows error."""
        run_main_with_inputs(["suggest fri", "quit"])
        captured = capsys.readouterr()
        assert "No index loaded" in captured.out

    def test_print_no_argument(self, capsys):
        """Test print with no word shows usage."""
        run_main_with_inputs(["print good", "quit"])
        captured = capsys.readouterr()
        assert "No index loaded" in captured.out

    def test_find_no_argument(self, capsys):
        """Test find with no argument shows usage."""
        run_main_with_inputs(["find good", "quit"])
        captured = capsys.readouterr()
        assert "No index loaded" in captured.out

    def test_load_success(self, capsys):
        """Test load when index file exists loads successfully."""
        run_main_with_inputs(["load", "quit"])
        captured = capsys.readouterr()
        assert "Index loaded" in captured.out

    @patch("src.main.Crawler")
    @patch("src.main.Indexer")
    def test_build_command(self, mock_indexer_class, mock_crawler_class, capsys):
        """Test build command runs crawler and indexer."""
        mock_crawler = MagicMock()
        mock_crawler.crawl.return_value = {
            "http://example.com": "<html><body>hello</body></html>"
        }
        mock_crawler_class.return_value = mock_crawler

        mock_indexer = MagicMock()
        mock_indexer.index = {}
        mock_indexer.doc_lengths = {}
        mock_indexer_class.return_value = mock_indexer

        run_main_with_inputs(["build", "quit"])
        captured = capsys.readouterr()
        assert "Build complete" in captured.out

    @patch("src.main.Crawler")
    @patch("src.main.Indexer")
    def test_print_after_build(self, mock_indexer_class, mock_crawler_class, capsys):
        """Test print works after build."""
        mock_crawler = MagicMock()
        mock_crawler.crawl.return_value = {}
        mock_crawler_class.return_value = mock_crawler

        mock_indexer = MagicMock()
        mock_indexer.index = {
            "good": {
                "http://example.com": {
                    "frequency": 1,
                    "positions": [1]
                }
            }
        }
        mock_indexer.doc_lengths = {"http://example.com": 10}
        mock_indexer_class.return_value = mock_indexer

        run_main_with_inputs(["build", "print good", "quit"])
        captured = capsys.readouterr()
        assert "Build complete" in captured.out

    
    def test_help_command(self, capsys):
        """Test that help command shows all available commands."""
        run_main_with_inputs(["help", "quit"])
        captured = capsys.readouterr()
        assert "Available Commands" in captured.out
        assert "build" in captured.out
        assert "load" in captured.out
        assert "print" in captured.out
        assert "find" in captured.out
        assert "suggest" in captured.out
        assert "quit" in captured.out

    def test_suggest_no_argument(self, capsys):
        """Test suggest with no argument shows usage."""
        run_main_with_inputs(["suggest", "quit"])
        captured = capsys.readouterr()
        assert "No index loaded" in captured.out