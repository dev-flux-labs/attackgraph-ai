"""
file_parser.py — Safe parsers for uploaded log and data files.

Public API:
    parse_file(filename, content) -> str
        Dispatches by file extension and returns plain UTF-8 text
        ready for chunk_text() in ingest.py.

Raises ValueError for:
    - Unsupported file extension
    - Decoded text exceeding MAX_TEXT_BYTES
    - Malformed CSV or JSON
"""

import csv
import io
import json
import re

# Hard cap on decoded text size to keep embedding times reasonable.
# Streamlit allows up to 200 MB uploads by default; we process up to 5 MB.
MAX_TEXT_BYTES = 5 * 1024 * 1024  # 5 MB

# Strip ANSI colour / control sequences common in terminal log files
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mGKHF]")


def _decode(content: bytes) -> str:
    """Decode bytes to UTF-8 (replacing bad bytes) and enforce the size cap."""
    text = content.decode("utf-8", errors="replace")
    if len(text.encode("utf-8")) > MAX_TEXT_BYTES:
        mb = MAX_TEXT_BYTES // (1024 * 1024)
        raise ValueError(
            f"File is too large to process ({len(content) // 1024} KB decoded). "
            f"Maximum supported size is {mb} MB."
        )
    return text


def parse_txt(content: bytes) -> str:
    """Parse plain text files (.txt, .log). Strips ANSI escape codes."""
    text = _decode(content)
    return _ANSI_RE.sub("", text)


def parse_csv(content: bytes) -> str:
    """
    Parse CSV files into one line per row.
    Format: "ColumnName: value | ColumnName2: value2 ..."
    Preserves column names as context so the LLM can reason about field meaning.
    Falls back to positional parsing if no header row is detected.
    """
    text = _decode(content)
    f = io.StringIO(text)

    # Detect whether the first row looks like a header
    sample = text[:2048]
    try:
        has_header = csv.Sniffer().has_header(sample)
    except csv.Error:
        has_header = True  # assume header on sniffer failure

    rows_out: list[str] = []

    if has_header:
        try:
            reader = csv.DictReader(f)
            for row in reader:
                parts = [
                    f"{k.strip()}: {v.strip()}"
                    for k, v in row.items()
                    if k and v and v.strip()
                ]
                if parts:
                    rows_out.append(" | ".join(parts))
        except csv.Error as e:
            raise ValueError(f"CSV parsing error: {e}") from e
    else:
        try:
            reader_plain = csv.reader(f)
            for row in reader_plain:
                parts = [cell.strip() for cell in row if cell.strip()]
                if parts:
                    rows_out.append(" | ".join(parts))
        except csv.Error as e:
            raise ValueError(f"CSV parsing error: {e}") from e

    if not rows_out:
        raise ValueError("CSV file contains no readable rows.")

    return "\n".join(rows_out)


def _flatten_json(obj, prefix: str = "") -> list[str]:
    """
    Recursively walk a JSON object and emit 'key: value' strings for leaf nodes.
    Lists are indexed: 'items[0]: value'.
    """
    lines: list[str] = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            child_key = f"{prefix}.{k}" if prefix else str(k)
            lines.extend(_flatten_json(v, child_key))

    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            child_key = f"{prefix}[{i}]" if prefix else f"[{i}]"
            lines.extend(_flatten_json(item, child_key))

    else:
        # Leaf node — emit only if non-empty
        value = str(obj).strip()
        if value and value.lower() not in ("null", "none", ""):
            label = prefix if prefix else "value"
            lines.append(f"{label}: {value}")

    return lines


def parse_json(content: bytes) -> str:
    """
    Parse JSON into flat 'key: value' lines for embedding.
    Top-level arrays are processed element by element with blank-line separators.
    """
    text = _decode(content)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}") from e

    if isinstance(data, list):
        # Process each top-level element as a separate block
        blocks: list[str] = []
        for i, item in enumerate(data):
            lines = _flatten_json(item, prefix=f"record[{i}]")
            if lines:
                blocks.append("\n".join(lines))
        result = "\n\n".join(blocks)
    else:
        result = "\n".join(_flatten_json(data))

    if not result.strip():
        raise ValueError("JSON file contains no extractable text content.")

    return result


def parse_file(filename: str, content: bytes) -> str:
    """
    Dispatch to the correct parser based on the file extension.
    Returns plain UTF-8 text ready for chunk_text().
    Raises ValueError for unsupported extensions or parse errors.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    parsers = {
        "txt":  parse_txt,
        "log":  parse_txt,   # same parser — ANSI stripping handles .log
        "csv":  parse_csv,
        "json": parse_json,
    }

    if ext not in parsers:
        raise ValueError(
            f"Unsupported file type '.{ext}'. "
            f"Supported: {', '.join('.' + e for e in parsers)}."
        )

    return parsers[ext](content)
