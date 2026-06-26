"""
graph.py — Persistent security memory graph using NetworkX.

Entities and relationships extracted from investigations are accumulated in a
directed graph that survives across Streamlit sessions. Each call to
populate_from_investigation() adds new nodes and edges without removing existing
ones — the graph grows as more investigations are run.

Storage: ~/.attackgraph_memory.json  (Linux FS, same convention as ChromaDB)
"""

import json
import os
import re

import networkx as nx

GRAPH_PATH = os.path.expanduser("~/.attackgraph_memory.json")

# Canonical entity types (node 'type' attribute)
ENTITY_TYPES = ["incident", "host", "user", "ip", "file", "process", "technique", "alert"]

# Process names that indicate a process entity in free text
_KNOWN_PROCESSES = {
    "powershell.exe", "cmd.exe", "wscript.exe", "mshta.exe",
    "rundll32.exe", "regsvr32.exe", "schtasks.exe", "winword.exe",
    "excel.exe", "cscript.exe", "wmic.exe", "msiexec.exe",
    "certutil.exe", "bitsadmin.exe", "net.exe", "whoami.exe",
    "mimikatz.exe", "psexec.exe",
}

# Regex patterns for entity extraction from free text
_RE_HOSTNAME = re.compile(r"\b([A-Z][A-Z0-9\-]{3,15})\b")
_RE_USER = re.compile(r"(?:user|username|account)[:\s]+([a-zA-Z0-9_\.\-]+)", re.IGNORECASE)
_RE_PROCESS = re.compile(r"\b([a-zA-Z0-9_\-]+\.exe)\b", re.IGNORECASE)


