#!/usr/bin/env python3
"""Generate the COMET 'at the heart' hub diagram as a standalone SVG.
Mirrors the Smart Freight Centre GLEC/ISO-14083 heart graphic, but tells
COMET's story: COMET is the shared language at the centre; four standards
domains feed in; ten MECE stakeholder groups read the single graph."""

import math

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

svg = []          # main buffer (bg, title, heart, pills, band)
conn = []         # connector buffer (drawn behind the heart)
def add(s): svg.append(s)
def addc(s): conn.append(s)

def esc(t):
    # escape XML specials only; literal Unicode (·, →) passes through untouched
    return (t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"))

# ── heart geometry ──────────────────────────────────────────────────────
# unit heart (dip top ~ -30, lobes -45, tip +50), scaled & translated
HCX, HTY = 800, 542          # translate origin
HS = 3.55                    # scale
def hx(x): return HCX + x*HS
def hy(y): return HTY + y*HS

heart_pts = [
    ("M", 0,-30),
    ("C", 0,-33, -5,-45, -25,-45),
    ("C", -55,-45, -55,-10, -55,-10),
    ("C", -55,15, -30,30, 0,50),
    ("C", 30,30, 55,15, 55,-10),
    ("C", 55,-10, 55,-45, 25,-45),
    ("C", 5,-45, 0,-33, 0,-30),
    ("Z",),
]
def heart_path():
    out=[]
    for seg in heart_pts:
        c=seg[0]
        if c=="Z": out.append("Z"); continue
        coords=seg[1:]
        pts=" ".join(f"{hx(coords[i]):.1f},{hy(coords[i+1]):.1f}" for i in range(0,len(coords),2))
        out.append(f"{c} {pts}")
    return " ".join(out)

# heart bounding box in device coords
HEART_TOP    = hy(-45)   # ~382
HEART_TIP    = hy(50)    # ~719
HEART_LEFT   = hx(-55)   # ~605
HEART_RIGHT  = hx(55)    # ~995
HEART_CX     = HCX
HEART_MIDY   = (HEART_TOP+HEART_TIP)/2 + 10

# ── pill / connector helpers ────────────────────────────────────────────
def pill(cx, cy, w, h, text, fill, txt="#ffffff", fs=15, bold=True, r=9):
    x=cx-w/2; y=cy-h/2
    add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" '
        f'fill="{fill}"/>')
    weight = "600" if bold else "500"
    add(f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" dominant-baseline="central" '
        f'font-family="{FONT_SANS}" font-size="{fs}" font-weight="{weight}" '
        f'fill="{txt}">{esc(text)}</text>')

def connector(x1,y1,x2,y2,color, label=None, curve=0.45, lbl_x=None, lbl_y=None):
    # smooth cubic from a pill edge (x1,y1) to a heart anchor (x2,y2) — drawn behind the heart
    dx=(x2-x1)
    c1x=x1+dx*curve; c1y=y1
    c2x=x2-dx*curve; c2y=y2
    addc(f'<path d="M {x1:.1f},{y1:.1f} C {c1x:.1f},{c1y:.1f} {c2x:.1f},{c2y:.1f} {x2:.1f},{y2:.1f}" '
        f'fill="none" stroke="{color}" stroke-width="2.2" opacity="0.7"/>')
    if label:
        lx = lbl_x if lbl_x is not None else (x1+x2)/2
        ly = lbl_y if lbl_y is not None else (y1+y2)/2
        addc(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" '
            f'font-family="{FONT_SANS}" font-size="13" font-style="italic" '
            f'fill="{color}">{esc(label)}</text>')

# =========================================================================
# BACKGROUND
# =========================================================================
add(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
    f'font-family="{FONT_SANS}" role="img" '
    f'aria-label="COMET is the shared language at the heart of carbon data interoperability. '
    f'Four standards domains — Product and Footprint, Regulation and Disclosure, Verification and Assurance, '
    f'and Markets and Credits — feed into the COMET graph, which every stakeholder group reads.">')
add(f'<rect width="{W}" height="{H}" fill="{PAPER}"/>')

# =========================================================================
# TITLE
# =========================================================================
add(f'<text x="{W/2}" y="52" text-anchor="middle" font-family="{FONT_MONO}" '
    f'font-size="13" letter-spacing="3" fill="{MUTED}">COMET &#183; CARBON ONTOLOGY FOR MARKETS, EMISSIONS &amp; TRADE</text>')
