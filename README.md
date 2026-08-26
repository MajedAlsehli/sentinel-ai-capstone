# Sentinel AI

- **Author:** Majed Mohamed Alsehli
- **Training programme:** SDAIA Academy — Building Agentic AI Systems
- **Instructor:** Mohamed Albeladi
- **Cohort:** 23–27 August 2026
- **Declared track:** Track A — Supervisor + workers

Sentinel AI is an agentic cybersecurity investigation system for suspicious emails, URLs, IP addresses, and file hashes. A structured LLM supervisor selects a specialist, the specialist executes model-selected tools, Hybrid RAG adds local security guidance, and a structured analyzer produces a cautious assessment. High-risk reports pause for analyst approval before they are written to disk.

The project was developed through an [SDAIA Academy](https://github.com/SDAIAAcademy) training programme.

## Features

- Structured-output LLM supervisor with email, URL, IP, and file specialists
- Argument-dependent local and external tools selected by the model
- Pydantic models for routes, specialist assessments, tool observations, analysis, approval, and report finalization
- Hybrid RAG with Markdown loading, chunking, OpenAI embeddings, Chroma storage, and semantic retrieval
- LangGraph Functional API workflow built with `@task` and `@entrypoint`
- Short-term checkpoint state with explicit `thread_id`
- Separate long-term Store with cross-thread access
- Human approval through `interrupt()` and same-thread `Command(resume=...)`
- Bounded `RetryPolicy` for transient failures and an `unknown` fallback for permanent investigation failures
- LangSmith tracing with run-tree inspection
- Approved PDF incident reports

## Installation

Python 3.11 or newer is recommended.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

## Configuration

Add local credentials to `.env`:

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | Routing, tool selection, embeddings, and analysis |
| `OPENAI_MODEL` | Chat model name |
| `OPENAI_EMBEDDING_MODEL` | Embedding model name |
| `LANGCHAIN_API_KEY` | LangSmith tracing and run inspection |
| `LANGCHAIN_TRACING_V2=true` | Enables tracing |
| `LANGCHAIN_PROJECT` | LangSmith project name |
| `ABUSEIPDB_API_KEY` | Optional IP reputation lookup |
| `VIRUSTOTAL_API_KEY` | Optional URL and file reputation lookup |

Public IP ownership lookup, public urlscan search, local email parsing, and local hash validation remain available without the optional provider keys. External reputation queries disclose the supplied indicator to the selected provider.

## Usage

Run the automated tests:

```bash
python -m pytest -q
```

Open `notebooks/sentinel_ai_walkthrough.ipynb`, restart the kernel, and run all cells from top to bottom. The notebook walks through:

1. Model-selected tool execution and structured responses
2. Structured supervisor routing across all four specialists
3. Hybrid RAG ingestion and retrieval
4. Cross-thread long-term memory
5. Human approval interruption and same-thread resume
6. Retry and controlled-fallback behavior
7. Routing workflow execution
8. LangSmith trace inspection

## Project structure

```text
src/sentinel/
  agents/       Supervisor, specialists, and structured analysis
  tools/        Local parsers and external reputation clients
  rag/          Document loading, embeddings, Chroma, and retrieval
  memory/       Long-term Store and cross-thread workflow
  workflows/    Functional API orchestration and reliability behavior
  models/       Pydantic data contracts
  reporting/    PDF report generation
data/           Local threat-intelligence documents
notebooks/      Executed system walkthrough
docs/           Technical architecture
tests/          Automated tests
```

## Safety and limitations

Sentinel supports analyst decisions; it does not block traffic, delete files, open suspicious links, or notify third parties. Provider failures and missing results remain explicit limitations, and investigation failures return `unknown` rather than a fabricated malicious or benign verdict. The in-memory checkpointer and Store are process-local; a production service should replace them with durable backends.

See [docs/architecture.md](docs/architecture.md) for implementation details.
