# Sentinel AI — Evidence-Grounded Cybersecurity Investigation

**Author:** Majed Alsehli  
**Training programme:** SDAIA Academy — Building Agentic AI Systems  
**Cohort:** 17 August 2025 – 21 May 2026  
**Declared track:** A — Supervisor + workers

Sentinel AI is an agentic cybersecurity investigation workflow for suspicious emails, URLs, IP addresses, and file hashes. An LLM supervisor selects a specialist; that specialist chooses and executes real tools; Hybrid RAG adds stable incident-response guidance; a structured analyzer produces a cautious verdict; and LangGraph pauses before an approved report is persisted.

The project was completed under an SDAIA Academy training programme. See the [SDAIA Academy GitHub organization](https://github.com/SDAIAAcademy).

## Why this project exists

Security analysts routinely move between artifact identification, live reputation services, internal guidance, risk synthesis, and approval. Fragmented lookups are slow and can blur the difference between observed evidence and inference. Sentinel keeps those stages explicit and auditable. Provider failures remain visible, an unavailable result is never treated as benign, and a failed evidence pipeline falls back to `unknown` rather than inventing a conclusion.

## Architecture

```text
Investigation request
        │
        ▼
Structured LLM supervisor ──► email / URL / IP / file specialist
                                      │
                                      ▼
                              model-selected real tools
                                      │
                   ┌──────────────────┴──────────────────┐
                   ▼                                     ▼
          structured tool evidence          semantic RAG retrieval
                   └──────────────────┬──────────────────┘
                                      ▼
                         Pydantic threat assessment
                                      │
                            high-risk or forced review?
                              ┌───────┴────────┐
                              │ yes            │ no
                              ▼                ▼
                         interrupt()       policy approval
                              │
                      Command(resume=...)
                              └───────┬────────┘
                                      ▼
                         approved PDF + Store fact
```

The primary workflow pattern is **Routing**. The LLM supervisor produces a validated `RouteDecision` and selects one specialist based on the dominant artifact. This fits the problem because email, URL, network, and malware investigations need distinct prompts and tools, while a single evidence-synthesis stage keeps verdicts consistent. Detailed component and state boundaries are documented in [docs/architecture.md](docs/architecture.md).

## Rubric evidence

| Section | Implementation | Demonstration |
|---|---|---|
| Agent fundamentals | Model-selected calls are executed and returned as `ToolMessage`; parsed outputs use Pydantic | Notebook §2; tool tests |
| Multi-agent routing | `ChatOpenAI.with_structured_output(RouteDecision)` supervisor | Notebook §3 |
| RAG | Markdown load → split → OpenAI embeddings → idempotent Chroma store → retrieval | Notebook §4 |
| Context and state | `InMemorySaver` with `thread_id`; separate `InMemoryStore` | Notebook §5 |
| Human-in-the-loop | Real `interrupt()` before report persistence and same-thread `Command(resume=...)` | Notebook §6 |
| Functional API and errors | `@task`, `@entrypoint`, `RetryPolicy`, controlled fallback | Notebook §7 |
| Workflow pattern | Routing, explicitly named and justified | Notebook §8 |
| LangSmith | Correct tracing variable and trace-derived observation | Notebook §9 |

See [docs/rubric_evidence.md](docs/rubric_evidence.md) for the written justification and exact code locations for all eight sections.

## Installation

Python 3.11 or newer is required.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Configure secrets only in `.env`. The file is ignored by Git.

| Variable | Required | Purpose |
|---|---:|---|
| `OPENAI_API_KEY` | Yes | Structured routing, tool choice, embeddings, and final analysis |
| `LANGCHAIN_API_KEY` | Yes for final evidence | LangSmith trace upload and inspection |
| `LANGCHAIN_TRACING_V2=true` | Yes for final evidence | Enables the tracing mode named by the rubric |
| `LANGCHAIN_PROJECT` | Yes for final evidence | Keeps capstone traces in one project |
| `ABUSEIPDB_API_KEY` | Optional | Live IP reputation; absence is recorded explicitly |
| `VIRUSTOTAL_API_KEY` | Optional | Live URL/file reputation; absence is recorded explicitly |

Public IP ownership lookup, public urlscan search, local email parsing, and local hash validation remain available without the optional provider keys. External reputation queries disclose the supplied indicator to that provider; do not submit confidential tokens or personal data.

## Verify and run

Run the credential-free automated suite first:

```bash
python -m pytest
```

Then open [notebooks/sentinel_capstone.ipynb](notebooks/sentinel_capstone.ipynb), restart the kernel, and run every cell from top to bottom. The notebook intentionally fails early if required credentials or tracing are unavailable; this prevents an apparently successful submission with missing evidence.

For a final submission audit:

```bash
python scripts/validate_submission.py
```

The validator checks submission identity, placeholders, notebook execution counts and errors, saved outputs, required evidence phrases, secret hygiene in tracked files, and Git history.

## Repository structure

```text
src/sentinel/
  agents/          LLM supervisor, specialists, structured synthesis
  tools/           Live and local analysis tools
  rag/             Document loading, splitting, embedding, Chroma retrieval
  memory/          Cross-thread Store and checkpointer demonstration
  workflows/       Functional API workflow and reliability evidence
  models/          Pydantic data contracts
  reporting/       Approved PDF generation
data/              Threat-intelligence knowledge corpus
notebooks/         Executed capstone evidence
docs/              Architecture, rubric mapping, submission checklist
scripts/           Final submission validator
tests/             Credential-free regression suite
```

## Safety and limitations

- Sentinel is an analyst-support system, not an autonomous blocking or deletion system.
- Live reputation results can be stale, incomplete, unavailable, or wrong; the analyzer must correlate sources.
- In-memory checkpoint and Store implementations demonstrate state semantics but are process-local. A production deployment should use durable database-backed implementations.
- The default corpus is intentionally small and educational. Production knowledge needs ownership, versioning, access control, and freshness review.
- Only an approved report is written to disk. Rejected reports are returned as structured data and are not persisted.

## Documentation

- [Technical architecture](docs/architecture.md)
- [Rubric evidence and design rationale](docs/rubric_evidence.md)
- [Submission checklist](docs/submission_checklist.md)
