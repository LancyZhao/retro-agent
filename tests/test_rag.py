from app.config import get_settings
from app.rag.embeddings import Embedder, cosine
from app.rag.store import VectorStore
from app.schemas import Document


def test_offline_embeddings_are_deterministic():
    emb = Embedder(get_settings())
    a = emb.embed(["redis connection pool timeout"])[0]
    b = emb.embed(["redis connection pool timeout"])[0]
    assert a == b
    assert abs(sum(x * x for x in a) - 1.0) < 1e-6  # L2-normalized


def test_similar_text_scores_higher():
    emb = Embedder(get_settings())
    q = emb.embed(["redis timeout connection pool"])[0]
    near = emb.embed(["redis connection pool exhausted causes timeout"])[0]
    far = emb.embed(["banana smoothie recipe"])[0]
    assert cosine(q, near) > cosine(q, far)


def test_vector_store_retrieves_relevant_chunk():
    emb = Embedder(get_settings())
    store = VectorStore(emb)
    store.add([
        Document(id="kb:redis", source="kb", title="redis",
                 content="Redis connection pool exhaustion leads to request timeout at peak QPS."),
        Document(id="kb:cake", source="kb", title="cake",
                 content="A sponge cake needs flour, eggs and sugar."),
    ])
    hits = store.search("why do we see redis timeout under load", k=1)
    assert hits and hits[0].document_id == "kb:redis"
