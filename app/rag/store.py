"""A minimal in-memory vector store for RAG.

Deliberately dependency-free (no faiss/chroma): fine for a knowledge base of
hundreds of chunks, and keeps the demo one `pip install` lighter. Swap this
class for a real vector DB behind the same `add`/`search` interface.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.rag.embeddings import Embedder, cosine
from app.schemas import Document, RetrievedChunk


def _chunk(text: str, size: int = 600, overlap: int = 80) -> list[str]:
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []
    out, start = [], 0
    while start < len(text):
        out.append(text[start:start + size])
        start += size - overlap
    return out


@dataclass
class _Entry:
    document_id: str
    source: str
    title: str
    text: str
    vector: list[float]


class VectorStore:
    def __init__(self, embedder: Embedder) -> None:
        self.embedder = embedder
        self._entries: list[_Entry] = []

    def __len__(self) -> int:
        return len(self._entries)

    def add(self, docs: list[Document]) -> int:
        chunks: list[tuple[Document, str]] = []
        for d in docs:
            for piece in _chunk(d.content):
                chunks.append((d, piece))
        if not chunks:
            return 0
        vectors = self.embedder.embed([p for _, p in chunks])
        for (d, piece), vec in zip(chunks, vectors):
            self._entries.append(_Entry(d.id, d.source, d.title, piece, vec))
        return len(chunks)

    def search(self, query: str, k: int = 4) -> list[RetrievedChunk]:
        if not self._entries:
            return []
        qvec = self.embedder.embed([query])[0]
        scored = [
            (cosine(qvec, e.vector), e) for e in self._entries
        ]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            RetrievedChunk(document_id=e.document_id, source=e.source, title=e.title,
                           snippet=e.text, score=round(score, 4))
            for score, e in scored[:k]
        ]
