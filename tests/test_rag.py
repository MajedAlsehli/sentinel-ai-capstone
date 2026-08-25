import hashlib
import math

from langchain_core.embeddings import Embeddings

from sentinel.rag.loader import load_markdown_documents
from sentinel.rag.retriever import build_retriever, split_documents


class DeterministicEmbeddings(Embeddings):
    """Small test-only embedding; production uses OpenAIEmbeddings."""

    dimensions = 64

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in text.lower().split():
            index = int(hashlib.sha256(token.encode()).hexdigest()[:8], 16) % self.dimensions
            vector[index] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


def test_documents_load_and_split():
    documents = load_markdown_documents()
    chunks = split_documents(documents)
    assert len(documents) == 5
    assert len(chunks) >= len(documents)
    assert all(chunk.metadata.get("source") for chunk in chunks)


def test_verbatim_fact_is_retrieved(tmp_path):
    documents = load_markdown_documents()
    expected_chunks = split_documents(documents)
    retriever, built_chunks = build_retriever(
        documents,
        tmp_path / "chroma",
        embeddings=DeterministicEmbeddings(),
        collection_name="sentinel-test",
        search_k=len(expected_chunks),
    )
    hits = retriever.invoke(
        "What safe initial response should an analyst take for a phishing message?"
    )
    joined = "\n".join(hit.page_content for hit in hits)
    assert "isolate the message, preserve full headers" in joined
    assert len(built_chunks) == len(expected_chunks) > 0
