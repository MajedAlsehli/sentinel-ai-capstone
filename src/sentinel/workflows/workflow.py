"""Sentinel's LangGraph Functional API routing workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_store
from langgraph.func import entrypoint, task
from langgraph.types import RetryPolicy, interrupt

from sentinel.agents.analyzer import analyze_with_context
from sentinel.agents.specialists import (
    run_email_agent,
    run_file_agent,
    run_ip_agent,
    run_url_agent,
)
from sentinel.agents.supervisor import route_request
from sentinel.memory.store import analyst_namespace, store
from sentinel.models.schemas import (
    ApprovalDecision,
    FinalizationResult,
    IncidentReport,
    SpecialistResult,
    ThreatAnalysis,
)
from sentinel.reporting.pdf import write_incident_pdf


checkpointer = InMemorySaver()
approval_demo_checkpointer = InMemorySaver()
external_retry = RetryPolicy(
    initial_interval=0.2,
    backoff_factor=2.0,
    max_interval=2.0,
    max_attempts=3,
    jitter=False,
)

# The retriever remains process-local so graph input is serializable and safe to checkpoint.
_RETRIEVER = None


def set_retriever(retriever) -> None:
    global _RETRIEVER
    _RETRIEVER = retriever


@task(retry_policy=external_retry)
def classify(request: str) -> dict[str, Any]:
    return route_request(request).model_dump()


@task(retry_policy=external_retry)
def specialist_investigation(request: str, route: dict[str, Any]) -> dict[str, Any]:
    destination = route["destination"]
    runners = {
        "ip_agent": run_ip_agent,
        "url_agent": run_url_agent,
        "email_agent": run_email_agent,
        "file_agent": run_file_agent,
    }
    result: SpecialistResult = runners[destination](request)
    return result.model_dump()


@task
def retrieve_context(request: str) -> list[dict[str, str]]:
    if _RETRIEVER is None:
        raise RuntimeError("Retriever not initialized. Call set_retriever() first.")
    docs = _RETRIEVER.invoke(request)
    if not docs:
        raise RuntimeError("The retriever returned no documents.")
    return [
        {
            "content": document.page_content,
            "source": document.metadata.get("source", "unknown"),
        }
        for document in docs
    ]


@task(retry_policy=external_retry)
def analyze(
    request: str,
    specialist_result: dict[str, Any],
    context_items: list[dict[str, str]],
) -> dict[str, Any]:
    context = "\n\n".join(
        f"[{item['source']}]\n{item['content']}" for item in context_items
    )
    specialist = json.dumps(specialist_result, ensure_ascii=False, default=str)
    return analyze_with_context(
        request,
        f"Structured specialist evidence:\n{specialist}\n\nRAG context:\n{context}",
    ).model_dump()


@task
def fallback_analysis(request: str, error_type: str) -> dict[str, Any]:
    return ThreatAnalysis(
        verdict="unknown",
        confidence=0.0,
        threat_type="insufficient_evidence",
        explanation=(
            "The primary evidence pipeline failed, so Sentinel used its fail-safe "
            "unknown verdict instead of fabricating a conclusion."
        ),
        evidence=[f"Primary pipeline error handled by fallback: {error_type}"],
        recommendations=["Retry when the required model or evidence service is available."],
        requires_human_approval=False,
    ).model_dump()


@task
def human_approval(
    analysis: dict[str, Any], force_human_review: bool = False
) -> dict[str, Any]:
    requires_review = (
        force_human_review
        or analysis.get("requires_human_approval", False)
        or analysis.get("verdict") == "malicious"
    )
    if requires_review:
        return interrupt(
            {
                "action": "persist_final_incident_report",
                "question": "Approve persisting this incident report?",
                "analysis": analysis,
                "required_response": {
                    "approved": "boolean",
                    "reviewer": "name or role",
                    "reason": "review rationale",
                },
            }
        )
    return ApprovalDecision(
        approved=True,
        reviewer="Sentinel low-risk policy",
        reason="The assessment did not cross the mandatory review threshold.",
    ).model_dump()


@task
def generate_report(
    request: str,
    analysis: dict[str, Any],
    approval_payload: dict[str, Any],
) -> dict[str, Any]:
    approval = ApprovalDecision.model_validate(approval_payload)
    verdict = analysis["verdict"]
    severity = (
        "critical"
        if analysis["confidence"] >= 0.9 and verdict == "malicious"
        else "high"
        if verdict == "malicious"
        else "medium"
        if verdict == "suspicious"
        else "low"
    )
    return IncidentReport(
        title="Sentinel AI Security Investigation",
        summary=(
            f"Investigation request: {request}\n\n"
            f"Reviewer: {approval.reviewer}. Review rationale: {approval.reason}"
        ),
        severity=severity,
        analysis=ThreatAnalysis.model_validate(analysis),
        approved=approval.approved,
    ).model_dump()


@task
def finalize_report(
    report: dict[str, Any], output_path: str | None
) -> dict[str, Any]:
    if not report["approved"]:
        return FinalizationResult(status="not_approved").model_dump()
    if not output_path:
        return FinalizationResult(status="not_requested").model_dump()
    path = Path(output_path)
    if path.suffix.lower() != ".pdf":
        raise ValueError("Incident report output_path must end in .pdf")
    written_path = write_incident_pdf(report, path)
    return FinalizationResult(
        status="written", output_path=str(Path(written_path).resolve())
    ).model_dump()


@entrypoint(checkpointer=checkpointer, store=store)
def sentinel_workflow(inputs: dict[str, Any]):
    """Route, investigate, retrieve, analyze, approve, and persist one incident."""

    request = inputs["request"]
    analyst_id = inputs.get("analyst_id", "default")
    runtime_store = get_store()
    route = classify(request).result()
    specialist: dict[str, Any] | None = None
    context: list[dict[str, str]] = []
    try:
        specialist = specialist_investigation(request, route).result()
        context = retrieve_context(request).result()
        analysis = analyze(request, specialist, context).result()
    except Exception as exc:
        analysis = fallback_analysis(request, type(exc).__name__).result()

    approval = human_approval(
        analysis, bool(inputs.get("force_human_review", False))
    ).result()
    report = generate_report(request, analysis, approval).result()
    finalization = finalize_report(report, inputs.get("output_path")).result()

    runtime_store.put(
        analyst_namespace(analyst_id),
        "last_incident",
        {
            "request": request,
            "route": route["destination"],
            "verdict": report["analysis"]["verdict"],
            "approved": report["approved"],
        },
    )
    return {
        "route": route,
        "specialist": specialist,
        "executed_tool_count": len(specialist["tool_evidence"]) if specialist else 0,
        "retrieved_documents": len(context),
        "report": report,
        "finalization": finalization,
    }


@entrypoint(checkpointer=approval_demo_checkpointer)
def approval_gate_demo(inputs: dict[str, Any]):
    """Credential-free deterministic proof of interrupt and resume semantics."""

    approval = human_approval(inputs["analysis"], force_human_review=True).result()
    return ApprovalDecision.model_validate(approval).model_dump()
