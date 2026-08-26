# Sentinel AI Architecture

## Tool execution and structured responses

Each specialist binds a narrow tool set to `ChatOpenAI`. The model selects a tool and supplies its arguments; Sentinel executes the call, records its status, latency, arguments, and output, and returns a `ToolMessage` to the model. A second model call uses `with_structured_output(SpecialistAssessment)` so downstream code receives a validated Pydantic object instead of parsing prose.

Local tools parse raw email content and validate hashes. External tools query AbuseIPDB, ipwho.is, urlscan.io, and VirusTotal when their services are available. Missing configuration, unavailable results, and provider errors remain explicit limitations.

## Supervisor routing

Track A uses a supervisor-and-workers architecture. The supervisor calls `with_structured_output(RouteDecision)` and selects one of `email_agent`, `url_agent`, `ip_agent`, or `file_agent` from the dominant artifact. Python dispatches the validated destination but does not classify requests with keyword conditions. A complete raw email remains an email artifact even when it contains embedded URLs or other indicators.

## Hybrid RAG

The local pipeline loads the Markdown security documents, splits them with overlap and source metadata, embeds the chunks with OpenAI embeddings, stores deterministic chunk identifiers in Chroma, and retrieves the most relevant passages. Local documents provide stable response guidance while live tools provide current reputation and infrastructure information. Combining both sources keeps procedural guidance reproducible without treating local text as current reputation data.

## State and memory

`InMemorySaver` holds short-term workflow state. Every stateful invocation supplies `configurable.thread_id`, which identifies the checkpoint used by pause and resume operations.

Long-term facts use a separate `InMemoryStore` namespaced by analyst. The cross-thread workflow writes a fact in one thread and reads it from another thread under the same analyst namespace. The checkpointer and Store are process-local implementations and can be replaced with durable backends without changing the workflow contracts.

## Human approval

The `human_approval` task calls `interrupt()` before report persistence when policy or the analysis calls for review. The reviewer returns an `ApprovalDecision` through `Command(resume=...)` using the same `thread_id`. Approved reports continue to PDF generation; rejected reports return `not_approved` and are not written.

## Reliability

Model-dependent tasks use a bounded LangGraph `RetryPolicy` with exponential backoff for transient failures. If specialist execution, retrieval, or synthesis fails permanently, the workflow returns a structured `unknown` analysis through a controlled fallback. Infrastructure failures never become benign or malicious conclusions.

## Routing workflow

The system uses the Routing workflow pattern. One supervisor selects a specialist with a constrained tool set, then the shared retrieval, synthesis, approval, reporting, and memory stages process the result consistently. The workflow is implemented with LangGraph Functional API `@task` and `@entrypoint` functions.

## Observability

Tracing uses `LANGCHAIN_TRACING_V2=true`, `LANGCHAIN_API_KEY`, and a dedicated `LANGCHAIN_PROJECT`. After a workflow run, the notebook waits for pending tracers, queries the LangSmith project, locates the `sentinel_workflow` child inside its `LangGraph` root, and inspects run count, tool spans, errors, and latency. The printed observation is calculated from the returned run tree.
