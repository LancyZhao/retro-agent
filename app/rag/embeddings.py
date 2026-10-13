"""Embeddings.

Default is an offline, deterministic hashing embedding (no model download, no
network) so RAG works in CI/demos. If EMBED_BASE_URL + EMBED_API_KEY are set,
calls an OpenAI-compatible `/embeddings` endpoint instead.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import urllib.request

from app.config import Settings

_DIM = 256
_TOKEN = re.compile(r"[A-Za-z0-9_]+|[一-鿿]")


def _hash_embed(text: str) -> list[float]:
    """Bag-of-tokens hashed into a fixed-dim, L2-normalized vector."""
    vec = [0.0] * _DIM
    for tok in _TOKEN.findall(text.lower()):
        h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
        idx = h % _DIM
        sign = 1.0 if (h >> 8) & 1 else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class Embedder:
    def __init__(self, settings: Settings) -> None:
        self.s = settings
        self.offline = not (settings.embed_base_url and settings.embed_api_key)
        self.name = "hash-256" if self.offline else settings.embed_model

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self.offline:
            return [_hash_embed(t) for t in texts]
        return self._remote_embed(texts)

    def _remote_embed(self, texts: list[str]) -> list[list[float]]:
        url = self.s.embed_base_url.rstrip("/") + "/embeddings"
        req = urllib.request.Request(
            url, data=json.dumps({"model": self.s.embed_model, "input": texts}).encode(),
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.s.embed_api_key}"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode())
        return [row["embedding"] for row in body["data"]]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)
