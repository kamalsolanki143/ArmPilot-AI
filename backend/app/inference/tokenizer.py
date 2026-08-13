"""
ArmPilot-AI — Tokenizer Utilities
Token counting, text truncation, and prompt length estimation.
"""

from __future__ import annotations

import re
from typing import Optional


# Average characters per token for common English text (rough estimate)
_CHARS_PER_TOKEN = 3.5


class TokenizerUtils:
    """Utilities for token counting and text manipulation."""

    def __init__(self) -> None:
        self._cache: dict[str, int] = {}

    def count_tokens(self, text: str) -> int:
        """Estimate token count for text. Uses cache for repeated strings."""
        if not text:
            return 0

        # Check cache (limited to avoid memory issues)
        if len(self._cache) > 10000:
            self._cache.clear()
        if text in self._cache:
            return self._cache[text]

        # Try tiktoken if available
        count = self._count_with_tiktoken(text)
        if count is None:
            count = self._estimate_tokens(text)

        self._cache[text] = count
        return count

    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """Truncate text to approximately max_tokens."""
        if not text:
            return text

        token_count = self.count_tokens(text)
        if token_count <= max_tokens:
            return text

        # Estimate character cutoff
        estimated_chars = int(max_tokens * _CHARS_PER_TOKEN)
        truncated = text[:estimated_chars]

        # Try to break at word boundary
        last_space = truncated.rfind(" ")
        if last_space > estimated_chars * 0.8:
            truncated = truncated[:last_space]

        return truncated + "..."

    def estimate_prompt_tokens(
        self,
        messages: list[dict[str, str]],
        overhead: int = 32,
    ) -> int:
        """Estimate total token count for a chat prompt."""
        total = overhead  # Token overhead for formatting
        for msg in messages:
            content = msg.get("content", "")
            total += self.count_tokens(content)
            total += 4  # Role + formatting tokens
        return total

    def fits_context(
        self,
        text: str,
        max_context: int,
        reserved: int = 256,
    ) -> bool:
        """Check if text fits within context window with reserved output space."""
        tokens = self.count_tokens(text)
        return tokens <= (max_context - reserved)

    def split_into_chunks(
        self,
        text: str,
        max_tokens_per_chunk: int,
        overlap_tokens: int = 50,
    ) -> list[str]:
        """Split text into chunks that fit within token limits."""
        if not text:
            return []

        total_tokens = self.count_tokens(text)
        if total_tokens <= max_tokens_per_chunk:
            return [text]

        # Estimate character-level split points
        chars_per_chunk = int(max_tokens_per_chunk * _CHARS_PER_TOKEN)
        overlap_chars = int(overlap_tokens * _CHARS_PER_TOKEN)

        chunks: list[str] = []
        start = 0

        while start < len(text):
            end = start + chars_per_chunk

            if end >= len(text):
                chunks.append(text[start:])
                break

            # Find a good break point (sentence or word boundary)
            break_point = self._find_break_point(text, start, end)
            chunks.append(text[start:break_point])

            start = break_point - overlap_chars
            if start < 0:
                start = break_point

        return chunks

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Estimate token count using character-based heuristic."""
        if not text:
            return 0

        # Count words and punctuation
        words = len(text.split())
        # Rough: ~1.3 tokens per word for English
        return max(1, int(words * 1.3))

    @staticmethod
    def _count_with_tiktoken(text: str) -> Optional[int]:
        """Try to count tokens using tiktoken."""
        try:
            import tiktoken
            encoder = tiktoken.get_encoding("cl100k_base")
            return len(encoder.encode(text))
        except (ImportError, Exception):
            return None

    @staticmethod
    def _find_break_point(text: str, start: int, end: int) -> int:
        """Find a good text break point near the end position."""
        # Prefer sentence boundaries
        for i in range(end, max(start, end - 200), -1):
            if i < len(text) and text[i] in ".!?\n":
                return i + 1

        # Prefer word boundaries
        for i in range(end, max(start, end - 100), -1):
            if i < len(text) and text[i] == " ":
                return i

        return end


# Singleton
tokenizer_utils = TokenizerUtils()
