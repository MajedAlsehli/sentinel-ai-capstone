from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def _paragraph(text, style):
    return Paragraph(escape(str(text)).replace("\n", "<br/>"), style)


def write_incident_pdf(report: dict, output_path="reports/incident_report.pdf"):
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        title=report["title"],
        author="Sentinel AI",
    )
    analysis = report["analysis"]
    story = [
        _paragraph(report["title"], styles["Title"]),
        Spacer(1, 12),
        _paragraph(f"Severity: {report['severity']}", styles["Heading2"]),
        _paragraph(f"Approved: {report['approved']}", styles["BodyText"]),
        Spacer(1, 12),
        _paragraph(report["summary"], styles["BodyText"]),
        Spacer(1, 12),
        _paragraph(f"Verdict: {analysis['verdict']}", styles["Heading2"]),
        _paragraph(f"Confidence: {analysis['confidence']:.0%}", styles["BodyText"]),
        _paragraph(f"Threat type: {analysis['threat_type']}", styles["BodyText"]),
        _paragraph(analysis["explanation"], styles["BodyText"]),
        Spacer(1, 12),
        _paragraph("Evidence", styles["Heading2"]),
    ]
    story.extend(
        _paragraph(f"• {item}", styles["BodyText"])
        for item in analysis.get("evidence", [])
    )
    story.extend([Spacer(1, 12), _paragraph("Recommendations", styles["Heading2"])])
    story.extend(
        _paragraph(f"• {item}", styles["BodyText"])
        for item in analysis.get("recommendations", [])
    )
    doc.build(story)
    return str(path)
