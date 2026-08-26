# Rubric Evidence and Design Rationale

## 1. Agent fundamentals — 15 points

Sentinel uses real argument-dependent tools rather than hardcoded response strings. Network tools query AbuseIPDB, ipwho.is, urlscan.io, and VirusTotal; local tools parse actual raw email content and validate the supplied hash. The model chooses calls through `bind_tools`, `execute_tool_call` invokes them, and their results return as `ToolMessage` objects. Parsed conclusions use `with_structured_output` and Pydantic models (`RouteDecision`, `SpecialistAssessment`, and `ThreatAnalysis`) because downstream code consumes those fields.

## 2. Multi-agent routing — 15 points

The project declares **Track A — Supervisor + workers**, matching the course's definition of a dedicated agent deciding which specialist works next. `route_request` asks the LLM for a validated `RouteDecision`, and the Functional API dispatches that result to an email, URL, IP, or file specialist. This pattern fits because each artifact requires a different prompt and tool set. No substring or keyword condition makes the routing decision; Python conditions only execute the already-selected destination.

## 3. Retrieval-augmented generation — 15 points

The pipeline loads the Markdown corpus, splits it with source metadata, embeds every chunk, stores deterministic IDs in Chroma, and retrieves relevant text. **Hybrid RAG** fits this problem because the local corpus supplies stable incident-response guidance while external tools supply current reputation evidence. The notebook asks a question whose answer appears verbatim in `phishing.md` and asserts that the exact phrase was retrieved, proving more than the presence of plausible-looking code.

## 4. Context and state — 15 points

Short-term workflow state uses `InMemorySaver` and explicit `thread_id` configuration, which is necessary for pausing and resuming the HITL run. Long-term facts use a separate `InMemoryStore`, not the checkpointer or message history. The notebook writes a report-format preference from thread A and reads the same fact from thread B under a shared analyst namespace, making the cross-thread boundary visible in the captured output.

## 5. Human-in-the-loop — 10 points

The approval task calls a real `interrupt()` before the side effect that persists an authoritative PDF incident record. A mandatory-review rule covers malicious results, model-requested review, and an explicit analyst override used to make the demonstration deterministic. The notebook captures the interrupt payload, inspects the saved checkpoint, and then calls `Command(resume=...)` with the same thread ID and a structured reviewer decision. The resumed output and written PDF prove completion rather than only a pause.

## 6. Functional API and error handling — 15 points

Sentinel is built with LangGraph `@task` and `@entrypoint`. The first error strategy is a real `RetryPolicy` applied to model-dependent tasks with bounded backoff. The second is a controlled fallback that converts evidence-pipeline failure into a structured `unknown` assessment. The deterministic reliability demonstration shows the retry recovering on attempt three and a separate permanent error reaching fallback; there is no handwritten sleep loop.

## 7. Workflow pattern — 10 points

The explicitly selected workflow pattern is **Routing**. It matches the mutually exclusive artifact types and keeps each specialist's permissions and prompts narrow. The supervisor's structured output is the routing authority, while the shared RAG, synthesis, approval, reporting, and memory stages provide consistent downstream behavior.

## 8. LangSmith observability — 5 points

Tracing uses `LANGCHAIN_TRACING_V2=true`, `LANGCHAIN_API_KEY`, and a dedicated `LANGCHAIN_PROJECT`. After the real workflow runs, the notebook waits for trace delivery and queries LangSmith rather than merely printing an environment variable. It finds the `sentinel_workflow` child inside the Functional API `LangGraph` root trace, then derives a written observation from the actual run tree—name, latency, run count, error count, and tool-run count—so the claim remains tied to visible trace data.

In the final saved execution, the verified investigation trace contained 18 runs, one model-selected tool run, and zero recorded errors. `specialist_investigation` was the slowest run at 5.326 seconds, showing that the model/tool exchange—rather than local retrieval, checkpointing, or PDF persistence—is the first latency optimization target.
