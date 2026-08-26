from uuid import uuid4

from langchain_core.documents import Document
from langgraph.types import Command

from sentinel.memory.store import cross_thread_memory_workflow
from sentinel.models.schemas import (
    RouteDecision,
    SpecialistAssessment,
    SpecialistResult,
    ThreatAnalysis,
    ToolObservation,
)
from sentinel.workflows import workflow as workflow_module
from sentinel.workflows.reliability_demo import reliability_demo
from sentinel.workflows.workflow import approval_gate_demo


def test_long_term_fact_crosses_thread_boundary():
    suffix = str(uuid4())
    analyst_id = f"analyst-{suffix}"
    config_a = {"configurable": {"thread_id": f"thread-A-{suffix}"}}
    config_b = {"configurable": {"thread_id": f"thread-B-{suffix}"}}
    written = cross_thread_memory_workflow.invoke(
        {
            "operation": "write",
            "thread_label": "thread-A",
            "analyst_id": analyst_id,
            "key": "report_format",
            "value": "PDF",
        },
        config_a,
    )
    read = cross_thread_memory_workflow.invoke(
        {
            "operation": "read",
            "thread_label": "thread-B",
            "analyst_id": analyst_id,
            "key": "report_format",
        },
        config_b,
    )
    assert written["thread_label"] == "thread-A"
    assert read["thread_label"] == "thread-B"
    assert read["value"] == "PDF"


def test_interrupt_and_command_resume_complete_same_thread():
    config = {"configurable": {"thread_id": f"approval-{uuid4()}"}}
    analysis = {
        "verdict": "malicious",
        "confidence": 0.91,
        "threat_type": "credential_phishing",
        "explanation": "Deterministic approval-gate test.",
        "findings": ["test finding"],
        "recommendations": ["review before persistence"],
        "requires_human_approval": True,
    }
    first = approval_gate_demo.invoke({"analysis": analysis}, config)
    assert "__interrupt__" in first
    assert first["__interrupt__"][0].value["action"] == "persist_final_incident_report"

    resumed = approval_gate_demo.invoke(
        Command(
            resume={
                "approved": True,
                "reviewer": "automated test analyst",
                "reason": "Findings were reviewed.",
            }
        ),
        config,
    )
    assert resumed["approved"] is True
    assert resumed["reviewer"] == "automated test analyst"


def test_retry_policy_and_controlled_fallback_both_fire():
    result = reliability_demo.invoke({"run_id": str(uuid4())})
    assert result["retry_policy"] == "RetryPolicy"
    assert result["retry_result"] == {"status": "recovered", "attempts": 3}
    assert result["fallback_result"]["strategy"] == "controlled_fallback"
    assert result["fallback_result"]["verdict"] == "unknown"


def test_full_workflow_interrupts_resumes_and_writes_report(monkeypatch, tmp_path):
    class FakeRetriever:
        def invoke(self, _request):
            return [
                Document(
                    page_content="Preserve headers and require approval.",
                    metadata={"source": "test-corpus.md"},
                )
            ]

    specialist = SpecialistResult(
        destination="email_agent",
        assessment=SpecialistAssessment(
            summary="A credential request was observed.",
            notable_indicators=["credential request"],
            limitations=[],
        ),
        tool_observations=[
            ToolObservation(
                tool_name="extract_email_indicators",
                arguments={"raw_email": "test"},
                output={"urls": ["https://example.invalid"]},
                status="success",
                latency_ms=1,
            )
        ],
    )
    analysis = ThreatAnalysis(
        verdict="malicious",
        confidence=0.92,
        threat_type="credential_phishing",
        explanation="Structured findings support escalation.",
        findings=["credential request"],
        recommendations=["isolate the message"],
        requires_human_approval=True,
    )
    monkeypatch.setattr(
        workflow_module,
        "route_request",
        lambda _request: RouteDecision(
            destination="email_agent", reason="The dominant artifact is a raw email."
        ),
    )
    monkeypatch.setattr(workflow_module, "run_email_agent", lambda _request: specialist)
    monkeypatch.setattr(
        workflow_module, "analyze_with_context", lambda _request, _context: analysis
    )
    workflow_module.set_retriever(FakeRetriever())

    config = {"configurable": {"thread_id": f"full-workflow-{uuid4()}"}}
    output_path = tmp_path / "approved.pdf"
    first = workflow_module.sentinel_workflow.invoke(
        {
            "request": "Review this raw email",
            "force_human_review": True,
            "output_path": str(output_path),
        },
        config,
    )
    assert "__interrupt__" in first
    assert workflow_module.sentinel_workflow.get_state(config).next

    resumed = workflow_module.sentinel_workflow.invoke(
        Command(
            resume={
                "approved": True,
                "reviewer": "test analyst",
                "reason": "Findings reviewed.",
            }
        ),
        config,
    )
    assert resumed["route"]["destination"] == "email_agent"
    assert resumed["executed_tool_count"] == 1
    assert resumed["retrieved_documents"] == 1
    assert resumed["finalization"]["status"] == "written"
    assert output_path.exists()


def test_full_workflow_fails_safe_when_specialist_breaks(monkeypatch):
    monkeypatch.setattr(
        workflow_module,
        "route_request",
        lambda _request: RouteDecision(
            destination="email_agent", reason="The dominant artifact is a raw email."
        ),
    )
    monkeypatch.setattr(
        workflow_module,
        "run_email_agent",
        lambda _request: (_ for _ in ()).throw(RuntimeError("provider offline")),
    )
    result = workflow_module.sentinel_workflow.invoke(
        {"request": "Review this raw email"},
        {"configurable": {"thread_id": f"fallback-{uuid4()}"}},
    )
    assert result["report"]["analysis"]["verdict"] == "unknown"
    assert result["report"]["analysis"]["confidence"] == 0.0
    assert "RuntimeError" in result["report"]["analysis"]["findings"][0]
