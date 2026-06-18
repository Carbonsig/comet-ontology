#!/usr/bin/env python3
"""Convert an EN 15804 / ISO 14025 EPD (Environmental Product Declaration) to COMET JSON-LD.

SCAFFOLD (v0.3.0): the public API, CLI and COMET output skeleton are in place
and exercised by tools/converters/tests. Full ILCD+EPD / EN 15804 XML field
mapping is a TODO — see the marked section in convert_epd_to_comet().

Target COMET classes:
    comet-pcf:EPDDeclaration
    comet-pcf:ProductCarbonFootprint   (per-module A1-A3, C, D results)
    comet-pcf:PCRReference
    comet-pcf:UncertaintyAssessment

Usage:
    python epd_to_comet.py epd.xml
    python epd_to_comet.py epd.xml --output comet_epd.json
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Any

COMET_CONTEXT = "https://comet.carbon/v1/jsonld/context.json"
COMET_TYPE = "comet-pcf:EPDDeclaration"

# EN 15804+A2 lifecycle module codes (for the full mapping TODO).
EN15804_MODULES = [
    "A1", "A2", "A3", "A4", "A5", "B1", "B2", "B3", "B4", "B5", "B6", "B7",
    "C1", "C2", "C3", "C4", "D",
]


def convert_epd_to_comet(input_path: str | Path) -> dict[str, Any]:
    """Convert an EPD document into a COMET JSON-LD skeleton.

    Currently emits the document envelope plus any top-level metadata found in a
    simple JSON EPD. Full EN 15804 ILCD-XML parsing is not yet implemented.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"EPD file not found: {input_path}")

    doc: dict[str, Any] = {
        "@context": COMET_CONTEXT,
        "@type": COMET_TYPE,
        "epdId": str(uuid.uuid4()),
        "_status": "scaffold",  # removed once full mapping lands
    }

    # Minimal JSON passthrough so the skeleton is testable today.
    if input_path.suffix.lower() == ".json":
        rec = json.loads(input_path.read_text(encoding="utf-8"))
        for k in ("productName", "declaredUnit", "pcrReference", "programOperator",
                  "registrationNumber", "validUntil"):
            if rec.get(k) is not None:
                doc[k] = rec[k]
        if rec.get("gwpTotal") is not None:
            doc["productCarbonFootprint"] = {
                "@type": "comet-pcf:ProductCarbonFootprint",
                "totalGWP": float(rec["gwpTotal"]),
                "unit": "kgCO2e",
            }
        return doc

    # ── TODO: EN 15804 ILCD-XML mapping ──────────────────────────────
    # 1. Parse the ILCD <processDataSet> / EPD XML envelope.
    # 2. Map <exchanges> per-module GWP-total / GWP-fossil / GWP-biogenic to
    #    comet-pcf:ProductCarbonFootprint with module codes from EN15804_MODULES.
    # 3. Map <referenceToPrecedingDataSetVersion> / PCR to comet-pcf:PCRReference.
    # 4. Map declared-unit + scaling to comet-pcf:FunctionalUnit.
    # 5. Map uncertainty distribution to comet-pcf:UncertaintyAssessment.
    raise NotImplementedError(
        "EN 15804 ILCD-XML EPD parsing is not yet implemented; pass a simple "
        "JSON EPD for the scaffold path, or contribute the XML mapping (see TODO)."
    )


def convert(input_path: str) -> dict[str, Any]:
    """Bridge for comet_cli.py."""
    return convert_epd_to_comet(input_path)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert an EN 15804 / ISO 14025 EPD to COMET JSON-LD (scaffold).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", type=Path, help="Path to the EPD file (JSON scaffold or XML)")
    parser.add_argument("--output", "-o", type=Path, default=None,
                        help="Output file (default: stdout)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        doc = convert_epd_to_comet(args.input)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except NotImplementedError as exc:
        print(f"Not implemented: {exc}", file=sys.stderr)
        return 2
    text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
