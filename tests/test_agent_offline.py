from app.agent.orchestrator import RetroAgent
from app.config import get_settings


def _agent():
    # Default settings use the mock LLM (no API key) and the sample data dirs.
    return RetroAgent(get_settings())


def test_offline_run_produces_grounded_report():
    report = _agent().run(period="2026-W41", connectors=["mock_oa", "markdown_logs"])
    assert report.model == "mock-retro-v1"
    assert report.summary
    assert report.highlights
    # The sample data plants a timeout incident; the agent must surface it.
    assert any("timeout" in i.lower() for i in report.issues)
    assert report.action_items
    # The 5-step plan is recorded in the trace.
    assert len(report.trace) == 5


def test_rag_evidence_is_attached():
    report = _agent().run(period="2026-W41", connectors=["mock_oa"])
    assert report.evidence, "expected retrieved knowledge-base evidence"
    # cosine similarity ranges in [-1, 1]
    assert all(-1.0 <= e.score <= 1.0 for e in report.evidence)


def test_report_serializes_to_dict():
    report = _agent().run(period="2026-W41", connectors=["mock_oa"])
    d = report.to_dict()
    assert {"period", "summary", "highlights", "issues", "action_items"} <= set(d)
    assert isinstance(d["action_items"], list)
