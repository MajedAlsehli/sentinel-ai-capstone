# Sentinel AI Technical Architecture

## System boundary

Sentinel accepts a textual cybersecurity investigation and returns a structured route, executed-tool evidence, retrieved document count, threat analysis, approval record, and finalization result. The system deliberately does not browse an untrusted URL directly, modify security controls, delete artifacts, or notify third parties. The only side effect in the capstone workflow is writing an approved PDF report and storing a long-term fact.

## Component model

The supervisor in `src/sentinel/agents/supervisor.py` uses `with_structured_output(RouteDecision)`. Its four destinations are email, URL, IP, and file specialists. There is no keyword router. The decision is consumed by the Functional API workflow, which dispatches to exactly one specialist.

Every specialist binds an appropriate tool set, allows the model to choose calls, executes each requested tool, appends a `ToolMessage`, and gives the resulting transcript back to the model. The second model pass returns `SpecialistAssessment`, while every actual invocation is retained as `ToolEvidence` with arguments, output, status, and latency. This separates a request to use a tool from proof that the tool actually ran.

The synthesis analyzer receives only structured specialist evidence and retrieved corpus text. It returns `ThreatAnalysis`, whose constrained verdict and confidence fields prevent downstream code from parsing free-form prose. Missing credentials, `not_found` responses, and tool errors stay visible as limitations.

## RAG lifecycle and design choice

The RAG pipeline genuinely loads five Markdown documents, splits them with overlap and source metadata, embeds them with `text-embedding-3-small`, stores them in Chroma, and retrieves the four most relevant chunks. Chunk identifiers are SHA-256 hashes of source, start offset, and content, making ingestion idempotent across notebook reruns.

Sentinel uses **Hybrid RAG**. Stable defensive procedures belong in the local corpus, while reputation and infrastructure observations require current external tools. Two-step RAG alone would lack live evidence; fully agentic retrieval alone would make stable guidance less predictable. Hybrid RAG keeps procedural knowledge reproducible while allowing specialists to gather current observations.

## State and memory

Short-term state is owned by `InMemorySaver`. Every stateful invocation supplies `configurable.thread_id`; the HITL demonstration resumes the exact paused thread, proving that its checkpoint survived the boundary between invocations.

Long-term memory uses a separate `InMemoryStore` namespaced by analyst. The cross-thread demonstration writes `report_format=PDF` in thread A and reads it from thread B. Because the threads have different checkpoint identities but share the Store namespace, the demonstration proves long-term memory rather than a growing chat-message list. Both implementations are process-local capstone choices; production should replace them with durable backends.

## Human approval boundary

The `human_approval` task calls `interrupt()` before an authoritative report is persisted. High-risk analyses trigger it automatically, and an analyst can force review for demonstrations or policy escalation. Resume data is validated as `ApprovalDecision` and must include approval, reviewer, and rationale. `Command(resume=...)` uses the same thread ID; rejected reports never reach the PDF writer.

## Functional API and reliability

The workflow is implemented with `@task` and `@entrypoint`, not `StateGraph`. LLM-dependent classification, specialist investigation, and synthesis tasks use a real `RetryPolicy` with bounded exponential backoff. The evidence pipeline is also wrapped by a controlled fallback that returns an explicit `unknown` verdict if specialist, retrieval, or synthesis work fails. A credential-free reliability entrypoint deterministically proves both strategies: a transient dependency succeeds on its third RetryPolicy attempt, while a permanent failure is converted into the controlled fallback.

## Observability

`.env.example` uses `LANGCHAIN_TRACING_V2=true` exactly as required and assigns all runs to `sentinel-ai-capstone`. The notebook waits for background tracers, queries the actual LangSmith project, locates the current workflow trace, counts its child runs and errors, calculates latency, and prints a trace-derived observation. This prevents a configuration flag from being presented as proof that a trace exists.

## Data contracts

Pydantic models define `RouteDecision`, `SpecialistAssessment`, `ToolEvidence`, `SpecialistResult`, `ThreatAnalysis`, `ApprovalDecision`, `IncidentReport`, and `FinalizationResult`. Mutable lists use `default_factory`, confidence is constrained to `[0, 1]`, and routing, verdict, severity, and finalization states are enumerated literals.

## Failure and trust assumptions

- Provider output is untrusted evidence and is serialized before inclusion in prompts.
- Tool timeouts are bounded; errors are recorded without becoming benign conclusions.
- A router configuration failure remains fatal because substituting a keyword router would violate the architecture.
- Evidence-stage failures become `unknown`, preserving analyst trust and preventing fabricated certainty.
- `.env`, vector data, generated PDFs, caches, and editor files are excluded by `.gitignore`.
