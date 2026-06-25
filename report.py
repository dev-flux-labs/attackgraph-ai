"""
report.py — Structured investigation report object.

The InvestigationReport dataclass is the single source of truth for all exporters.
Markdown, PDF, and any future formats (DOCX, HTML, JSON) consume this object —
they never parse rendered text.
"""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class InvestigationReport:
    case_title: str
    severity: str                   # Critical | High | Medium | Low
    generated_at: datetime
    query: str

    # Sections parsed from LLM output
    incident_summary: str = ""
    iocs: list[str] = field(default_factory=list)           # bullet text, stripped of leading "- "
    attack_techniques: list[str] = field(default_factory=list)
    recommended_steps: list[str] = field(default_factory=list)

    # Analyst-supplied
    timeline: list[dict] = field(default_factory=list)      # [{"time": str, "event": str}]
    analyst_notes: str = ""

    # Passthrough from pipeline
    evidence_chunks: list[dict] = field(default_factory=list)   # from rag.retrieve()
    mitre_techniques: list[dict] = field(default_factory=list)  # from mitre.techniques_from_texts()


def parse_llm_output(text: str) -> dict:
    """
    Split LLM report text into sections by '## ' headings.
    Returns a dict mapping section name → list of content lines.

    Expected headings (from llm.py SYSTEM_PROMPT):
      Incident Summary
      Key Indicators of Compromise (IOCs)
      Likely Attack Techniques
      Recommended Next Steps
    """
    sections: dict[str, list[str]] = {}
    current_heading = None
    current_lines: list[str] = []

    for line in text.splitlines():
        if line.startswith("## "):
            # Save previous section
            if current_heading is not None:
                sections[current_heading] = current_lines
            current_heading = line[3:].strip()
            current_lines = []
        elif current_heading is not None:
            current_lines.append(line)

    # Save the last section
    if current_heading is not None:
        sections[current_heading] = current_lines

    return sections


def _extract_bullets(lines: list[str]) -> list[str]:
    """Return non-empty lines, stripping leading '- ' or '* ' bullet markers."""
    result = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- ") or stripped.startswith("* "):
            stripped = stripped[2:]
        elif stripped.startswith("• "):
            stripped = stripped[2:]
        result.append(stripped)
    return result


def _extract_numbered(lines: list[str]) -> list[str]:
    """Return non-empty lines, stripping leading '1. ', '2. ' etc."""
    import re
    result = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Strip leading number+dot: "1. Foo" → "Foo"
        stripped = re.sub(r"^\d+\.\s*", "", stripped)
        result.append(stripped)
    return result


def build_report(
    llm_text: str,
    case_title: str,
    severity: str,
    query: str,
    timeline: list[dict],
    analyst_notes: str,
    evidence_chunks: list[dict],
    mitre_techniques: list[dict],
) -> "InvestigationReport":
    """
    Assemble all pipeline outputs into a single InvestigationReport.
    Called in app.py immediately after st.write_stream() completes.
    """
    sections = parse_llm_output(llm_text)

    ioc_lines = _extract_bullets(sections.get("Key Indicators of Compromise (IOCs)", []))
    technique_lines = _extract_bullets(sections.get("Likely Attack Techniques", []))
    step_lines = _extract_numbered(sections.get("Recommended Next Steps", []))
    summary_lines = sections.get("Incident Summary", [])
    summary = "\n".join(l for l in summary_lines if l.strip())

    return InvestigationReport(
        case_title=case_title,
        severity=severity,
        generated_at=datetime.now(),
        query=query,
        incident_summary=summary,
        iocs=ioc_lines,
        attack_techniques=technique_lines,
        recommended_steps=step_lines,
        timeline=timeline,
        analyst_notes=analyst_notes,
        evidence_chunks=evidence_chunks,
        mitre_techniques=mitre_techniques,
    )
