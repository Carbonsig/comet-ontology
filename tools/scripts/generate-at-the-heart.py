#!/usr/bin/env python3
"""Generate the COMET 'at the heart' hub diagram as a standalone SVG.

Mirrors the Smart Freight Centre GLEC/ISO-14083 heart graphic, but tells
COMET's story: COMET is the shared language at the centre; four standards
domains feed in; ten MECE stakeholder groups read the single graph.

Cluster membership and the crosswalk counts shown on each pill are pulled
live from docs/ontology-data.json (the same file that drives the schema map
and glossary), so the graphic stays in sync with the published alignments.
The four-domain taxonomy and the stakeholder band are editorial.

Regenerate:  python3 tools/scripts/generate-at-the-heart.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = REPO_ROOT / "docs" / "ontology-data.json"
OUT_PATH = REPO_ROOT / "docs" / "assets" / "comet-at-the-heart.svg"

W, H = 1600, 1010

# ── palette (from the microsite + stakeholder colours) ──────────────────
ACCENT      = "#c8360a"   # COMET burnt-orange
ACCENT_DK   = "#a52a06"
INK         = "#1c1c1a"
INK2        = "#4a4a45"
MUTED       = "#7a7a74"
PAPER       = "#f5f4f0"
RULE        = "#d8d7d0"

# cluster colours
C_PRODUCT = "#2563eb"   # blue
C_REG     = "#7c3aed"   # purple
C_VERIFY  = "#059669"   # green
C_MARKET  = "#d97706"   # amber

FONT_SERIF = "'Playfair Display', Georgia, serif"
FONT_SANS  = "'DM Sans', 'Helvetica Neue', Arial, sans-serif"
FONT_MONO  = "'DM Mono', 'SFMono-Regular', Menlo, monospace"

# ── how each published target_standard maps into the four editorial domains
# Membership + counts come from the data; this dict only assigns a bucket.
CLUSTER_OF = {
    # Product & Footprint — what a product emits
    "WBCSD PACT":            "product",
    "GHG Protocol":          "product",
    "GHG Protocol Scope 3":  "product",
    "ISO 14067":             "product",
    "EN 15804+A2":           "product",
    # Regulation & Disclosure — what must be reported
    "EU ESRS":               "reg",
    "EU CBAM":               "reg",
    "ISO 14068-1":           "reg",
    "ISSB S2":               "reg",
    "IRA 45V":               "reg",
    "EU ETS MRV":            "reg",
    "SBTi":                  "reg",
    # Verification & Assurance — who checked it
    "CarbonSig Verifier Export v4": "verify",
    "ISO 14064-3":           "verify",
    "ISAE 3410":             "verify",
    "ISO 14065":             "verify",
    # Markets & Credits — what it is worth
    "CAD Trust":             "market",
    "Verra VCS":             "market",
    "ICAO CORSIA":           "market",
}

# pretty short labels for pills (default = raw standard name)
DISPLAY = {
    "WBCSD PACT":                   "WBCSD PACT v3",
    "GHG Protocol Scope 3":         "GHG Protocol · Sc.3",
    "EN 15804+A2":                  "EN 15804  ·  EPD",
    "EU ESRS":                      "CSRD / ESRS E1",
    "EU CBAM":                      "EU CBAM",
    "ISO 14068-1":                  "ISO 14068-1",
    "ISSB S2":                      "ISSB S2",
    "IRA 45V":                      "IRA 45V",
    "EU ETS MRV":                   "EU ETS MRV",
    "CarbonSig Verifier Export v4": "CarbonSig Verifier",
    "ISO 14064-3":                  "ISO 14064-3",
    "ISAE 3410":                    "ISAE 3410",
    "ISO 14065":                    "ISO 14065",
    "CAD Trust":                    "CAD Trust registry",
    "Verra VCS":                    "Verra VCS",
    "ICAO CORSIA":                  "ICAO CORSIA",
}

# standards intentionally not shown as clusters (vocab / infra / cross-cutting)
IGNORE = {"QUDT", "QUDT Unit", "W3C PROV", "schema.org", "UN SDG"}

MAX_PILLS = 5   # top-N standards per cluster, ranked by crosswalk count

# =========================================================================
# LOAD DATA — count term-level crosswalks per target standard
# =========================================================================
data = json.loads(DATA_PATH.read_text())
stats = data.get("stats", {})
counts = Counter(a["target_standard"] for a in data.get("alignments", []))

# bucket standards -> cluster, ranked by count
buckets: dict[str, list[tuple[str, int]]] = {"product": [], "reg": [], "verify": [], "market": []}
unmapped: list[str] = []
for std, n in counts.items():
    if std in IGNORE or std.lower().startswith("comet"):
        continue
    key = CLUSTER_OF.get(std)
    if key is None:
        unmapped.append(std)
        continue
    buckets[key].append((std, n))

for key in buckets:
    buckets[key].sort(key=lambda t: (-t[1], t[0]))
    buckets[key] = buckets[key][:MAX_PILLS]

if unmapped:
    print("WARNING: target_standard values not assigned to a cluster (add to CLUSTER_OF):")
    for std in unmapped:
        print(f"  - {std}  ({counts[std]} crosswalks)")

# =========================================================================
# SVG SCAFFOLD
# =========================================================================
svg: list[str] = []   # main buffer (bg, title, heart, pills, band)
conn: list[str] = []  # connector buffer (drawn behind the heart)


def add(s: str) -> None:
    svg.append(s)


def addc(s: str) -> None:
    conn.append(s)


def esc(t: str) -> str:
    # escape XML specials only; literal Unicode (·, →) passes through untouched
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── heart geometry ──────────────────────────────────────────────────────
HCX, HTY = 800, 542          # translate origin
HS = 3.55                    # scale


def hx(x: float) -> float:
    return HCX + x * HS


def hy(y: float) -> float:
    return HTY + y * HS


heart_pts = [
    ("M", 0, -30),
    ("C", 0, -33, -5, -45, -25, -45),
    ("C", -55, -45, -55, -10, -55, -10),
    ("C", -55, 15, -30, 30, 0, 50),
    ("C", 30, 30, 55, 15, 55, -10),
    ("C", 55, -10, 55, -45, 25, -45),
    ("C", 5, -45, 0, -33, 0, -30),
    ("Z",),
]


def heart_path() -> str:
    out = []
    for seg in heart_pts:
        c = seg[0]
        if c == "Z":
            out.append("Z")
            continue
        coords = seg[1:]
        pts = " ".join(f"{hx(coords[i]):.1f},{hy(coords[i + 1]):.1f}" for i in range(0, len(coords), 2))
        out.append(f"{c} {pts}")
    return " ".join(out)


HEART_TOP = hy(-45)
HEART_TIP = hy(50)
HEART_LEFT = hx(-55)
HEART_RIGHT = hx(55)
HEART_CX = HCX
HEART_MIDY = (HEART_TOP + HEART_TIP) / 2 + 10

# ── pill / connector helpers ────────────────────────────────────────────
PILL_W, PILL_H, PILL_GAP = 190, 34, 12


def pill(cx: float, cy: float, name: str, count: int, color: str) -> None:
    x = cx - PILL_W / 2
    y = cy - PILL_H / 2
    add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{PILL_W:.1f}" height="{PILL_H:.1f}" rx="8" fill="#ffffff"/>')
    add(f'<rect x="{x:.1f}" y="{y:.1f}" width="5" height="{PILL_H:.1f}" fill="{color}"/>')
    add(f'<text x="{x + 15:.1f}" y="{cy:.1f}" dominant-baseline="central" '
        f'font-family="{FONT_SANS}" font-size="13.5" font-weight="600" fill="{color}">{esc(name)}</text>')
    add(f'<text x="{x + PILL_W - 13:.1f}" y="{cy:.1f}" text-anchor="end" dominant-baseline="central" '
        f'font-family="{FONT_MONO}" font-size="11.5" fill="{MUTED}">{count}</text>')


def connector(x1: float, y1: float, x2: float, y2: float, color: str, curve: float = 0.45) -> None:
    dx = x2 - x1
    c1x = x1 + dx * curve
    c2x = x2 - dx * curve
    addc(f'<path d="M {x1:.1f},{y1:.1f} C {c1x:.1f},{y1:.1f} {c2x:.1f},{y2:.1f} {x2:.1f},{y2:.1f}" '
         f'fill="none" stroke="{color}" stroke-width="2.2" opacity="0.7"/>')


# =========================================================================
# BACKGROUND
# =========================================================================
add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
    f'font-family="{FONT_SANS}" role="img" '
    f'aria-label="COMET is the shared language at the heart of carbon data interoperability. '
    f'Four standards domains — Product and Footprint, Regulation and Disclosure, Verification and Assurance, '
    f'and Markets and Credits — feed into the COMET graph, which every stakeholder group reads. '
    f'Each standard shows its number of term-level crosswalks into COMET.">')
add(f'<rect width="{W}" height="{H}" fill="{PAPER}"/>')

# =========================================================================
# TITLE
# =========================================================================
add(f'<text x="{W / 2}" y="50" text-anchor="middle" font-family="{FONT_MONO}" '
    f'font-size="13" letter-spacing="3" fill="{MUTED}">COMET &#183; CARBON ONTOLOGY FOR MARKETS, EMISSIONS &amp; TRADE</text>')
add(f'<text x="{W / 2}" y="93" text-anchor="middle" font-family="{FONT_SERIF}" '
    f'font-size="33" font-weight="700" fill="{INK}">One shared language at the heart of carbon data</text>')
n_std = sum(1 for s in counts if s not in IGNORE and not s.lower().startswith("comet"))
add(f'<text x="{W / 2}" y="122" text-anchor="middle" font-family="{FONT_MONO}" font-size="12.5" '
    f'fill="{MUTED}">{stats.get("alignments", sum(counts.values()))} term-level crosswalks &#183; '
    f'{n_std} external standards &#183; {stats.get("terms", "")} terms &#183; '
    f'pill number = crosswalks into COMET</text>')

# =========================================================================
# CLUSTERS  (each: header bar + vertical pill stack + connectors)
# =========================================================================
CLUSTER_META = {
    "product": ("Product & Footprint", "WHAT A PRODUCT EMITS", C_PRODUCT, "ingests & normalises"),
    "reg":     ("Regulation & Disclosure", "WHAT MUST BE REPORTED", C_REG, "emits compliance"),
    "verify":  ("Verification & Assurance", "WHO CHECKED IT", C_VERIFY, "carries audited claims"),
    "market":  ("Markets & Credits", "WHAT IT IS WORTH", C_MARKET, "prices the signal"),
}


def cluster(key: str, side: str, top_y: float, anchor_x: float, anchor_y0: float, anchor_y1: float) -> None:
    title, subtitle, color, edge_label = CLUSTER_META[key]
    items = buckets[key]
    left = side == "L"
    hdr_w = 340
    hdr_x = 36 if left else W - 36 - hdr_w

    add(f'<rect x="{hdr_x}" y="{top_y}" width="{hdr_w}" height="46" rx="8" fill="{color}"/>')
    add(f'<text x="{hdr_x + hdr_w / 2}" y="{top_y + 21}" text-anchor="middle" '
        f'font-family="{FONT_SANS}" font-size="18" font-weight="700" fill="#ffffff">{esc(title)}</text>')
    add(f'<text x="{hdr_x + hdr_w / 2}" y="{top_y + 38}" text-anchor="middle" '
        f'font-family="{FONT_MONO}" font-size="10.5" fill="#ffffff" opacity="0.85" '
        f'letter-spacing="1">{esc(subtitle)}</text>')

    py = top_y + 46 + 22
    pill_cx = hdr_x + hdr_w / 2
    edge_x = pill_cx + (PILL_W / 2 if left else -PILL_W / 2)
    stub = 26 if left else -26
    edges = []
    for std, n in items:
        pill(pill_cx, py, DISPLAY.get(std, std), n, color)
        edges.append((edge_x, py))
        py += PILL_H + PILL_GAP

    m = len(edges)
    for i, (ex, ey) in enumerate(edges):
        ay = anchor_y0 + (anchor_y1 - anchor_y0) * (i / max(m - 1, 1))
        addc(f'<line x1="{ex:.1f}" y1="{ey:.1f}" x2="{ex + stub:.1f}" y2="{ey:.1f}" '
             f'stroke="{color}" stroke-width="2.2" opacity="0.7"/>')
        connector(ex + stub, ey, anchor_x, ay, color)

    mid_x = (edge_x + stub + anchor_x) / 2
    mid_y = (edges[0][1] + edges[-1][1]) / 2 + (-14 if top_y < 400 else 16)
    addc(f'<text x="{mid_x:.1f}" y="{mid_y:.1f}" text-anchor="middle" '
         f'font-family="{FONT_SANS}" font-size="13.5" font-style="italic" fill="{color}">{esc(edge_label)}</text>')


cluster("product", "L", 150, HEART_LEFT + 40, HEART_TOP + 64, HEART_MIDY - 14)
cluster("verify",  "L", 560, HEART_LEFT + 52, HEART_MIDY + 22, HEART_TIP - 36)
cluster("reg",     "R", 150, HEART_RIGHT - 40, HEART_TOP + 64, HEART_MIDY - 14)
cluster("market",  "R", 560, HEART_RIGHT - 52, HEART_MIDY + 22, HEART_TIP - 36)

# =========================================================================
# CENTRE HEART  (connectors are spliced in just before this, behind the heart)
# =========================================================================
add("<!--CONN-->")
add(f'<ellipse cx="{HEART_CX}" cy="{HEART_TIP - 8}" rx="150" ry="26" fill="{ACCENT}" opacity="0.10"/>')
add(f'<path d="{heart_path()}" fill="{ACCENT}"/>')
add(f'<text x="{HEART_CX}" y="{HEART_MIDY - 34:.1f}" text-anchor="middle" '
    f'font-family="{FONT_SERIF}" font-size="62" font-weight="700" fill="#ffffff" letter-spacing="1">COMET</text>')
add(f'<text x="{HEART_CX}" y="{HEART_MIDY + 4:.1f}" text-anchor="middle" '
    f'font-family="{FONT_SANS}" font-size="16" font-weight="500" fill="#ffe6dc" letter-spacing="0.5">Shared Carbon Language</text>')
add(f'<line x1="{HEART_CX - 70}" y1="{HEART_MIDY + 22:.1f}" x2="{HEART_CX + 70}" y2="{HEART_MIDY + 22:.1f}" '
    f'stroke="#ffffff" stroke-opacity="0.35" stroke-width="1"/>')
add(f'<text x="{HEART_CX}" y="{HEART_MIDY + 44:.1f}" text-anchor="middle" '
    f'font-family="{FONT_MONO}" font-size="12.5" fill="#ffd9cc" letter-spacing="0.5">7-layer interoperable graph</text>')
add(f'<text x="{HEART_CX}" y="{HEART_MIDY + 66:.1f}" text-anchor="middle" '
    f'font-family="{FONT_MONO}" font-size="11" fill="#ffc7b5" letter-spacing="0.5">L1 identity &#8594; L7 market signals</text>')

# =========================================================================
# STAKEHOLDER BAND  — one graph, read by every stakeholder
# =========================================================================
BAND_Y = 905
add(f'<line x1="60" y1="{BAND_Y - 18}" x2="{W - 60}" y2="{BAND_Y - 18}" stroke="{RULE}" stroke-width="1"/>')
add(f'<text x="{W / 2}" y="{BAND_Y + 6}" text-anchor="middle" font-family="{FONT_SERIF}" '
    f'font-size="18" font-style="italic" font-weight="600" fill="{INK}">'
    f'One graph &#8212; read &amp; written by every stakeholder</text>')

stakeholders = [
    "Steel & Metals", "Automotive OEMs", "Construction", "Finance & Investors",
    "Regulators", "LCA Consultants", "Logistics", "Carbon Markets",
    "Verifiers", "Data Platforms",
]
sp_h, sp_gap, pad = 30, 12, 18
widths = [len(s) * 7.4 + pad * 2 for s in stakeholders]
total = sum(widths) + sp_gap * (len(stakeholders) - 1)
x = (W - total) / 2
sy = BAND_Y + 40
for s, wd in zip(stakeholders, widths):
    add(f'<rect x="{x:.1f}" y="{sy - sp_h / 2:.1f}" width="{wd:.1f}" height="{sp_h}" rx="15" '
        f'fill="none" stroke="{ACCENT}" stroke-width="1.4"/>')
    add(f'<text x="{x + wd / 2:.1f}" y="{sy:.1f}" text-anchor="middle" dominant-baseline="central" '
        f'font-family="{FONT_SANS}" font-size="13" font-weight="500" fill="{ACCENT_DK}">{esc(s)}</text>')
    x += wd + sp_gap

add("</svg>")

# =========================================================================
# WRITE
# =========================================================================
doc = "\n".join(svg).replace("<!--CONN-->", "\n".join(conn))
OUT_PATH.write_text(doc)
print(f"wrote {OUT_PATH.relative_to(REPO_ROOT)}  ({len(doc)} bytes)")
for key, (title, *_rest) in CLUSTER_META.items():
    shown = ", ".join(f"{DISPLAY.get(s, s)}={n}" for s, n in buckets[key])
    print(f"  {title:26s} {shown}")
