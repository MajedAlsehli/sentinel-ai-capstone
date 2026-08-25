"""Keep credential-free regression tests local and free of trace side effects."""

import os


os.environ["LANGCHAIN_TRACING_V2"] = "false"
os.environ["LANGSMITH_TRACING"] = "false"
