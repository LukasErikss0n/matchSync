"""Typo-tolerant, multi-field search matching (e.g. team names against league
names/abbreviations like "prem", "champions league", "champ", "uefa")."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

_WORD_RE = re.compile(r"[a-z0-9]+")

_EXACT_SCORE = 100.0
_PREFIX_SCORE = 90.0
_SUBSTRING_SCORE = 75.0
_ACRONYM_SCORE = 85.0
_ACRONYM_PREFIX_SCORE = 70.0
_TOKEN_PREFIX_SCORE = 60.0
_FUZZY_WEIGHT = 40.0
_FUZZY_THRESHOLD = 0.72


def _tokenize(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def _acronym(tokens: list[str]) -> str:
    return "".join(t[0] for t in tokens if t)


def _field_score(query_tokens: list[str], query: str, text: str) -> float:
    if not text:
        return 0.0
    text_l = text.lower()
    tokens = _tokenize(text)
    if not tokens:
        return 0.0

    if text_l == query:
        return _EXACT_SCORE
    if text_l.startswith(query):
        return _PREFIX_SCORE
    if query in text_l:
        return _SUBSTRING_SCORE

    acronym = _acronym(tokens)
    if len(query) >= 2:
        if acronym == query:
            return _ACRONYM_SCORE
        if acronym.startswith(query):
            return _ACRONYM_PREFIX_SCORE

    # Every query word must be a prefix of some distinct word in the target,
    # e.g. "champ" -> "Champions", "uefa champ" -> "UEFA Champions League".
    remaining = list(tokens)
    matched = 0
    for qt in query_tokens:
        for i, t in enumerate(remaining):
            if t.startswith(qt):
                matched += 1
                del remaining[i]
                break
    if query_tokens and matched == len(query_tokens):
        return _TOKEN_PREFIX_SCORE

    # Fuzzy fallback for typos, e.g. "champions leauge" -> "Champions League".
    best_ratio = SequenceMatcher(None, query, text_l).ratio()
    for t in tokens:
        best_ratio = max(best_ratio, SequenceMatcher(None, query, t).ratio())
    if best_ratio >= _FUZZY_THRESHOLD:
        return _FUZZY_WEIGHT * best_ratio

    return 0.0


def match_score(query: str, *fields: str) -> float:
    """Best relevance score of `query` against any of `fields` (0 = no match)."""
    query = query.strip().lower()
    if not query:
        return 1.0
    query_tokens = _tokenize(query)
    if not query_tokens:
        return 0.0
    return max((_field_score(query_tokens, query, f) for f in fields if f), default=0.0)