add(f'<text x="{W/2}" y="97" text-anchor="middle" font-family="{FONT_SERIF}" '
    f'font-size="33" font-weight="700" fill="{INK}">One shared language at the heart of carbon data</text>')

# =========================================================================
# CENTRE HEART  (connectors are spliced in just before this, behind the heart)
# =========================================================================
add("<!--CONN-->")
# soft shadow under the heart
add(f'<ellipse cx="{HEART_CX}" cy="{HEART_TIP-8}" rx="150" ry="26" fill="{ACCENT}" opacity="0.10"/>')
add(f'<path d="{heart_path()}" fill="{ACCENT}"/>')
# COMET wordmark + tagline reversed out
add(f'<text x="{HEART_CX}" y="{HEART_MIDY-34:.1f}" text-anchor="middle" '
    f'font-family="{FONT_SERIF}" font-size="62" font-weight="700" fill="#ffffff" '
    f'letter-spacing="1">COMET</text>')
add(f'<text x="{HEART_CX}" y="{HEART_MIDY+4:.1f}" text-anchor="middle" '
    f'font-family="{FONT_SANS}" font-size="16" font-weight="500" fill="#ffe6dc" '
    f'letter-spacing="0.5">Shared Carbon Language</text>')
add(f'<line x1="{HEART_CX-70}" y1="{HEART_MIDY+22:.1f}" x2="{HEART_CX+70}" y2="{HEART_MIDY+22:.1f}" '
    f'stroke="#ffffff" stroke-opacity="0.35" stroke-width="1"/>')
add(f'<text x="{HEART_CX}" y="{HEART_MIDY+44:.1f}" text-anchor="middle" '
    f'font-family="{FONT_MONO}" font-size="12.5" fill="#ffd9cc" letter-spacing="0.5">7-layer interoperable graph</text>')
add(f'<text x="{HEART_CX}" y="{HEART_MIDY+66:.1f}" text-anchor="middle" '
    f'font-family="{FONT_MONO}" font-size="11" fill="#ffc7b5" letter-spacing="0.5">L1 identity &#8594; L7 market signals</text>')

# =========================================================================
# CLUSTERS
# each: header (x,y,w), colour, tagline into heart, list of standard pills
# =========================================================================
PILL_W, PILL_H, PILL_GAP = 190, 34, 12

def cluster(side, top_y, color, title, subtitle, items, edge_label,
            anchor_x, anchor_y0, anchor_y1):
    """side: 'L' or 'R'. Header bar + vertical pill stack + connectors to heart."""
    left = side=='L'
    hdr_w = 340
    if left:
        hdr_x = 36
    else:
        hdr_x = W-36-hdr_w
    # header bar
    add(f'<rect x="{hdr_x}" y="{top_y}" width="{hdr_w}" height="46" rx="8" fill="{color}"/>')
    add(f'<text x="{hdr_x+hdr_w/2}" y="{top_y+21}" text-anchor="middle" '
        f'font-family="{FONT_SANS}" font-size="18" font-weight="700" fill="#ffffff">{esc(title)}</text>')
    add(f'<text x="{hdr_x+hdr_w/2}" y="{top_y+38}" text-anchor="middle" '
        f'font-family="{FONT_MONO}" font-size="10.5" fill="#ffffff" opacity="0.85" '
        f'letter-spacing="1">{esc(subtitle)}</text>')
    # pills
    py = top_y + 46 + 22
    pill_cx = hdr_x + PILL_W/2 + (hdr_w-PILL_W)/2
    # inner edge x (toward centre) for connectors
    edge_x = pill_cx + (PILL_W/2 if left else -PILL_W/2)
    edges=[]
    for it in items:
        pill(pill_cx, py, PILL_W, PILL_H, it, "#ffffff" , txt=color, fs=14, bold=True, r=8)
        # thin coloured left rule inside pill
        add(f'<rect x="{pill_cx-PILL_W/2}" y="{py-PILL_H/2}" width="5" height="{PILL_H}" '
            f'rx="0" fill="{color}"/>')
        edges.append((edge_x, py))
        py += PILL_H + PILL_GAP
    # connectors: fan pill edges to a span of anchor points on the heart
    n=len(edges)
    # short horizontal stub out of each pill, then curve to the heart
    stub = 26 if left else -26
    for i,(ex,ey) in enumerate(edges):
        ay = anchor_y0 + (anchor_y1-anchor_y0)*(i/(max(n-1,1)))
        addc(f'<line x1="{ex:.1f}" y1="{ey:.1f}" x2="{ex+stub:.1f}" y2="{ey:.1f}" '
             f'stroke="{color}" stroke-width="2.2" opacity="0.7"/>')
        connector(ex+stub,ey, anchor_x, ay, color)
    # single italic edge-label placed midway between cluster and heart
    mid_x = (edge_x + stub + anchor_x)/2
    mid_y = (edges[0][1] + edges[-1][1])/2 + (-14 if top_y<400 else 16)
    addc(f'<text x="{mid_x:.1f}" y="{mid_y:.1f}" text-anchor="middle" '
         f'font-family="{FONT_SANS}" font-size="13.5" font-style="italic" fill="{color}">'
         f'{esc(edge_label)}</text>')
    return py

