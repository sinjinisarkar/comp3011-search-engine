import math


class SearchEngine:
    def __init__(self, index: dict, doc_lengths: dict[str, int]):
        """
        Initialise the search engine.
        index: the inverted index from Indexer
        doc_lengths: number of tokens per document (used for TF-IDF normalisation)
        """
        self.index = index
        self.doc_lengths = doc_lengths

    def print_word(self, word: str) -> None:
        """
        Print the inverted index entry for a given word.
        Shows every page the word appears in, with frequency and positions.
        """
        word = word.lower().strip()

        if not word:
            print("Error: please provide a word.")
            return

        if word not in self.index:
            print(f"'{word}' not found in index.")
            return

        print(f"\nIndex entry for '{word}':")
        for url, stats in self.index[word].items():
            print(f"  {url}")
            print(f"    Frequency : {stats['frequency']}")
            print(f"    Positions : {stats['positions']}")

    def find(self, query: str) -> list[str]:
        """
        Find all pages containing ALL words in the query.
        Results are ranked by TF-IDF score (highest first).
        Supports single and multi-word queries.
        """
        if not query.strip():
            print("Error: empty query.")
            return []

        words = [w.lower() for w in query.strip().split()]

        # Find pages containing ALL query words (set intersection)
        matching_sets = []
        for word in words:
            if word not in self.index:
                print(f"'{word}' not found in index. No results.")
                return []
            matching_sets.append(set(self.index[word].keys()))

        common_pages = set.intersection(*matching_sets)

        if not common_pages:
            print("No pages found containing all query terms.")
            return []

        # Rank by combined TF-IDF score across all query words
        total_docs = len(self.doc_lengths)
        scored = []
        for url in common_pages:
            score = sum(
                self._tfidf(word, url, total_docs) for word in words
            )
            scored.append((url, score))

        # Sort highest score first
        scored.sort(key=lambda x: x[1], reverse=True)

        print(f"\nFound {len(scored)} page(s) for '{query}':")
        for url, score in scored:
            print(f"  {url}  (score: {score:.4f})")

        return [url for url, _ in scored]

    def _tfidf(self, word: str, url: str, total_docs: int) -> float:
        """
        Calculate TF-IDF score for a word in a document.
        TF  = frequency of word in document
        IDF = log(total documents / documents containing word)
        Higher score = more relevant result.
        """
        tf = self.index[word][url]["frequency"]
        df = len(self.index[word])  # number of docs containing this word
        idf = math.log(total_docs / (1 + df))
        return tf * idf