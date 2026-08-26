# Capstone Submission Checklist

## Identity and programme

- [x] Full English and Arabic name appears in README and notebook
- [x] Instructor name appears in README and notebook
- [x] Exact SDAIA Academy programme name appears in README and notebook
- [x] Cohort dates appear in README and notebook
- [x] Declared Track A/B/C/D appears in README and notebook
- [x] SDAIA Academy GitHub link is present

## Eight scored sections

- [x] Real argument-dependent tools are implemented
- [x] Model-selected tool calls are executed and returned as `ToolMessage`
- [x] Parsed LLM results use `with_structured_output` plus Pydantic
- [x] LLM supervisor routing is implemented without a keyword router
- [x] Documents load, split, embed, store, and retrieve
- [x] Hybrid RAG is explicitly named and justified
- [x] Verbatim-answer RAG assertion is implemented
- [x] Checkpointer and explicit `thread_id` are implemented
- [x] Separate Store and genuine cross-thread workflow are implemented
- [x] Real `interrupt()` and same-thread `Command(resume=...)` are implemented
- [x] Functional API `@task` and `@entrypoint` are used
- [x] Real `RetryPolicy` and controlled fallback are implemented
- [x] Routing is explicitly named and justified
- [x] Correct LangSmith tracing variable is configured
- [x] Actual LangSmith trace observation is captured in the submitted notebook

## Verification and repository quality

- [x] Credential-free automated tests pass
- [x] README contains project description, architecture, setup, use, safety, and limitations
- [x] Technical architecture and result-backed rubric rationale are documented
- [x] `.gitignore` excludes secrets, caches, vector data, and generated reports
- [x] Current tracked-source scan contains no obvious API key values
- [x] Notebook cells have stable IDs
- [x] Notebook restarted and executed top-to-bottom with no errors
- [x] Every notebook demo cell has captured output
- [x] Git repository contains meaningful incremental commits
- [x] Final `python scripts/validate_submission.py` audit passes

## Product demonstration layer

- [x] Streamlit console invokes the same graded LangGraph workflow
- [x] Four representative artifact examples are available without keyword routing
- [x] Human interrupt and resume are interactive in the console
- [x] Tool evidence, RAG count, assessment, limitations, and actions are visible
- [x] Approved PDF is downloadable and rejected reports are not persisted
- [x] UI errors redact configured credentials
- [x] Credential-free Streamlit render test passes
