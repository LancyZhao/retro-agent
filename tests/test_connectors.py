from app.config import get_settings
from app.connectors import registry


def test_registry_lists_all():
    names = registry.available()
    assert {"mock_oa", "markdown_logs", "git_commits"} <= set(names)


def test_mock_oa_returns_docs():
    s = get_settings()
    (conn,) = [c for c in registry.build(["mock_oa"], s)]
    docs = conn.fetch("2026-W41")
    assert docs, "mock_oa should return sample docs"
    assert all(d.source == "mock_oa" for d in docs)
    assert any("timeout" in d.content.lower() for d in docs)


def test_markdown_logs_reads_sample():
    s = get_settings()
    (conn,) = registry.build(["markdown_logs"], s)
    docs = conn.fetch()
    stems = {d.title for d in docs}
    assert "2026-W41" in stems


def test_unknown_connector_raises():
    import pytest

    with pytest.raises(KeyError):
        registry.build(["does_not_exist"], get_settings())
