from pathlib import Path

from sentinel.ui.presentation import (
    SAMPLE_INVESTIGATIONS,
    confidence_percent,
    downloadable_pdf,
    redact_secrets,
    route_label,
    verdict_color,
)


def test_samples_cover_every_specialist_artifact():
    assert set(SAMPLE_INVESTIGATIONS) == {
        "Phishing email",
        "Suspicious URL",
        "Network indicator",
        "File hash",
    }
    assert all(value.strip() for value in SAMPLE_INVESTIGATIONS.values())


def test_dashboard_labels_and_confidence_are_safe():
    assert route_label("email_agent") == "Email specialist"
    assert route_label("not-real") == "Pending model decision"
    assert confidence_percent(0.854) == "85%"
    assert confidence_percent(4) == "100%"
    assert confidence_percent("invalid") == "0%"
    assert verdict_color("malicious") != verdict_color("benign")
    assert verdict_color("not-real") == verdict_color("unknown")


def test_redaction_removes_every_configured_secret():
    environment = {
        "OPENAI_API_KEY": "secret-openai-value",
        "LANGCHAIN_API_KEY": "secret-langsmith-value",
    }
    message = "failure secret-openai-value then secret-langsmith-value"
    redacted = redact_secrets(message, environment)
    assert "secret-openai-value" not in redacted
    assert "secret-langsmith-value" not in redacted
    assert "[OPENAI_API_KEY redacted]" in redacted
    assert "[LANGCHAIN_API_KEY redacted]" in redacted


def test_pdf_download_requires_real_written_pdf(tmp_path):
    pdf = tmp_path / "approved.pdf"
    pdf.write_bytes(b"%PDF-1.4\n")
    written = {"finalization": {"status": "written", "output_path": str(pdf)}}
    missing = {"finalization": {"status": "written", "output_path": str(tmp_path / "missing.pdf")}}
    rejected = {"finalization": {"status": "not_approved", "output_path": str(pdf)}}

    assert downloadable_pdf(written) == Path(pdf)
    assert downloadable_pdf(missing) is None
    assert downloadable_pdf(rejected) is None
