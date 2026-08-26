"""Tool-using cybersecurity specialists.

The important distinction in this module is that ``bind_tools`` is not treated
as completed tool use. The model chooses calls, Sentinel executes them, returns
``ToolMessage`` results to the model, and finally requests a Pydantic-validated
assessment. Every invocation is retained as a structured observation.
"""

from __future__ import annotations

import json
import time
from typing import Any, Iterable

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from sentinel.config import get_chat_model, require_openai
from sentinel.models.schemas import (
    SpecialistAssessment,
    SpecialistResult,
    ToolObservation,
)
from sentinel.tools.abuseipdb import check_ip_reputation
from sentinel.tools.email import extract_email_indicators
from sentinel.tools.file import validate_file_hash
from sentinel.tools.geolocation import geolocate_ip
from sentinel.tools.urlscan import scan_url
from sentinel.tools.virustotal import (
    check_file_hash_virustotal,
    check_url_virustotal,
)


MAX_TOOL_ROUNDS = 3


def _json_safe(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    try:
        json.dumps(value)
        return value
    except TypeError:
        return str(value)


def execute_tool_call(
    tool_call: dict[str, Any], tools: Iterable[BaseTool]
) -> ToolObservation:
    """Execute one model-selected call and return a structured observation."""

    registry = {candidate.name: candidate for candidate in tools}
    tool_name = str(tool_call.get("name", ""))
    arguments = tool_call.get("args") or {}
    started = time.perf_counter()
    if tool_name not in registry:
        output: Any = {"error": f"Unknown tool requested: {tool_name}"}
        status = "error"
    else:
        try:
            output = _json_safe(registry[tool_name].invoke(arguments))
            status = "success"
        except Exception as exc:  # A tool failure becomes an explicit observation.
            output = {"error_type": type(exc).__name__, "message": str(exc)}
            status = "error"
    latency_ms = round((time.perf_counter() - started) * 1000)
    return ToolObservation(
        tool_name=tool_name,
        arguments=arguments,
        output=output,
        status=status,
        latency_ms=latency_ms,
    )


def _run_tool_specialist(
    destination: str,
    request: str,
    system_prompt: str,
    tools: list[BaseTool],
) -> SpecialistResult:
    require_openai()
    base_llm = ChatOpenAI(model=get_chat_model(), temperature=0, max_retries=0)
    tool_llm = base_llm.bind_tools(tools)
    messages = [
        SystemMessage(
            content=(
                system_prompt
                + " You must use at least one relevant tool when the request "
                "contains an observable indicator. Never claim that a tool ran "
                "unless its ToolMessage is present. Treat not_configured and "
                "not_found as limitations, not as benign findings."
            )
        ),
        HumanMessage(content=request),
    ]
    observations: list[ToolObservation] = []
    last_content = ""

    for round_number in range(MAX_TOOL_ROUNDS):
        response = tool_llm.invoke(messages)
        messages.append(response)
        last_content = str(response.content or "")
        tool_calls = list(response.tool_calls or [])
        if not tool_calls:
            if not observations and round_number == 0:
                messages.append(
                    HumanMessage(
                        content=(
                            "No tool has run yet. Re-check the supplied artifact and call "
                            "a relevant tool if it is actionable."
                        )
                    )
                )
                continue
            break

        for tool_call in tool_calls:
            item = execute_tool_call(tool_call, tools)
            observations.append(item)
            messages.append(
                ToolMessage(
                    content=json.dumps(item.output, ensure_ascii=False, default=str),
                    tool_call_id=str(
                        tool_call.get("id", f"call-{len(observations)}")
                    ),
                    name=item.tool_name,
                    status=item.status,
                )
            )

    structured_llm = base_llm.with_structured_output(SpecialistAssessment)
    assessment = structured_llm.invoke(
        [
            SystemMessage(
                content=(
                    "Summarize specialist findings conservatively. Distinguish observed "
                    "tool results from inference and list every material limitation."
                )
            ),
            HumanMessage(
                content=(
                    f"Destination: {destination}\nRequest: {request}\n"
                    f"Tool observations: {json.dumps([item.model_dump() for item in observations], default=str)}\n"
                    f"Earlier specialist response: {last_content}"
                )
            ),
        ]
    )
    return SpecialistResult(
        destination=destination,
        assessment=assessment,
        tool_observations=observations,
    )


def run_ip_agent(request: str) -> SpecialistResult:
    return _run_tool_specialist(
        "ip_agent",
        request,
        "You are an IP security analyst. Correlate reputation with ownership and location.",
        [check_ip_reputation, geolocate_ip],
    )


def run_url_agent(request: str) -> SpecialistResult:
    return _run_tool_specialist(
        "url_agent",
        request,
        "You are a URL security analyst. Check prior scans and reputation without visiting the URL.",
        [scan_url, check_url_virustotal],
    )


def run_email_agent(request: str) -> SpecialistResult:
    return _run_tool_specialist(
        "email_agent",
        request,
        "You are a phishing analyst. Parse the supplied email before drawing conclusions.",
        [extract_email_indicators],
    )


def run_file_agent(request: str) -> SpecialistResult:
    return _run_tool_specialist(
        "file_agent",
        request,
        "You are a malware analyst. Validate hashes and check live reputation when available.",
        [validate_file_hash, check_file_hash_virustotal],
    )
