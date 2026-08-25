import hashlib
from pathlib import Path
from typing import Any

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from sentinel.config import get_embedding_model


def split_documents(documents, chunk_size: int = 700, chunk_overlap: int = 100):
    """Split documents while retaining file metadata for citations."""

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True,
    )
    return splitter.split_documents(documents)


def _chunk_id(chunk) -> str:
    identity = (
        f"{chunk.metadata.get('source')}::{chunk.metadata.get('start_index')}::"
        f"{chunk.page_content}"
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def build_retriever(
    documents,
    persist_directory: str | Path | None = "chroma",
    *,
    embeddings: Any | None = None,
    collection_name: str = "sentinel-threat-intelligence",
    search_k: int = 4,
):
    """Split, embed, store, and expose semantic retrieval over the corpus."""

    chunks = split_documents(documents)
    embedding_model = embeddings or OpenAIEmbeddings(model=get_embedding_model())
    persist_path = str(Path(persist_directory).resolve()) if persist_directory else None
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_model,
        persist_directory=persist_path,
        collection_metadata={"hnsw:space": "cosine"},
    )
    ids = [_chunk_id(chunk) for chunk in chunks]
    existing = set(vectorstore.get(ids=ids, include=[]).get("ids", []))
    missing = [
        (chunk, chunk_id)
        for chunk, chunk_id in zip(chunks, ids)
        if chunk_id not in existing
    ]
    if missing:
        vectorstore.add_documents(
            documents=[chunk for chunk, _ in missing],
            ids=[chunk_id for _, chunk_id in missing],
        )
    return vectorstore.as_retriever(search_kwargs={"k": search_k}), chunks