class SecurityGraph:
    def __init__(self):
        self.G: nx.DiGraph = nx.DiGraph()

    # ── Entity & relationship CRUD ─────────────────────────────────────────

    def add_entity(self, entity_id: str, entity_type: str, label: str = "") -> None:
        """Add a node. Safe to call repeatedly — deduplicates by entity_id."""
        if entity_id not in self.G:
            self.G.add_node(entity_id, type=entity_type, label=label or entity_id)

    def add_relationship(self, source_id: str, target_id: str, rel: str) -> None:
        """Add a directed edge. Both nodes must already exist. Deduplicates."""
        if source_id in self.G and target_id in self.G:
            if not self.G.has_edge(source_id, target_id):
                self.G.add_edge(source_id, target_id, rel=rel)

    # ── Entity extraction ──────────────────────────────────────────────────

    def _extract_hosts(self, text: str) -> list[str]:
        """Extract likely hostnames (ALL-CAPS-WITH-HYPHENS pattern) from text."""
        # Common false positives to exclude
        stopwords = {
            "IOC", "IP", "URL", "DNS", "SMB", "RDP", "VPN", "EDR", "AV",
            "MFA", "BEC", "SOC", "CVE", "TTPs", "MITRE", "ATT", "CK",
            "HTTP", "HTTPS", "SSH", "FTP", "API", "AWS", "GCP", "AKA",
            "NTLM", "LDAP", "WMI", "RPC", "COM", "NET",
        }
        found = set()
        for m in _RE_HOSTNAME.finditer(text):
            name = m.group(1)
            if name not in stopwords and len(name) >= 4:
                found.add(name)
        return sorted(found)

    def _extract_users(self, text: str) -> list[str]:
        """Extract usernames from 'user: xxx' or 'account: xxx' patterns."""
        found = set()
        for m in _RE_USER.finditer(text):
            u = m.group(1).strip(".,;:'\"")
            if u and len(u) >= 2:
                found.add(u.lower())
        return sorted(found)

    def _extract_processes(self, text: str) -> list[str]:
        """Extract process names that appear in the known-processes allowlist."""
        found = set()
        for m in _RE_PROCESS.finditer(text):
            p = m.group(1).lower()
            if p in _KNOWN_PROCESSES:
                found.add(p)
        return sorted(found)

    # ── Main population method ─────────────────────────────────────────────

    def populate_from_investigation(
        self,
        case_title: str,
        iocs: dict,
        mitre_techniques: list[dict],
        query: str,
        report_text: str,
    ) -> int:
        """
        Extract entities and relationships from investigation results and add
        them to the graph. Returns the number of NEW edges created this call.
        """
        edges_before = self.G.number_of_edges()
        combined_text = query + "\n" + report_text

        # --- Incident node ---
        incident_id = case_title.strip() or "Unnamed Incident"
        self.add_entity(incident_id, "incident")

        # --- IPs ---
        ip_ids = []
        for ip in iocs.get("IPs", []):
            self.add_entity(ip, "ip", label=ip)
            ip_ids.append(ip)

        # --- Domains → hosts ---
        domain_hosts: list[str] = []
        for domain in iocs.get("Domains", []):
            self.add_entity(domain, "host", label=domain)
            domain_hosts.append(domain)

        # --- CVEs → alerts ---
        for cve in iocs.get("CVEs", []):
            self.add_entity(cve, "alert", label=cve)
            self.add_relationship(cve, incident_id, "alert_related_to_host")

        # --- MITRE techniques ---
        technique_ids: list[str] = []
        for t in mitre_techniques:
            tid = t["id"]
            self.add_entity(tid, "technique", label=f"{tid} {t['name']}")
            technique_ids.append(tid)

        # --- Hosts from text ---
        text_hosts = self._extract_hosts(combined_text)
        all_host_ids = list(dict.fromkeys(domain_hosts + text_hosts))  # preserve order, dedup
        for h in all_host_ids:
            self.add_entity(h, "host", label=h)

        # --- Users from text ---
        user_ids = self._extract_users(combined_text)
        for u in user_ids:
            self.add_entity(u, "user", label=u)

        # --- Processes from text ---
        process_ids = self._extract_processes(combined_text)
        for p in process_ids:
            self.add_entity(p, "process", label=p)

        # --- Relationships ---

        # techniques → incident
        for tid in technique_ids:
            self.add_relationship(tid, incident_id, "technique_observed_in_incident")

        # incident → hosts
        for h in all_host_ids:
            self.add_relationship(incident_id, h, "alert_related_to_host")

        # hosts → IPs
        for h in all_host_ids:
            for ip in ip_ids:
                self.add_relationship(h, ip, "host_connected_to_ip")

        # IPs → incident (reverse link — attacker IPs connected to case)
        for ip in ip_ids:
            self.add_relationship(ip, incident_id, "alert_related_to_host")

        # users → hosts
        for u in user_ids:
            for h in all_host_ids:
                self.add_relationship(u, h, "user_logged_into_host")

        # processes → incident
        for p in process_ids:
            self.add_relationship(p, incident_id, "alert_related_to_host")

        return self.G.number_of_edges() - edges_before

    # ── Query helpers ──────────────────────────────────────────────────────

    def summary(self) -> dict:
        """Return node counts by type and total edge count."""
        counts: dict[str, int] = {etype: 0 for etype in ENTITY_TYPES}
        for _, attrs in self.G.nodes(data=True):
            etype = attrs.get("type", "unknown")
            if etype in counts:
                counts[etype] += 1
        counts["total_edges"] = self.G.number_of_edges()
        return counts

    def all_nodes(self) -> list[dict]:
        """Return all nodes as a list of dicts for DataFrame display."""
        return [
            {"ID": nid, "Type": attrs.get("type", ""), "Label": attrs.get("label", nid)}
            for nid, attrs in sorted(self.G.nodes(data=True), key=lambda x: (x[1].get("type",""), x[0]))
        ]

    def all_edges(self) -> list[dict]:
        """Return all edges as a list of dicts for DataFrame display."""
        return [
            {"Source": u, "Relationship": attrs.get("rel", ""), "Target": v}
            for u, v, attrs in sorted(self.G.edges(data=True), key=lambda x: x[2].get("rel",""))
        ]

    # ── Persistence ────────────────────────────────────────────────────────

    def save(self) -> None:
        """Serialise the graph to JSON and write to GRAPH_PATH."""
        data = nx.node_link_data(self.G)
        with open(GRAPH_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls) -> "SecurityGraph":
        """Load the graph from GRAPH_PATH. Returns an empty graph if file doesn't exist."""
        g = cls()
        if not os.path.exists(GRAPH_PATH):
            return g
        try:
            with open(GRAPH_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            g.G = nx.node_link_graph(data, directed=True)
        except (json.JSONDecodeError, Exception):
            # Corrupt file — start fresh rather than crashing
            g.G = nx.DiGraph()
        return g
