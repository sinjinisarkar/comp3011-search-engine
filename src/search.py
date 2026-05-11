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
        # Cache IDF values on startup — IDF depends only on the index,
        # not the query, so we compute once and reuse
        self._idf_cache: dict[str, float] = {}
        self._precompute_idf()

    def _precompute_idf(self) -> None:
        """
        Precompute IDF for every word in the index.
        IDF = log(total_docs / (1 + df))
        Cached to avoid redundant computation during search.
        """
        total_docs = len(self.doc_lengths)
        for word, postings in self.index.items():
            df = len(postings)
            self._idf_cache[word] = math.log(total_docs / (1 + df))

    def print_word(self, word: str) -> None:
        """
        Print the inverted index entry for a given word.
        Shows every page the word appears in, with frequency and positions.
        Sorted by frequency descending.
        """
        word = word.lower().strip()

        if not word:
            print("Error: please provide a word.")
            return

        if word not in self.index:
            print(f"\n  '{word}' not found in index.")
            return

        entries = self.index[word]
        total_occurrences = sum(e["frequency"] for e in entries.values())

        print(f"\n{'='*80}")
        print(f"  Index entry for '{word}'")
        print(f"  Found in {len(entries)} pages | {total_occurrences} total occurrences")
        print(f"{'='*80}")
        print(f"  {'URL':<60} {'Freq':>5}  Positions")
        print(f"  {'-'*75}")

        # Sort by frequency descending
        sorted_entries = sorted(
            entries.items(),
            key=lambda x: x[1]["frequency"],
            reverse=True
        )

        for url, stats in sorted_entries:
            positions_preview = str(stats["positions"][:3])
            if len(stats["positions"]) > 3:
                positions_preview = positions_preview[:-1] + ", ...]"
            print(f"  {url:<60} {stats['frequency']:>5}  {positions_preview}")

        print(f"{'='*80}")

    def find(self, query: str) -> list[str]:
        """
        Find all pages containing ALL words in the query.
        Optimisations applied:
        - Deduplicates query terms to avoid redundant intersection
        - Sorts terms by document frequency (rarest first) for faster intersection
        - Uses cached IDF values for scoring
        - Normalises TF by document length to avoid long-document bias
        Results are ranked by TF-IDF score (highest first).
        """
        if not query.strip():
            print("Error: empty query.")
            return []

        # Deduplicate query terms while preserving order
        seen = set()
        words = []
        for w in query.strip().lower().split():
            if w not in seen:
                seen.add(w)
                words.append(w)

        # Early exit if any word not in index
        for word in words:
            if word not in self.index:
                print(f"\n  '{word}' not found in index. No results.")
                return []

        # Sort words by document frequency ascending (rarest first)
        words.sort(key=lambda w: len(self.index[w]))

        # Intersect posting lists starting from smallest
        common_pages = set(self.index[words[0]].keys())
        for word in words[1:]:
            common_pages &= set(self.index[word].keys())
            if not common_pages:
                break

        if not common_pages:
            print(f"\n  No pages found containing all query terms: {', '.join(words)}")
            return []

        # Rank by combined TF-IDF score
        scored = []
        for url in common_pages:
            score = sum(self._tfidf(word, url) for word in words)
            scored.append((url, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        print(f"\n{'='*80}")
        print(f"  Results for '{query}'")
        print(f"  Found {len(scored)} page(s)")
        print(f"{'='*80}")
        print(f"  {'Rank':<6} {'Score':<12} URL")
        print(f"  {'-'*75}")

        for rank, (url, score) in enumerate(scored, 1):
            print(f"  #{rank:<5} {score:<12.4f} {url}")

        print(f"{'='*80}")

        return [url for url, _ in scored]

    def _tfidf(self, word: str, url: str) -> float:
        """
        Calculate normalised TF-IDF score for a word in a document.
        TF  = frequency / document_length (normalised to avoid long-doc bias)
        IDF = precomputed log(total_docs / (1 + df))
        Higher score = more relevant result.
        """
        frequency = self.index[word][url]["frequency"]
        doc_length = self.doc_lengths.get(url, 1)
        tf = frequency / doc_length
        idf = self._idf_cache.get(word, 0.0)
        return tf * idf

    def suggest(self, partial: str) -> list[str]:
        """
        Suggest words from the index that start with the given prefix.
        Useful for query completion, an advanced feature beyond basic requirements.
        Returns up to 5 suggestions sorted alphabetically.
        """
        partial = partial.lower().strip()
        if not partial:
            return []
        suggestions = [
            word for word in self.index
            if word.startswith(partial)
        ]
        return sorted(suggestions)[:5]