from uuid import uuid4

from langgraph.types import Command

from sentinel.memory.store import cross_thread_memory_workflow
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
        "evidence": ["test evidence"],
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
                "reason": "Evidence was reviewed.",
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
