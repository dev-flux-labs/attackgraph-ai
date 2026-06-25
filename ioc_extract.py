"""
ioc_extract.py — Regex-based IOC extractor.

Scans arbitrary text and returns a dict of categorised, deduplicated indicators.
"""

import re

# --- Patterns ---

_IPV4 = re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b")

_MD5 = re.compile(r"\b[a-fA-F0-9]{32}\b")
_SHA256 = re.compile(r"\b[a-fA-F0-9]{64}\b")

# Common TLDs only — avoids matching hex strings or numeric tokens as domains
_DOMAIN = re.compile(
    r"\b(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.)"
    r"+(?:com|net|org|io|gov|edu|mil|ru|cn|co|uk|de|fr|jp|br|in|au)\b",
    re.IGNORECASE,
)

_CVE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE)

_WIN_PATH = re.compile(
    r"[A-Za-z]:\\(?:[^\\/:*?\"<>|\r\n]+\\)*[^\\/:*?\"<>|\r\n]+"
)


def extract(text: str) -> dict[str, list[str]]:
    """
    Extract and deduplicate IOCs from text.

    Returns a dict with keys:
      "IPs", "MD5 Hashes", "SHA256 Hashes", "Domains", "CVEs", "File Paths"

    Empty categories are included with empty lists so callers can iterate
    without key-existence checks.
    """
    # SHA256 must be checked before MD5 — 64-char hex would also match the 32-char pattern
    sha256_matches = {m.group() for m in _SHA256.finditer(text)}

    # Exclude SHA256 matches from MD5 candidates
    md5_matches = {
        m.group() for m in _MD5.finditer(text)
        if m.group() not in sha256_matches and len(m.group()) == 32
    }

    return {
        "IPs": sorted({m.group() for m in _IPV4.finditer(text)}),
        "MD5 Hashes": sorted(md5_matches),
        "SHA256 Hashes": sorted(sha256_matches),
        "Domains": sorted({m.group().lower() for m in _DOMAIN.finditer(text)}),
        "CVEs": sorted({m.group().upper() for m in _CVE.finditer(text)}),
        "File Paths": sorted({m.group() for m in _WIN_PATH.finditer(text)}),
    }
