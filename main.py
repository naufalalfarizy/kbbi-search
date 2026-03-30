import json
from collections import defaultdict
from pathlib import Path

DATA_FILE = "kbbi.json"
MAX_RESULTS_TO_SHOW = 100


def load_words(filepath: str) -> set[str]:
    """Load unique single-word entries from the KBBI JSON file."""
    with open(filepath, "r", encoding="utf-8") as file:
        data = json.load(file)

    words: set[str] = set()

    def add_word(word: str) -> None:
        if word and " " not in word:
            words.add(word.lower())

    for entry in data:
        add_word(entry.get("kata", ""))

        for variant in entry.get("varian", []):
            add_word(variant)

        for derivative in entry.get("turunan", []):
            add_word(derivative)

    return words


def build_indexes(words: set[str]):
    """Build helper indexes to speed up searching."""
    prefix_index = defaultdict(set)
    suffix_index = defaultdict(set)
    letter_index = defaultdict(set)

    for word in words:
        prefix_index[word[0]].add(word)
        suffix_index[word[-1]].add(word)

        for char in set(word):
            letter_index[char].add(word)

    return prefix_index, suffix_index, letter_index


def search_words(
    words: set[str],
    prefix_index,
    suffix_index,
    letter_index,
    prefix: str = "",
    root: str = "",
    suffix: str = "",
) -> list[str]:
    """
    Search words by:
    - prefix: word must start with this text
    - root: text must appear in the middle part of the word
    - suffix: word must end with this text

    The "middle part" means:
    - after the prefix
    - before the suffix
    """
    prefix = prefix.lower().strip()
    root = root.lower().strip()
    suffix = suffix.lower().strip()

    candidates = None

    if prefix:
        candidates = prefix_index.get(prefix[0], set()).copy()

    if root:
        for char in root:
            matching_words = letter_index.get(char, set())
            if candidates is None:
                candidates = matching_words.copy()
            else:
                candidates &= matching_words

    if suffix:
        matching_words = suffix_index.get(suffix[-1], set())
        if candidates is None:
            candidates = matching_words.copy()
        else:
            candidates &= matching_words

    if candidates is None:
        candidates = words

    results = []

    for word in candidates:
        if prefix and not word.startswith(prefix):
            continue

        if suffix and not word.endswith(suffix):
            continue

        if root:
            start = len(prefix) if prefix else 1
            end = len(word) - len(suffix) if suffix else len(word) - 1
            middle_part = word[start:end]

            if root not in middle_part:
                continue

        results.append(word)

    return sorted(results)


def main() -> None:
    if not Path(DATA_FILE).exists():
        print(f'File "{DATA_FILE}" not found.')
        return

    words = load_words(DATA_FILE)
    prefix_index, suffix_index, letter_index = build_indexes(words)

    print("Dictionary search\n")

    while True:
        prefix = input("Prefix (leave empty if none): ").strip()
        root = input("Middle (leave empty if none): ").strip()
        suffix = input("Suffix (leave empty if none): ").strip()

        results = search_words(
            words,
            prefix_index,
            suffix_index,
            letter_index,
            prefix=prefix,
            root=root,
            suffix=suffix,
        )

        print(f"\nFound {len(results)} result(s):")
        for word in results[:MAX_RESULTS_TO_SHOW]:
            print(word)

        if len(results) > MAX_RESULTS_TO_SHOW:
            print(f"... and {len(results) - MAX_RESULTS_TO_SHOW} more")

        print()


if __name__ == "__main__":
    main()