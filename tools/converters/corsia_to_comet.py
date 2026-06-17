#!/usr/bin/env python3
"""Convert an ICAO CORSIA eligible-emissions-unit record to COMET JSON-LD.

SCAFFOLD (v0.3.0): public API, CLI and COMET skeleton in place; full ICAO TAB
eligible-unit registry-field mapping is a TODO.

Target COMET classes:
    comet-eac:CORSIAEligibleUnit
    comet-eac:EAC
    comet-eac:RetirementEvent

Usage:
    python corsia_to_comet.py unit.json
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Any

COMET_CONTEXT = "https://comet.carbon/v1/jsonld/context.json"
COMET_TYPE = "comet-eac:CORSIAEligibleUnit"


def convert_corsia_to_comet(input_path: str | Path) -> dict[str, Any]:
    """Convert a CORSIA eligible-unit JSON record into a COMET JSON-LD skeleton."""
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"CORSIA unit file not found: {input_path}")

    doc: dict[str, Any] = {
        "@context": COMET_CONTEXT,
        "@type": COMET_TYPE,
        "unitId": str(uuid.uuid4()),
        "_status": "scaffold",
    }

    if input_path.suffix.lower() == ".json":
        rec = json.loads(input_path.read_text(encoding="utf-8"))
        for k in ("serialNumber", "registry", "programName", "vintageYear",
                  "unitCount", "eligiblePeriod"):
            if rec.get(k) is not None:
                doc[k] = rec[k]
        return doc

    # ── TODO: ICAO CORSIA registry mapping ───────────────────────────
    # 1. Map ICAO TAB eligible-programme + unit serial block to comet-eac:EAC.
    # 2. Map CORSIA phase/vintage eligibility to CORSIAEligibleUnit.eligiblePeriod.
    # 3. Map cancellation/retirement to comet-eac:RetirementEvent with
    #    retirementBeneficiary = the operator's compliance obligation.
    raise NotImplementedError(
        "ICAO CORSIA registry mapping is not yet implemented; pass a JSON record "
        "for the scaffold path, or contribute the registry mapping (see TODO)."
    )


def convert(input_path: str) -> dict[str, Any]:
    """Bridge for comet_cli.py."""
    return convert_corsia_to_comet(input_path)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert an ICAO CORSIA eligible unit to COMET JSON-LD (scaffold).",
    )
    parser.add_argument("input", type=Path, help="Path to the CORSIA unit JSON file")
    parser.add_argument("--output", "-o", type=Path, default=None,
                        help="Output file (default: stdout)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        doc = convert_corsia_to_comet(args.input)
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