# anchor spans on heart perimeter (device coords)
# top-left cluster -> upper-left lobe;  bottom-left -> lower-left
# top-right -> upper-right lobe; bottom-right -> lower-right
prod_end = cluster('L', 150, C_PRODUCT,
    "Product & Footprint",
    "WHAT A PRODUCT EMITS",
    ["ISO 14067  ·  PCF", "GHG Protocol (product)", "PACT v3 exchange", "EN 15804  ·  EPD"],
    "ingests & normalises",
    HEART_LEFT+40, HEART_TOP+64, HEART_MIDY-14)

verify_end = cluster('L', 560, C_VERIFY,
    "Verification & Assurance",
    "WHO CHECKED IT",
    ["ISO 14064-3", "ISO 14065  ·  ISAE 3410", "ResponsibleSteel", "ASI (aluminium)"],
    "carries audited claims",
    HEART_LEFT+52, HEART_MIDY+22, HEART_TIP-36)

reg_end = cluster('R', 150, C_REG,
    "Regulation & Disclosure",
    "WHAT MUST BE REPORTED",
    ["EU CBAM", "CSRD / ESRS E1", "ISSB S2  ·  ISO 14064-1", "IRA 45V  ·  CORSIA"],
    "emits compliance",
    HEART_RIGHT-40, HEART_TOP+64, HEART_MIDY-14)

market_end = cluster('R', 560, C_MARKET,
    "Markets & Credits",
    "WHAT IT IS WORTH",
    ["Verra  ·  Gold Standard", "Article 6 (ITMOs)", "CAD Trust registry", "I-REC / EAC  ·  premiums"],
    "prices the signal",
    HEART_RIGHT-52, HEART_MIDY+22, HEART_TIP-36)

# =========================================================================
# STAKEHOLDER BAND  — one graph, read by every stakeholder
# =========================================================================
BAND_Y = 905
add(f'<line x1="60" y1="{BAND_Y-18}" x2="{W-60}" y2="{BAND_Y-18}" stroke="{RULE}" stroke-width="1"/>')
add(f'<text x="{W/2}" y="{BAND_Y+6}" text-anchor="middle" font-family="{FONT_SERIF}" '
    f'font-size="18" font-style="italic" font-weight="600" fill="{INK}">'
    f'One graph &#8212; read &amp; written by every stakeholder</text>')

stakeholders = [
    "Steel & Metals", "Automotive OEMs", "Construction", "Finance & Investors",
    "Regulators", "LCA Consultants", "Logistics", "Carbon Markets",
    "Verifiers", "Data Platforms",
]
# lay out as centred pill row
sp_h=30; sp_gap=12; pad=18
# measure approximate widths (char*7.2 + pad*2)
widths=[len(s)*7.4+pad*2 for s in stakeholders]
total=sum(widths)+sp_gap*(len(stakeholders)-1)
x=(W-total)/2
sy=BAND_Y+40
for s,wd in zip(stakeholders,widths):
    add(f'<rect x="{x:.1f}" y="{sy-sp_h/2:.1f}" width="{wd:.1f}" height="{sp_h}" rx="15" '
        f'fill="none" stroke="{ACCENT}" stroke-width="1.4"/>')
    add(f'<text x="{x+wd/2:.1f}" y="{sy:.1f}" text-anchor="middle" dominant-baseline="central" '
        f'font-family="{FONT_SANS}" font-size="13" font-weight="500" fill="{ACCENT_DK}">{esc(s)}</text>')
    x+=wd+sp_gap

add('</svg>')

doc = "\n".join(svg).replace("<!--CONN-->", "\n".join(conn))
out="/Users/nickgogerty/Projects/comet-ontology/docs/assets/comet-at-the-heart.svg"
open(out,"w").write(doc)
print("wrote", out, len(doc), "bytes")
