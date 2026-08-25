from pathlib import Path

from langchain_core.documents import Document

from sentinel.config import PROJECT_ROOT


def load_markdown_documents(directory: str | Path | None = None) -> list[Document]:
    """Load every threat-intelligence Markdown file with source metadata."""

    source_directory = Path(directory) if directory else PROJECT_ROOT / "data/threat_intelligence"
    docs = []
    for path in sorted(source_directory.glob("*.md")):
        docs.append(
            Document(
                page_content=path.read_text(encoding="utf-8"),
                metadata={"source": str(path.resolve()), "filename": path.name},
            )
        )
    if not docs:
        raise FileNotFoundError(f"No Markdown knowledge files found in {source_directory}")
    return docs
