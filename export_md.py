"""
export_md.py — Render an InvestigationReport as a Markdown string.

Usage:
    from export_md import to_markdown, filename
    md_text = to_markdown(report)
    fname   = filename(report)
"""

from report import InvestigationReport


def filename(report: InvestigationReport) -> str:
    return report.generated_at.strftime("IncidentReport_%Y-%m-%d_%H%M.md")


def to_markdown(report: InvestigationReport) -> str:
    lines: list[str] = []

    def h1(text: str) -> None:
        lines.append(f"# {text}")
        lines.append("")

    def h2(text: str) -> None:
        lines.append(f"## {text}")
        lines.append("")

    def bullets(items: list[str]) -> None:
        for item in items:
            lines.append(f"- {item}")
        lines.append("")

    def numbered(items: list[str]) -> None:
        for i, item in enumerate(items, 1):
            lines.append(f"{i}. {item}")
        lines.append("")

    def para(text: str) -> None:
        lines.append(text)
        lines.append("")

    # --- Title ---
    title = report.case_title or "Untitled Investigation"
    h1(f"Investigation Report: {title}")

    # --- Case Metadata ---
    h2("Case Metadata")
    lines.append(f"| Field | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| Case Title | {title} |")
    lines.append(f"| Severity | {report.severity} |")
    lines.append(f"| Generated | {report.generated_at.strftime('%Y-%m-%d %H:%M')} |")
    lines.append("")

    # --- Incident Description ---
    h2("Incident Description")
    para(report.query)

    # --- LLM Sections ---
    h2("Incident Summary")
    para(report.incident_summary or "_No summary generated._")

    h2("Key Indicators of Compromise (IOCs)")
    if report.iocs:
        bullets(report.iocs)
    else:
        para("_None identified._")

    h2("Likely Attack Techniques")
    if report.attack_techniques:
        bullets(report.attack_techniques)
    else:
        para("_None identified._")

    h2("Recommended Next Steps")
    if report.recommended_steps:
        numbered(report.recommended_steps)
    else:
        para("_None provided._")

    # --- Timeline ---
    h2("Incident Timeline")
    if report.timeline:
        lines.append("| Time | Event |")
        lines.append("|---|---|")
        for entry in report.timeline:
            t = entry.get("time", "").replace("|", "\\|")
            e = entry.get("event", "").replace("|", "\\|")
            lines.append(f"| {t} | {e} |")
        lines.append("")
    else:
        para("_No timeline entries recorded._")

    # --- MITRE ATT&CK ---
    h2("MITRE ATT&CK Techniques")
    if report.mitre_techniques:
        lines.append("| Tactic | ID | Technique |")
        lines.append("|---|---|---|")
        for t in report.mitre_techniques:
            lines.append(f"| {t['tactic']} | [{t['id']}]({t['url']}) | {t['name']} |")
        lines.append("")
    else:
        para("_No MITRE techniques identified._")

    # --- Evidence Sources ---
    h2("Evidence Sources")
    if report.evidence_chunks:
        lines.append("| # | Source | Distance | Relevance |")
        lines.append("|---|---|---|---|")
        for i, chunk in enumerate(report.evidence_chunks, 1):
            dist = chunk.get("distance", 0)
            if dist < 1.0:
                rel = "High"
            elif dist < 1.3:
                rel = "Medium"
            else:
                rel = "Low"
            lines.append(f"| {i} | {chunk.get('source', '')} | {dist:.4f} | {rel} |")
        lines.append("")
    else:
        para("_No evidence chunks retrieved._")

    # --- Analyst Notes ---
    h2("Analyst Notes")
    para(report.analyst_notes or "_No analyst notes added._")

    return "\n".join(lines)
