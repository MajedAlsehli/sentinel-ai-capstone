from langchain_openai import ChatOpenAI

from sentinel.config import get_chat_model, require_openai
from sentinel.models.schemas import RouteDecision


def route_request(request: str) -> RouteDecision:
    require_openai()
    llm = ChatOpenAI(model=get_chat_model(), temperature=0, max_retries=0)
    router = llm.with_structured_output(RouteDecision)
    return router.invoke(
        [
            (
                "system",
                "You are a cybersecurity investigation supervisor. Select exactly one "
                "specialist from the provided schema. Base the decision on the dominant "
                "artifact and explain the decision; do not use a keyword rule.",
            ),
            (
                "human",
                "Specialists: email_agent for raw email/phishing content; url_agent for "
                "URLs and domains; ip_agent for IP/network indicators; file_agent for "
                f"files, hashes, or malware artifacts.\n\nInvestigation: {request}",
            ),
        ]
    )
