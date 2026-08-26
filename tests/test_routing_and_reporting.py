from pathlib import Path

from sentinel.agents import supervisor
from sentinel.models.schemas import RouteDecision
from sentinel.reporting.pdf import write_incident_pdf
from sentinel.workflows import workflow as workflow_module


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
            "explanation": "The finding was confirmed.",
            "findings": ["indicator <one>"],
            "recommendations": ["isolate safely"],
        },
    }
    written = Path(write_incident_pdf(report, output_path))
    assert written.exists()
    assert written.read_bytes().startswith(b"%PDF")
    assert written.stat().st_size > 1_000


def test_rejected_report_is_not_written(monkeypatch, tmp_path):
    output_path = tmp_path / "rejected.pdf"

    def unexpected_write(*_args, **_kwargs):
        raise AssertionError("The PDF writer must not run for a rejected report")

    monkeypatch.setattr(workflow_module, "write_incident_pdf", unexpected_write)
    result = workflow_module.finalize_report.func(
        {"approved": False}, str(output_path)
    )

    assert result == {"status": "not_approved", "output_path": None}
    assert not output_path.exists()
