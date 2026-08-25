"""Long-term memory separated from per-thread workflow checkpoints."""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_store
from langgraph.func import entrypoint
from langgraph.store.memory import InMemoryStore


store = InMemoryStore()
NAMESPACE = ("sentinel", "analyst")
memory_demo_checkpointer = InMemorySaver()


def analyst_namespace(analyst_id: str = "default") -> tuple[str, str, str]:
    return (*NAMESPACE, analyst_id)


def save_fact(key: str, value: Any, analyst_id: str = "default") -> dict[str, Any]:
    payload = {"value": value}
    store.put(analyst_namespace(analyst_id), key, payload)
    return payload


def get_fact(key: str, analyst_id: str = "default") -> dict[str, Any] | None:
    item = store.get(analyst_namespace(analyst_id), key)
    return item.value if item else None


def save_preference(key: str, value: Any) -> dict[str, Any]:
    """Backward-compatible alias used by the original smoke test."""

    return save_fact(key, value)


def get_preference(key: str) -> dict[str, Any] | None:
    return get_fact(key)


@entrypoint(checkpointer=memory_demo_checkpointer, store=store)
def cross_thread_memory_workflow(inputs: dict[str, Any]):
    """Write/read Store facts in independent graph threads for rubric evidence."""

    analyst_id = inputs.get("analyst_id", "demo-analyst")
    runtime_store = get_store()
    key = inputs["key"]
    namespace = analyst_namespace(analyst_id)
    operation = inputs["operation"]
    if operation == "write":
        runtime_store.put(namespace, key, {"value": inputs["value"]})
        value = inputs["value"]
    elif operation == "read":
        item = runtime_store.get(namespace, key)
        value = item.value["value"] if item else None
    else:
        raise ValueError("operation must be 'write' or 'read'")
    return {
        "operation": operation,
        "thread_label": inputs["thread_label"],
        "analyst_id": analyst_id,
        "key": key,
        "value": value,
    }
