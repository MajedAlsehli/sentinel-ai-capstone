"""Fail-fast validation for the final capstone artifact."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks/sentinel_capstone.ipynb"
TEXT_SUFFIXES = {".md", ".py", ".toml", ".txt", ".example"}
SECRET_PATTERNS = {
    "OpenAI-style key": re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=ROOT, text=True, capture_output=True, check=False
    )
    if result.returncode:
        fail(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def validate_identity(readme: str, notebook_text: str) -> None:
    pending_marker = "Pending " + "author response"
    programme_marker = "pending " + "programme response"
    track_marker = "Pending " + "track response"
    combined = readme + notebook_text
    for marker in (pending_marker, programme_marker, track_marker):
        if marker in combined:
            fail(f"submission identity is incomplete: {marker}")
    if not re.search(r"Declared track:\*\*\s*[ABCD]\b", readme, re.IGNORECASE):
        fail("README does not declare Track A, B, C, or D")


def validate_notebook(notebook: dict) -> None:
    code_cells = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    if not code_cells:
        fail("notebook contains no code cells")
    if any(cell.get("execution_count") is None for cell in code_cells):
        fail("one or more notebook code cells are unexecuted")
    if any(not cell.get("outputs") for cell in code_cells):
        fail("one or more notebook code cells have no saved output")
    errors = [
        output
        for cell in code_cells
        for output in cell.get("outputs", [])
        if output.get("output_type") == "error"
    ]
    if errors:
        fail(f"notebook contains {len(errors)} saved error output(s)")
    notebook_text = json.dumps(notebook)
    required = (
        "Cross-thread Store assertion: PASS",
        "Interrupt captured: PASS",
        "Resume completed: PASS",
        "Verbatim retrieval assertion: PASS",
        "Actual trace observation:",
        "RetryPolicy assertion: PASS",
    )
    for phrase in required:
        if phrase not in notebook_text:
            fail(f"notebook lacks required evidence phrase: {phrase}")


def validate_source_hygiene() -> None:
    forbidden = ("YOUR " + "FULL NAME", "REPLACE " + "THIS")
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part.startswith(".") for part in path.parts):
            continue
        if path.suffix not in TEXT_SUFFIXES and path.name != ".env.example":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for marker in forbidden:
            if marker in text:
                fail(f"template marker remains in {path.relative_to(ROOT)}")
        if path.name != ".env.example":
            for label, pattern in SECRET_PATTERNS.items():
                if pattern.search(text):
                    fail(f"possible {label} found in {path.relative_to(ROOT)}")


def main() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    notebook_text = json.dumps(notebook)
    validate_identity(readme, notebook_text)
    validate_notebook(notebook)
    validate_source_hygiene()
    commit_count = int(git_output("rev-list", "--count", "HEAD"))
    if commit_count < 3:
        fail("Git history needs at least three meaningful incremental commits")
    tracked_env = git_output("ls-files", ".env")
    if tracked_env:
        fail(".env is tracked by Git")
    print("PASS: identity, notebook evidence, source hygiene, secrets, and Git history")


if __name__ == "__main__":
    main()
