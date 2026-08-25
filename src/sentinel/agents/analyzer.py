from langchain_openai import ChatOpenAI

from sentinel.config import get_chat_model, require_openai
from sentinel.models.schemas import ThreatAnalysis


def analyze_with_context(request: str, context: str) -> ThreatAnalysis:
    require_openai()
    llm = ChatOpenAI(model=get_chat_model(), temperature=0, max_retries=0)
    structured = llm.with_structured_output(ThreatAnalysis)
    return structured.invoke(
        [
            (
                "system",
                "You are Sentinel's evidence synthesis analyst. Use only the supplied "
                "specialist evidence and retrieved knowledge. Label uncertainty, do not "
                "treat missing provider configuration as benign evidence, and request "
                "human approval for malicious or high-impact conclusions.",
            ),
            (
                "human",
                f"Investigation:\n{request}\n\nEvidence and RAG context:\n{context}",
            ),
        ]
    )
