from pathlib import Path

from sentinel.agents import supervisor
from sentinel.models.schemas import RouteDecision
from sentinel.reporting.pdf import write_incident_pdf


def test_supervisor_uses_structured_llm_output(monkeypatch):
    class FakeStructured:
        def invoke(self, _messages):
            return RouteDecision(
                destination="file_agent",
                reason="The dominant artifact is a SHA-256 file hash.",
            )

    class FakeLLM:
        def __init__(self, **_kwargs):
            pass

        def with_structured_output(self, schema):
            assert schema is RouteDecision
            return FakeStructured()

    monkeypatch.setattr(supervisor, "require_openai", lambda: "test-key")
    monkeypatch.setattr(supervisor, "ChatOpenAI", FakeLLM)
    result = supervisor.route_request("Please investigate this artifact")
    assert isinstance(result, RouteDecision)
    assert result.destination == "file_agent"


def test_approved_report_is_written_as_pdf(tmp_path):
    output_path = tmp_path / "incident.pdf"
    report = {
        "title": "Sentinel AI Test Report",
        "summary": "Approved by analyst <reviewer>.",
        "severity": "high",
        "approved": True,
        "analysis": {
            "verdict": "malicious",
            "confidence": 0.9,
            "threat_type": "test",
            "explanation": "Evidence was confirmed.",
            "evidence": ["indicator <one>"],
            "recommendations": ["isolate safely"],
        },
    }
    written = Path(write_incident_pdf(report, output_path))
    assert written.exists()
    assert written.read_bytes().startswith(b"%PDF")
    assert written.stat().st_size > 1_000
