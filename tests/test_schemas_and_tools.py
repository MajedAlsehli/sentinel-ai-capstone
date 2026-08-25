from langchain_core.messages import AIMessage
from langchain_core.tools import tool

from sentinel.agents import specialists
from sentinel.agents.specialists import execute_tool_call
from sentinel.models.schemas import SpecialistAssessment, ThreatAnalysis
from sentinel.tools.email import extract_email_indicators
from sentinel.tools.file import validate_file_hash


def test_local_email_tool_uses_its_input():
    raw_email = (
        "From: Security <alerts@example.invalid>\n"
        "Reply-To: attacker@example.net\n"
        "Subject: Urgent verification\n\n"
        "Verify your account at https://example.net/login immediately."
    )
    result = extract_email_indicators.invoke({"raw_email": raw_email})
    assert result["reply_to"] == "attacker@example.net"
    assert result["urls"] == ["https://example.net/login"]
    assert "urgent" in result["suspicious_phrases"]
    assert "verify your account" in result["suspicious_phrases"]


def test_hash_validation_is_argument_dependent():
    valid = validate_file_hash.invoke({"file_hash": "a" * 64})
    invalid = validate_file_hash.invoke({"file_hash": "not-a-hash"})
    assert valid["valid"] is True
    assert valid["hash_type"] == "SHA-256"
    assert invalid["valid"] is False


def test_model_selected_tool_call_is_really_executed():
    @tool
    def multiply(value: int, factor: int) -> dict:
        """Multiply two integer arguments."""

        return {"product": value * factor}

    evidence = execute_tool_call(
        {"name": "multiply", "args": {"value": 7, "factor": 6}}, [multiply]
    )
    assert evidence.status == "success"
    assert evidence.output == {"product": 42}
    assert evidence.arguments == {"value": 7, "factor": 6}


def test_specialist_executes_call_and_returns_structured_result(monkeypatch):
    class FakeStructured:
        def invoke(self, _messages):
            return SpecialistAssessment(
                summary="Parsed the supplied message.",
                notable_indicators=["reply-to mismatch"],
                limitations=[],
            )

    class FakeLLM:
        def __init__(self, **_kwargs):
            self.call_number = 0

        def bind_tools(self, _tools):
            return self

        def with_structured_output(self, _schema):
            return FakeStructured()

        def invoke(self, _messages):
            self.call_number += 1
            if self.call_number == 1:
                return AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "extract_email_indicators",
                            "args": {
                                "raw_email": "From: a@example.com\nSubject: Urgent\n\n"
                                "Verify your account now."
                            },
                            "id": "call-1",
                            "type": "tool_call",
                        }
                    ],
                )
            return AIMessage(content="Tool result received.")

    monkeypatch.setattr(specialists, "require_openai", lambda: "test-key")
    monkeypatch.setattr(specialists, "ChatOpenAI", FakeLLM)
    result = specialists.run_email_agent("Analyze the supplied raw email")
    assert result.destination == "email_agent"
    assert result.assessment.summary == "Parsed the supplied message."
    assert len(result.tool_evidence) == 1
    assert result.tool_evidence[0].tool_name == "extract_email_indicators"
    assert result.tool_evidence[0].output["subject"] == "Urgent"


def test_pydantic_list_defaults_are_not_shared():
    first = ThreatAnalysis(
        verdict="unknown", confidence=0, threat_type="test", explanation="first"
    )
    second = ThreatAnalysis(
        verdict="unknown", confidence=0, threat_type="test", explanation="second"
    )
    first.evidence.append("only-first")
    assert second.evidence == []
