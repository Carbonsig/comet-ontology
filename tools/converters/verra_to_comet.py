#!/usr/bin/env python3
"""Convert a Verra VCS / Gold Standard registry credit record to COMET JSON-LD.

SCAFFOLD (v0.3.0): public API, CLI and COMET skeleton in place; full Verra
Registry / Gold Standard Impact Registry API field mapping is a TODO.

Target COMET classes:
    comet-eac:EAC
    comet-eac:CertificateRegistry
    comet-eac:RetirementEvent
    comet-ver:ValidationRecord
    comet-ver:VerificationClaim

Usage:
    python verra_to_comet.py credit.json
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Any

COMET_CONTEXT = "https://comet.carbon/v1/jsonld/context.json"
COMET_TYPE = "comet-eac:EAC"

_REGISTRIES = {"verra": "Verra VCS", "vcs": "Verra VCS",
               "goldstandard": "Gold Standard", "gs": "Gold Standard"}


def convert_verra_to_comet(input_path: str | Path) -> dict[str, Any]:
    """Convert a registry credit JSON record into a COMET JSON-LD skeleton."""
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Registry record file not found: {input_path}")

    doc: dict[str, Any] = {
        "@context": COMET_CONTEXT,
        "@type": COMET_TYPE,
        "eacId": str(uuid.uuid4()),
        "_status": "scaffold",
    }

    if input_path.suffix.lower() == ".json":
        rec = json.loads(input_path.read_text(encoding="utf-8"))
        reg = (rec.get("registry") or "").strip().lower()
        if reg:
            doc["registry"] = _REGISTRIES.get(reg, rec["registry"])
        for k in ("serialNumber", "vintageYear", "unitCount", "unitType",
                  "unitStatus", "projectId", "methodology"):
            if rec.get(k) is not None:
                doc[k] = rec[k]
        return doc

    # ── TODO: Verra / Gold Standard registry API mapping ─────────────
    # 1. Map registry unit-block serial range to comet-eac:EAC.serialNumber.
    # 2. Map issuance/retirement events to comet-eac:RetirementEvent.
    # 3. Map validation/verification report metadata to comet-ver:ValidationRecord
    #    and comet-ver:VerificationClaim (with the new FindingsLog / CAR terms).
    # 4. Map SD-VISta / co-benefits to comet-eac:CoBenefit.
    raise NotImplementedError(
        "Verra / Gold Standard registry API mapping is not yet implemented; pass "
        "a JSON record for the scaffold path, or contribute the mapping (see TODO)."
    )


def convert(input_path: str) -> dict[str, Any]:
    """Bridge for comet_cli.py."""
    return convert_verra_to_comet(input_path)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert a Verra VCS / Gold Standard credit record to COMET JSON-LD (scaffold).",
    )
    parser.add_argument("input", type=Path, help="Path to the registry record JSON file")
    parser.add_argument("--output", "-o", type=Path, default=None,
                        help="Output file (default: stdout)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        doc = convert_verra_to_comet(args.input)
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
