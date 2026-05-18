import re

STOP_WORDS: set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
    "for", "of", "with", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "can", "shall",
    "not", "no", "i", "me", "my", "we", "our", "you", "your",
    "he", "she", "it", "they", "them", "this", "that", "these",
    "those", "get", "got", "make", "made", "go", "going",
    "some", "any", "all", "just", "very", "really", "too",
    "also", "only", "how", "what", "when", "where", "which",
    "from", "up", "down", "out", "off", "over", "into",
    "if", "then", "else", "than", "more", "much", "so",
    "de", "la", "le", "un", "une", "des", "les", "et",
    "en", "au", "aux", "du", "pour", "dans", "sur",
}


def extract_keywords(title: str) -> str:
    if not title or not title.strip():
        return ""
    words = re.findall(r'[a-zA-Z0-9一-鿿]+', title.lower().strip())
    seen: set[str] = set()
    result: list[str] = []
    for word in words:
        if len(word) >= 2 and word not in STOP_WORDS and word not in seen:
            seen.add(word)
            result.append(word)
    return ",".join(result)
