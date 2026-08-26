# Sentinel AI — Evidence-Grounded Cybersecurity Investigation

- **Author:** Majed Mohamed Alsehli (ماجد محمد السهلي)
- **Training programme:** SDAIA Academy — Building Agentic AI Systems
- **Instructor:** محمد البلادي
- **Cohort:** 17 August 2025 – 21 May 2026
- **Declared track:** A — Supervisor + workers

Sentinel AI is an agentic cybersecurity investigation workflow for suspicious emails, URLs, IP addresses, and file hashes. An LLM supervisor selects a specialist; that specialist chooses and executes real tools; Hybrid RAG adds stable incident-response guidance; a structured analyzer produces a cautious verdict; and LangGraph pauses before an approved report is persisted.

The repository includes both an executed evidence notebook for grading and a polished Streamlit investigation console for product demonstration. Both surfaces call the same workflow; the dashboard does not replace the rubric evidence or hide a second implementation.

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

## Interactive investigation console

Launch the product interface from the repository root:

```bash
streamlit run app.py
```

The console provides four safe example artifact types, model-selected specialist routing, tool and RAG evidence, a genuine human-approval pause, same-thread resume, structured response actions, LangSmith readiness, and approved PDF download. Credentials remain server-side in `.env`; the interface displays only readiness booleans and redacts configured secret values from provider errors.

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

### Verified execution snapshot

The submitted notebook was restarted and executed top-to-bottom on 26 August 2026. All 13 code cells completed with saved outputs and no error outputs; all 14 core regression tests captured at execution time passed; the final submission validator passed; and the inspected LangSmith investigation trace contained 18 runs, one model-selected tool run, and zero recorded errors. The trace showed `specialist_investigation` as the slowest stage at 5.326 seconds, identifying the model/tool exchange as the clearest latency target. The current repository suite contains 19 passing tests, including pure UI helpers and a credential-free Streamlit render test.

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

## Expected output

A successful investigation visibly produces:

1. A Pydantic-validated supervisor destination and routing rationale.
2. A specialist assessment backed by at least one executed tool record.
3. Retrieved incident-response context with source metadata.
4. A structured verdict, confidence, evidence list, limitations, and recommendations.
5. A real approval interrupt for high-risk or analyst-forced review.
6. A resumed result that either writes an approved PDF or records rejection without persistence.
7. A LangSmith trace containing the model, tool, retriever, retry, workflow, and timing spans.

The notebook saves evidence for every item. The Streamlit console exposes the same stages as an interactive analyst workflow.

## Technologies

Python 3.11+, LangChain, LangGraph Functional API, OpenAI structured outputs and embeddings, Chroma, Pydantic, LangSmith, Streamlit, ReportLab, and Pytest.

## Repository structure

```text
app.py             Streamlit investigation console
.streamlit/        Versioned visual theme; secrets are ignored
src/sentinel/
  agents/          LLM supervisor, specialists, structured synthesis
  tools/           Live and local analysis tools
  rag/             Document loading, splitting, embedding, Chroma retrieval
  memory/          Cross-thread Store and checkpointer demonstration
  workflows/       Functional API workflow and reliability evidence
  models/          Pydantic data contracts
  reporting/       Approved PDF generation
  ui/              Safe UI formatting, labels, samples, and download guards
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
