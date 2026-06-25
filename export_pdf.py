"""
export_pdf.py — Render an InvestigationReport as a PDF (bytes) using reportlab.

Usage:
    from export_pdf import to_pdf, filename
    pdf_bytes = to_pdf(report)
    fname     = filename(report)
"""

from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    ListFlowable, ListItem, Table, TableStyle,
)

from report import InvestigationReport

# --- Severity colours ---
_SEVERITY_COLORS = {
    "Critical": colors.HexColor("#FF4B4B"),
    "High":     colors.HexColor("#FF8C00"),
    "Medium":   colors.HexColor("#FFD700"),
    "Low":      colors.HexColor("#00C853"),
}


def filename(report: InvestigationReport) -> str:
    return report.generated_at.strftime("IncidentReport_%Y-%m-%d_%H%M.pdf")


def _styles():
    base = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=base["Title"],
        fontSize=18,
        spaceAfter=6,
        textColor=colors.HexColor("#1a1a2e"),
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=base["Heading1"],
        fontSize=13,
        spaceBefore=14,
        spaceAfter=4,
        textColor=colors.HexColor("#16213e"),
        borderPad=2,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=base["Normal"],
        fontSize=10,
        spaceAfter=4,
        leading=14,
    )
    caption_style = ParagraphStyle(
        "Caption",
        parent=base["Normal"],
        fontSize=9,
        textColor=colors.grey,
        spaceAfter=10,
    )
    return title_style, heading_style, body_style, caption_style


def to_pdf(report: InvestigationReport) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    title_style, h_style, body_style, caption_style = _styles()
    story = []

    def h(text: str) -> None:
        story.append(Paragraph(text, h_style))

    def para(text: str) -> None:
        story.append(Paragraph(text or "—", body_style))
        story.append(Spacer(1, 3))

    def bullets(items: list[str]) -> None:
        if not items:
            para("None identified.")
            return
        story.append(ListFlowable(
            [ListItem(Paragraph(item, body_style), bulletColor=colors.grey) for item in items],
            bulletType="bullet",
            leftIndent=12,
        ))
        story.append(Spacer(1, 4))

    def numbered(items: list[str]) -> None:
        if not items:
            para("None provided.")
            return
        story.append(ListFlowable(
            [ListItem(Paragraph(item, body_style)) for item in items],
            bulletType="1",
            leftIndent=12,
        ))
        story.append(Spacer(1, 4))

    # --- Title ---
    title = report.case_title or "Untitled Investigation"
    story.append(Paragraph(f"Investigation Report: {title}", title_style))
    story.append(Spacer(1, 2))

    # --- Severity badge ---
    sev_color = _SEVERITY_COLORS.get(report.severity, colors.grey)
    sev_hex = sev_color.hexval() if hasattr(sev_color, "hexval") else "#888888"
    story.append(Paragraph(
        f'Severity: <font color="{sev_hex}"><b>{report.severity}</b></font>  |  '
        f'Generated: {report.generated_at.strftime("%Y-%m-%d %H:%M")}',
        caption_style,
    ))
    story.append(Spacer(1, 6))

    # --- Case Metadata table ---
    h("Case Metadata")
    meta_data = [
        ["Case Title", title],
        ["Severity", report.severity],
        ["Generated", report.generated_at.strftime("%Y-%m-%d %H:%M")],
    ]
    meta_table = Table(meta_data, colWidths=[40 * mm, 120 * mm])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#e8eaf6")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # --- Incident Description ---
    h("Incident Description")
    para(report.query)

    # --- LLM Sections ---
    h("Incident Summary")
    para(report.incident_summary or "No summary generated.")

    h("Key Indicators of Compromise (IOCs)")
    bullets(report.iocs)

    h("Likely Attack Techniques")
    bullets(report.attack_techniques)

    h("Recommended Next Steps")
    numbered(report.recommended_steps)

    # --- Timeline ---
    h("Incident Timeline")
    if report.timeline:
        tl_data = [["Time", "Event"]] + [
            [e.get("time", ""), e.get("event", "")] for e in report.timeline
        ]
        tl_table = Table(tl_data, colWidths=[35 * mm, 125 * mm])
        tl_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(tl_table)
        story.append(Spacer(1, 6))
    else:
        para("No timeline entries recorded.")

    # --- MITRE ATT&CK ---
    h("MITRE ATT&CK Techniques")
    if report.mitre_techniques:
        mt_data = [["Tactic", "ID", "Technique"]] + [
            [t["tactic"], t["id"], t["name"]] for t in report.mitre_techniques
        ]
        mt_table = Table(mt_data, colWidths=[45 * mm, 22 * mm, 93 * mm])
        mt_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(mt_table)
        story.append(Spacer(1, 6))
    else:
        para("No MITRE techniques identified.")

    # --- Evidence Sources ---
    h("Evidence Sources")
    if report.evidence_chunks:
        ev_data = [["#", "Source", "Distance", "Relevance"]]
        for i, chunk in enumerate(report.evidence_chunks, 1):
            dist = chunk.get("distance", 0)
            rel = "High" if dist < 1.0 else ("Medium" if dist < 1.3 else "Low")
            ev_data.append([str(i), chunk.get("source", ""), f"{dist:.4f}", rel])
        ev_table = Table(ev_data, colWidths=[10 * mm, 80 * mm, 22 * mm, 20 * mm])
        ev_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16213e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
            ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dddddd")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(ev_table)
        story.append(Spacer(1, 6))
    else:
        para("No evidence chunks retrieved.")

    # --- Analyst Notes ---
    h("Analyst Notes")
    para(report.analyst_notes or "No analyst notes added.")

    doc.build(story)
    return buffer.getvalue()
