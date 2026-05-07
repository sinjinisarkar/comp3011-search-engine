# src/main.py
import sys
import os

# Allow running directly from src/ folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.crawler import Crawler
from src.indexer import Indexer
from src.search import SearchEngine

INDEX_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "index.json")
BASE_URL = "https://quotes.toscrape.com/"


def print_help():
    """Print all available commands with descriptions."""
    print("\n" + "=" * 80)
    print("  Available Commands")
    print("=" * 80)
    print("  build              Crawl the website and build the index")
    print("  load               Load a previously saved index from disk")
    print("  print <word>       Show index entry for a word")
    print("  find <query>       Find pages containing all query words")
    print("  suggest <prefix>   Suggest words starting with a prefix")
    print("  help               Show this help message")
    print("  quit               Exit the program")
    print("=" * 80)


def main():
    indexer = Indexer()
    engine = None

    print("=" * 80)
    print("  Search Engine — COMP3011 Coursework 2")
    print("=" * 80)
    print("  Commands: build | load | print | find | suggest | help | quit")
    print("  Type 'help' for detailed command descriptions.")
    print("=" * 80)

    while True:
        try:
            raw = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not raw:
            continue

        parts = raw.split(maxsplit=1)
        command = parts[0].lower()
        argument = parts[1] if len(parts) > 1 else ""

        if command == "build":
            print("\nStarting crawl — this will take several minutes")
            print("due to the 6 second politeness window...")
            print("Please wait.\n")
            crawler = Crawler(BASE_URL)
            pages = crawler.crawl()
            print(f"\nCrawled {len(pages)} pages. Building index...")
            indexer.build(pages)
            indexer.save(INDEX_PATH)
            engine = SearchEngine(indexer.index, indexer.doc_lengths)
            print("Build complete! You can now use print and find commands.")

        elif command == "load":
            try:
                indexer.load(INDEX_PATH)
                engine = SearchEngine(indexer.index, indexer.doc_lengths)
                print("Index loaded. You can now use print and find commands.")
            except FileNotFoundError as e:
                print(f"Error: {e}")

        elif command == "print":
            if not engine:
                print("No index loaded. Run 'build' or 'load' first.")
            elif not argument:
                print("Usage: print <word>")
                print("Example: print good")
            else:
                engine.print_word(argument)

        elif command == "find":
            if not engine:
                print("No index loaded. Run 'build' or 'load' first.")
            elif not argument:
                print("Usage: find <word> [word2 ...]")
                print("Example: find good friends")
            else:
                engine.find(argument)

        elif command == "suggest":
            if not engine:
                print("No index loaded. Run 'build' or 'load' first.")
            elif not argument:
                print("Usage: suggest <partial word>")
                print("Example: suggest fri")
            else:
                suggestions = engine.suggest(argument)
                if suggestions:
                    print(f"\n{'='*80}")
                    print(f"  Suggestions for '{argument}'")
                    print(f"{'='*80}")
                    for word in suggestions:
                        count = len(engine.index[word])
                        print(f"  → {word:<20} (appears in {count} pages)")
                    print(f"{'='*80}")
                else:
                    print(f"\n  No suggestions found for '{argument}'")

        elif command == "help":
            print_help()

        elif command == "quit" or command == "exit":
            print("Goodbye!")
            break

        else:
            print(f"Unknown command: '{command}'")
            print("Type 'help' to see all available commands.")


if __name__ == "__main__":
    main()