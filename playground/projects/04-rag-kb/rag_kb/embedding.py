"""Deterministic local embedding suitable for tests and examples."""

import hashlib
import math
import re
from collections.abc import Sequence

_TOKEN_PATTERN = re.compile(r"[a-z0-9_]+|[\u4e00-\u9fff]", re.IGNORECASE)


class FakeEmbedding:
    """Feature-hashing embedding backed by stable BLAKE2 digests.

    Python's built-in ``hash`` is intentionally randomized between processes,
    so it must not be used for reproducible embeddings.
    """

    def __init__(self, dimensions: int = 256) -> None:
        if dimensions < 8:
            raise ValueError("dimensions must be at least 8")
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in self._tokens(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=16).digest()
            index = int.from_bytes(digest[:8], "big") % self.dimensions
            sign = 1.0 if digest[8] & 1 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        return vector if norm == 0.0 else [value / norm for value in vector]

    def embed_many(self, texts: Sequence[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]

    @staticmethod
    def _tokens(text: str) -> list[str]:
        normalized = text.casefold()
        base = _TOKEN_PATTERN.findall(normalized)
        chinese = [token for token in base if "\u4e00" <= token <= "\u9fff"]
        bigrams = [
            chinese[index] + chinese[index + 1]
            for index in range(len(chinese) - 1)
        ]
        return base + bigrams
