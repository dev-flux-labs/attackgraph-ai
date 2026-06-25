"""
mitre.py — extract and enrich MITRE ATT&CK technique IDs from text.
"""

import re

# Curated subset of common techniques. Covers what's in the sample docs
# plus techniques likely to appear in real incident descriptions.
# Format: "TXXXX[.YYY]": (name, tactic, url)
TECHNIQUES = {
    "T1566":     ("Phishing",                              "Initial Access",        "https://attack.mitre.org/techniques/T1566/"),
    "T1566.001": ("Spear-Phishing Attachment",             "Initial Access",        "https://attack.mitre.org/techniques/T1566/001/"),
    "T1566.002": ("Spear-Phishing Link",                   "Initial Access",        "https://attack.mitre.org/techniques/T1566/002/"),
    "T1190":     ("Exploit Public-Facing Application",     "Initial Access",        "https://attack.mitre.org/techniques/T1190/"),
    "T1078":     ("Valid Accounts",                        "Initial Access",        "https://attack.mitre.org/techniques/T1078/"),
    "T1059":     ("Command and Scripting Interpreter",     "Execution",             "https://attack.mitre.org/techniques/T1059/"),
    "T1059.001": ("PowerShell",                            "Execution",             "https://attack.mitre.org/techniques/T1059/001/"),
    "T1059.003": ("Windows Command Shell",                 "Execution",             "https://attack.mitre.org/techniques/T1059/003/"),
    "T1047":     ("Windows Management Instrumentation",   "Execution",             "https://attack.mitre.org/techniques/T1047/"),
    "T1053":     ("Scheduled Task/Job",                    "Persistence",           "https://attack.mitre.org/techniques/T1053/"),
    "T1053.005": ("Scheduled Task",                        "Persistence",           "https://attack.mitre.org/techniques/T1053/005/"),
    "T1543":     ("Create or Modify System Process",       "Persistence",           "https://attack.mitre.org/techniques/T1543/"),
    "T1547":     ("Boot or Logon Autostart Execution",     "Persistence",           "https://attack.mitre.org/techniques/T1547/"),
    "T1548":     ("Abuse Elevation Control Mechanism",     "Privilege Escalation",  "https://attack.mitre.org/techniques/T1548/"),
    "T1068":     ("Exploitation for Privilege Escalation", "Privilege Escalation",  "https://attack.mitre.org/techniques/T1068/"),
    "T1055":     ("Process Injection",                     "Defense Evasion",       "https://attack.mitre.org/techniques/T1055/"),
    "T1027":     ("Obfuscated Files or Information",       "Defense Evasion",       "https://attack.mitre.org/techniques/T1027/"),
    "T1003":     ("OS Credential Dumping",                 "Credential Access",     "https://attack.mitre.org/techniques/T1003/"),
    "T1003.001": ("LSASS Memory",                          "Credential Access",     "https://attack.mitre.org/techniques/T1003/001/"),
    "T1110":     ("Brute Force",                           "Credential Access",     "https://attack.mitre.org/techniques/T1110/"),
    "T1111":     ("Multi-Factor Authentication Interception", "Credential Access",  "https://attack.mitre.org/techniques/T1111/"),
    "T1539":     ("Steal Web Session Cookie",              "Credential Access",     "https://attack.mitre.org/techniques/T1539/"),
    "T1550":     ("Use Alternate Authentication Material", "Lateral Movement",      "https://attack.mitre.org/techniques/T1550/"),
    "T1550.002": ("Pass the Hash",                         "Lateral Movement",      "https://attack.mitre.org/techniques/T1550/002/"),
    "T1550.003": ("Pass the Ticket",                       "Lateral Movement",      "https://attack.mitre.org/techniques/T1550/003/"),
    "T1021":     ("Remote Services",                       "Lateral Movement",      "https://attack.mitre.org/techniques/T1021/"),
    "T1021.001": ("Remote Desktop Protocol",               "Lateral Movement",      "https://attack.mitre.org/techniques/T1021/001/"),
    "T1021.002": ("SMB/Windows Admin Shares",              "Lateral Movement",      "https://attack.mitre.org/techniques/T1021/002/"),
    "T1083":     ("File and Directory Discovery",          "Discovery",             "https://attack.mitre.org/techniques/T1083/"),
    "T1018":     ("Remote System Discovery",               "Discovery",             "https://attack.mitre.org/techniques/T1018/"),
    "T1087":     ("Account Discovery",                     "Discovery",             "https://attack.mitre.org/techniques/T1087/"),
    "T1482":     ("Domain Trust Discovery",                "Discovery",             "https://attack.mitre.org/techniques/T1482/"),
    "T1041":     ("Exfiltration Over C2 Channel",          "Exfiltration",          "https://attack.mitre.org/techniques/T1041/"),
    "T1567":     ("Exfiltration Over Web Service",         "Exfiltration",          "https://attack.mitre.org/techniques/T1567/"),
    "T1486":     ("Data Encrypted for Impact",             "Impact",                "https://attack.mitre.org/techniques/T1486/"),
    "T1490":     ("Inhibit System Recovery",               "Impact",                "https://attack.mitre.org/techniques/T1490/"),
    "T1489":     ("Service Stop",                          "Impact",                "https://attack.mitre.org/techniques/T1489/"),
}

# Tactic order for sorting the output table
TACTIC_ORDER = [
    "Initial Access", "Execution", "Persistence", "Privilege Escalation",
    "Defense Evasion", "Credential Access", "Discovery", "Lateral Movement",
    "Exfiltration", "Impact",
]


def extract_technique_ids(text: str) -> set[str]:
    """
    Find all MITRE ATT&CK technique IDs in a string (e.g. T1059, T1566.001).
    Returns a set of uppercase IDs.
    """
    # Matches T followed by 4 digits, optionally dot + 3 digits
    pattern = r'\bT\d{4}(?:\.\d{3})?\b'
    return set(re.findall(pattern, text, re.IGNORECASE))


def enrich(technique_ids: set[str]) -> list[dict]:
    """
    Look up technique IDs and return a list of dicts sorted by tactic order.
    Unknown IDs are included with placeholder values so nothing is silently dropped.
    """
    results = []
    for tid in technique_ids:
        tid_upper = tid.upper()
        if tid_upper in TECHNIQUES:
            name, tactic, url = TECHNIQUES[tid_upper]
        else:
            # Keep unknown IDs visible — user can follow the link to look them up
            name = "Unknown technique"
            tactic = "Unknown"
            url = f"https://attack.mitre.org/techniques/{tid_upper}/"

        results.append({"id": tid_upper, "name": name, "tactic": tactic, "url": url})

    # Sort by tactic order, then by technique ID within each tactic
    results.sort(key=lambda t: (
        TACTIC_ORDER.index(t["tactic"]) if t["tactic"] in TACTIC_ORDER else 99,
        t["id"],
    ))
    return results


def techniques_from_texts(*texts: str) -> list[dict]:
    """Convenience wrapper: extract and enrich IDs from one or more text strings."""
    all_ids: set[str] = set()
    for text in texts:
        all_ids |= extract_technique_ids(text)
    return enrich(all_ids)
