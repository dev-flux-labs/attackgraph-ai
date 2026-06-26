"""
graph_viz.py — Convert a SecurityGraph NetworkX DiGraph into an interactive
pyvis HTML network, styled to match the SOC dark theme.

Returns a self-contained HTML string consumed by st.components.v1.html().
"""

import html as _html
import tempfile
import os
import networkx as nx
from pyvis.network import Network

# ── Entity colour palette (matches ui_styles.py) ──────────────────────────
_TYPE_COLORS = {
    "incident":  "#FF4D4F",   # red
    "host":      "#58A6FF",   # blue
    "user":      "#00D084",   # green
    "ip":        "#FFB000",   # orange
    "file":      "#A371F7",   # purple
    "process":   "#FFD700",   # yellow
    "technique": "#79B8FF",   # light blue
    "alert":     "#FF8C00",   # amber
}

_TYPE_SHAPES = {
    "incident":  "star",
    "host":      "dot",
    "user":      "triangle",
    "ip":        "diamond",
    "file":      "square",
    "process":   "hexagon",
    "technique": "ellipse",
    "alert":     "triangleDown",
}

_TYPE_SIZES = {
    "incident": 32,
    "technique": 22,
    "host": 20,
    "ip": 18,
    "user": 18,
    "alert": 18,
    "process": 16,
    "file": 16,
}


def build_pyvis_html(G: nx.DiGraph, height: int = 560) -> str:
    """
    Build a pyvis network from a NetworkX DiGraph and return HTML.

    Args:
        G:      The SecurityGraph.G directed graph.
        height: Canvas height in pixels.

    Returns:
        A self-contained HTML string.
    """
    net = Network(
        height=f"{height}px",
        width="100%",
        bgcolor="#161B22",
        font_color="#C9D1D9",
        directed=True,
        notebook=False,
    )

    # Physics — Barnes-Hut gives a good spread for security graphs
    net.barnes_hut(
        gravity=-8000,
        central_gravity=0.3,
        spring_length=140,
        spring_strength=0.04,
        damping=0.09,
    )

    # Nodes
    for node_id, attrs in G.nodes(data=True):
        etype  = attrs.get("type", "unknown")
        label  = attrs.get("label", node_id)
        color  = _TYPE_COLORS.get(etype, "#8B949E")
        shape  = _TYPE_SHAPES.get(etype, "dot")
        size   = _TYPE_SIZES.get(etype, 18)
        # Escape graph-derived values before embedding in HTML tooltip
        safe_etype = _html.escape(str(etype).upper())
        safe_label = _html.escape(str(label))
        title  = f"<b>{safe_etype}</b><br>{safe_label}"

        # Truncate long labels so the graph stays readable
        display_label = _html.escape(label if len(label) <= 22 else label[:20] + "…")

        net.add_node(
            node_id,
            label=display_label,
            title=title,
            color={
                "background": color,
                "border":     color,
                "highlight":  {"background": "#F3F4F6", "border": color},
                "hover":      {"background": "#F3F4F6", "border": color},
            },
            shape=shape,
            size=size,
            font={"color": "#F3F4F6", "size": 11, "face": "Inter, sans-serif"},
            borderWidth=2,
            borderWidthSelected=3,
        )

    # Edges
    for u, v, attrs in G.edges(data=True):
        rel = attrs.get("rel", "")
        # Escape graph-derived values; replace underscores for display
        short = _html.escape(rel.replace("_", " "))
        net.add_edge(
            u, v,
            title=_html.escape(rel),
            label=short,
            color={"color": "#484F58", "highlight": "#58A6FF", "hover": "#58A6FF"},
            width=1.5,
            font={"color": "#8B949E", "size": 9, "face": "Inter, sans-serif"},
            arrows={"to": {"enabled": True, "scaleFactor": 0.6}},
            smooth={"type": "curvedCW", "roundness": 0.2},
        )

    # Write to temp file and read back as HTML string
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
        tmp_path = f.name

    net.save_graph(tmp_path)
    with open(tmp_path, "r", encoding="utf-8") as f:
        html = f.read()
    os.unlink(tmp_path)

    # Inject extra CSS to make the canvas background match the SOC panel
    extra_css = """
    <style>
      body { margin: 0; background: #161B22; }
      #mynetwork {
        border: 1px solid #30363D !important;
        border-radius: 8px;
        background: #161B22 !important;
      }
      .vis-tooltip {
        background: #1C2128 !important;
        border: 1px solid #58A6FF !important;
        color: #F3F4F6 !important;
        border-radius: 6px !important;
        font-family: Inter, sans-serif !important;
        font-size: 12px !important;
        padding: 6px 10px !important;
      }
    </style>
    """
    html = html.replace("</head>", extra_css + "</head>")
    return html


def legend_html() -> str:
    """Return an HTML legend strip for the entity type colours."""
    items = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:5px;'
        f'margin-right:14px;font-size:0.72rem;color:#8B949E;">'
        f'<span style="width:10px;height:10px;border-radius:50%;'
        f'background:{color};display:inline-block;flex-shrink:0;"></span>'
        f'{etype}</span>'
        for etype, color in _TYPE_COLORS.items()
    )
    return f'<div style="padding:8px 0 12px 0;flex-wrap:wrap;display:flex;">{items}</div>'
