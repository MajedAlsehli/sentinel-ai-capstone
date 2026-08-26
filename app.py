"""Sentinel AI Streamlit investigation console.

Run from the repository root:
    streamlit run app.py

The interface is deliberately a thin product layer over the same LangGraph
workflow exercised by the capstone notebook. It does not replace or duplicate
the model-selected routing, specialist tools, RAG, memory, HITL, or reporting
logic.
"""

from __future__ import annotations

import json
import os
import sys
from html import escape
from pathlib import Path
from uuid import uuid4

import streamlit as st
from langgraph.types import Command


PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from sentinel.config import langsmith_status  # noqa: E402
from sentinel.rag.loader import load_markdown_documents  # noqa: E402
from sentinel.rag.retriever import build_retriever  # noqa: E402
from sentinel.ui.presentation import (  # noqa: E402
    SAMPLE_INVESTIGATIONS,
    confidence_percent,
    downloadable_pdf,
    redact_secrets,
    route_label,
    verdict_color,
)
from sentinel.workflows.workflow import sentinel_workflow, set_retriever  # noqa: E402


st.set_page_config(
    page_title="Sentinel AI | Investigation Console",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background:
        radial-gradient(circle at 75% 0%, rgba(45,212,191,.10), transparent 34%),
        linear-gradient(180deg, #07111f 0%, #081421 100%); }
    .block-container { max-width: 1240px; padding-top: 2.2rem; padding-bottom: 4rem; }
    [data-testid="stSidebar"] { border-right: 1px solid rgba(148,163,184,.16); }
    .sentinel-kicker { color: #5eead4; font-size: .78rem; font-weight: 750;
        letter-spacing: .19em; text-transform: uppercase; margin-bottom: .45rem; }
    .sentinel-title { font-size: clamp(2.25rem, 5vw, 4.5rem); line-height: .98;
        letter-spacing: -.055em; font-weight: 780; margin: 0; }
    .sentinel-subtitle { color: #9fb0c5; max-width: 760px; font-size: 1.05rem;
        line-height: 1.65; margin: 1rem 0 2rem; }
    .glass-card { border: 1px solid rgba(148,163,184,.16); border-radius: 18px;
        padding: 1.1rem 1.2rem; background: rgba(15,29,45,.72); margin: .45rem 0 1rem; }
    .stage-line { color: #a7b7ca; font-size: .86rem; letter-spacing: .025em; }
    .signal-dot { display:inline-block; width:.54rem; height:.54rem; border-radius:50%;
        background:#34d399; box-shadow:0 0 14px rgba(52,211,153,.65); margin-right:.45rem; }
    div[data-testid="stMetric"] { border: 1px solid rgba(148,163,184,.15);
        background: rgba(15,29,45,.68); padding: 1rem; border-radius: 16px; }
    div[data-testid="stMetricValue"] { font-size: 1.65rem; }
    .verdict { border-left: 4px solid var(--accent); padding: .9rem 1rem;
        background: rgba(15,29,45,.78); border-radius: 0 14px 14px 0; }
    .verdict strong { color: var(--accent); text-transform: uppercase;
        letter-spacing: .08em; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _initialize_state() -> None:
    defaults = {
        "result": None,
        "pending_payload": None,
        "thread_id": None,
        "last_error": None,
        "request_text": SAMPLE_INVESTIGATIONS["Phishing email"],
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def _clear_case() -> None:
    st.session_state.result = None
    st.session_state.pending_payload = None
    st.session_state.thread_id = None
    st.session_state.last_error = None


@st.cache_resource(show_spinner=False)
def _prepare_retriever():
    documents = load_markdown_documents()
    retriever, chunks = build_retriever(documents, PROJECT_ROOT / "chroma")
    return retriever, len(documents), len(chunks)


def _ensure_retriever() -> tuple[int, int]:
    retriever, document_count, chunk_count = _prepare_retriever()
    set_retriever(retriever)
    return document_count, chunk_count


def _safe_error(exc: Exception) -> str:
    environment = {name: os.getenv(name) for name in os.environ}
    return redact_secrets(f"{type(exc).__name__}: {exc}", environment)


def _run_investigation(request: str, analyst_id: str, force_review: bool) -> None:
    _clear_case()
    thread_id = f"streamlit-{uuid4()}"
    st.session_state.thread_id = thread_id
    config = {"configurable": {"thread_id": thread_id}}
    output_path = PROJECT_ROOT / "reports" / f"{thread_id}.pdf"
    try:
        _ensure_retriever()
        first_run = sentinel_workflow.invoke(
            {
                "request": request,
                "analyst_id": analyst_id.strip() or "streamlit-analyst",
                "force_human_review": force_review,
                "output_path": str(output_path),
            },
            config,
        )
        if "__interrupt__" in first_run:
            st.session_state.pending_payload = first_run["__interrupt__"][0].value
        else:
            st.session_state.result = first_run
    except Exception as exc:  # The UI must report provider failures without leaking keys.
        st.session_state.last_error = _safe_error(exc)


def _resume_investigation(approved: bool, reviewer: str, reason: str) -> None:
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    try:
        st.session_state.result = sentinel_workflow.invoke(
            Command(
                resume={
                    "approved": approved,
                    "reviewer": reviewer.strip() or "Streamlit reviewer",
                    "reason": reason.strip() or "Reviewed in the Sentinel console.",
                }
            ),
            config,
        )
        st.session_state.pending_payload = None
    except Exception as exc:
        st.session_state.last_error = _safe_error(exc)


def _render_analysis(analysis: dict) -> None:
    verdict = str(analysis.get("verdict", "unknown"))
    accent = verdict_color(verdict)
    safe_verdict = escape(verdict)
    safe_explanation = escape(
        str(analysis.get("explanation", "No explanation returned."))
    )
    st.markdown(
        f'<div class="verdict" style="--accent:{accent}"><strong>{safe_verdict}</strong>'
        f'<div>{safe_explanation}</div></div>',
        unsafe_allow_html=True,
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Confidence", confidence_percent(analysis.get("confidence")))
    c2.metric("Threat type", str(analysis.get("threat_type", "unknown")).replace("_", " ").title())
    c3.metric("Human review", "Required" if analysis.get("requires_human_approval") else "Policy based")


def _render_result(result: dict) -> None:
    route = result.get("route") or {}
    report = result.get("report") or {}
    analysis = report.get("analysis") or {}

    st.subheader("Investigation result")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Specialist", route_label(route.get("destination")))
    c2.metric("Tool calls", result.get("executed_tool_count", 0))
    c3.metric("RAG sources", result.get("retrieved_documents", 0))
    c4.metric("Approval", "Approved" if report.get("approved") else "Not approved")
    _render_analysis(analysis)

    overview, evidence_tab, actions_tab, trace_tab = st.tabs(
        ["Assessment", "Evidence", "Response actions", "Observability"]
    )
    with overview:
        st.markdown("#### Supervisor decision")
        st.write(route.get("reason", "No routing reason returned."))
        specialist = result.get("specialist") or {}
        assessment = specialist.get("assessment") or {}
        st.markdown("#### Specialist assessment")
        st.write(assessment.get("summary", "No specialist summary returned."))
        limitations = assessment.get("limitations") or []
        if limitations:
            st.markdown("**Limitations**")
            for item in limitations:
                st.write(f"- {item}")
    with evidence_tab:
        observed = analysis.get("evidence") or []
        if observed:
            for number, item in enumerate(observed, 1):
                st.markdown(f"**{number:02d}** &nbsp; {item}")
        else:
            st.info("No evidence items were returned.")
        tool_evidence = (result.get("specialist") or {}).get("tool_evidence") or []
        if tool_evidence:
            st.markdown("#### Executed tool records")
            for item in tool_evidence:
                with st.expander(
                    f"{item.get('tool_name', 'tool')} · {item.get('status', 'unknown')} · "
                    f"{item.get('latency_ms', 0)} ms"
                ):
                    st.json(item)
    with actions_tab:
        recommendations = analysis.get("recommendations") or []
        for item in recommendations:
            st.markdown(f"- {item}")
        if not recommendations:
            st.info("No response actions were returned.")
        pdf_path = downloadable_pdf(result)
        if pdf_path:
            st.download_button(
                "Download approved incident report",
                data=pdf_path.read_bytes(),
                file_name=pdf_path.name,
                mime="application/pdf",
                type="primary",
            )
    with trace_tab:
        tracing = langsmith_status()
        safe_project = escape(str(tracing["project"]))
        safe_thread = escape(str(st.session_state.thread_id))
        st.markdown(
            f'<div class="glass-card"><span class="signal-dot"></span>'
            f'LangSmith tracing {"enabled" if tracing["tracing_enabled"] else "disabled"}<br>'
            f'<span class="stage-line">Project: {safe_project} · Thread: '
            f'{safe_thread}</span></div>',
            unsafe_allow_html=True,
        )
        st.caption("Detailed timing, model, retriever, and tool spans are available in LangSmith.")


_initialize_state()
tracing = langsmith_status()

with st.sidebar:
    st.markdown("### ◈ Sentinel AI")
    st.caption("Evidence-grounded security investigations")
    st.divider()
    analyst_id = st.text_input("Analyst identity", value="Majed Alsehli")
    force_review = st.toggle(
        "Require human approval",
        value=True,
        help="Pauses the LangGraph workflow before the PDF report is persisted.",
    )
    st.divider()
    st.markdown("**Runtime readiness**")
    st.write("● OpenAI configured" if os.getenv("OPENAI_API_KEY") else "○ OpenAI missing")
    st.write("● LangSmith configured" if tracing["api_key_configured"] else "○ LangSmith missing")
    st.caption(f"Trace project: {tracing['project']}")
    if st.button("Clear current case", use_container_width=True):
        _clear_case()

st.markdown('<div class="sentinel-kicker">Agentic security operations</div>', unsafe_allow_html=True)
st.markdown('<h1 class="sentinel-title">Investigate with evidence,<br>not assumptions.</h1>', unsafe_allow_html=True)
st.markdown(
    '<div class="sentinel-subtitle">A structured LLM supervisor routes each artifact to a '
    'narrow specialist. Real tools, Hybrid RAG, cross-thread memory, human approval, and '
    'LangSmith tracing keep every decision inspectable.</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="glass-card stage-line">SUPERVISOR &nbsp;→&nbsp; SPECIALIST &nbsp;→&nbsp; '
    'TOOLS + RAG &nbsp;→&nbsp; ANALYSIS &nbsp;→&nbsp; HUMAN REVIEW &nbsp;→&nbsp; PDF</div>',
    unsafe_allow_html=True,
)

sample_name = st.selectbox("Load an investigation example", list(SAMPLE_INVESTIGATIONS))
if st.button("Use selected example"):
    st.session_state.request_text = SAMPLE_INVESTIGATIONS[sample_name]

with st.form("investigation-form"):
    request = st.text_area(
        "Artifact or investigation request",
        key="request_text",
        height=210,
        placeholder="Paste a raw email, URL, IP address, or file hash...",
    )
    submitted = st.form_submit_button("Run agentic investigation", type="primary")

if submitted:
    if request.strip():
        with st.spinner("Routing, executing tools, retrieving context, and synthesizing evidence..."):
            _run_investigation(request, analyst_id, force_review)
    else:
        st.warning("Enter an artifact or investigation request first.")

if st.session_state.last_error:
    st.error("The investigation could not complete. The provider response is shown safely below.")
    st.code(st.session_state.last_error)

if st.session_state.pending_payload:
    payload = st.session_state.pending_payload
    st.warning("Human approval required before the incident report can be persisted.")
    _render_analysis(payload.get("analysis") or {})
    with st.expander("Review the complete interrupt payload"):
        st.code(json.dumps(payload, indent=2, default=str), language="json")
    review_reason = st.text_input(
        "Review rationale",
        value="Evidence, limitations, and recommended actions were reviewed.",
    )
    approve_col, reject_col = st.columns(2)
    if approve_col.button("Approve and generate PDF", type="primary", use_container_width=True):
        with st.spinner("Resuming the saved workflow checkpoint..."):
            _resume_investigation(True, analyst_id, review_reason)
        st.rerun()
    if reject_col.button("Reject report", use_container_width=True):
        _resume_investigation(False, analyst_id, review_reason)
        st.rerun()

if st.session_state.result:
    _render_result(st.session_state.result)

st.divider()
st.caption(
    "Analyst-support system only. Never treat an unavailable reputation result as benign, "
    "and do not submit confidential artifacts to external providers."
)
