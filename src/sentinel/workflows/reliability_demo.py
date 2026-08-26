"""Deterministic exercise for retry and controlled-fallback behavior."""

from __future__ import annotations

from typing import Any

from langgraph.func import entrypoint, task
from langgraph.types import RetryPolicy


_ATTEMPTS: dict[str, int] = {}
demo_retry_policy = RetryPolicy(
    initial_interval=0.01,
    backoff_factor=1.0,
    max_interval=0.01,
    max_attempts=3,
    jitter=False,
    retry_on=(ConnectionError,),
)


@task(retry_policy=demo_retry_policy)
def transient_dependency(run_id: str) -> dict[str, Any]:
    """Fail twice, then succeed so RetryPolicy behavior is visible and repeatable."""

    _ATTEMPTS[run_id] = _ATTEMPTS.get(run_id, 0) + 1
    attempt = _ATTEMPTS[run_id]
    if attempt < 3:
        raise ConnectionError(f"simulated transient failure on attempt {attempt}")
    return {"status": "recovered", "attempts": attempt}


@task
def permanent_dependency() -> dict[str, Any]:
    raise ValueError("simulated permanent provider failure")


@task
def controlled_fallback(error_type: str) -> dict[str, Any]:
    return {
        "verdict": "unknown",
        "confidence": 0.0,
        "strategy": "controlled_fallback",
        "handled_error": error_type,
    }


@entrypoint()
def reliability_demo(inputs: dict[str, Any]):
    retry_result = transient_dependency(inputs["run_id"]).result()
    try:
        permanent_dependency().result()
    except Exception as exc:
        fallback_result = controlled_fallback(type(exc).__name__).result()
    return {
        "retry_policy": "RetryPolicy",
        "retry_result": retry_result,
        "fallback_result": fallback_result,
    }
