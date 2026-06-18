#!/usr/bin/env python3
"""Convert an IRA 45V clean-hydrogen attestation into COMET JSON-LD.

Maps a producer's 45V production record (lifecycle carbon intensity from the
45VH2-GREET model, production volume, provenance) into a COMET JSON-LD document
populating the v0.3.0 terms:

    comet-pcf:CarbonIntensity            lifecycle CI in kgCO2e/kgH2
    comet-mkt:CleanHydrogenCreditTier    statutory 45V credit tier + USD/kg value
    comet-eac:EnergyAttributeCert        EAC / book-and-claim backing (optional)

The four statutory 45V tiers (26 USC 45V(b)) keyed to lifecycle CI:

    CI < 0.45 kgCO2e/kgH2          -> 100% credit  ($3.00/kg with prevailing wage)
    0.45 <= CI < 1.5              -> 33.4% credit  ($1.002/kg)
    1.5  <= CI < 2.5             -> 25%  credit  ($0.75/kg)
    2.5  <= CI <= 4.0           -> 20%  credit  ($0.60/kg)
    CI > 4.0                      -> not eligible

Usage:
    python h45v_to_comet.py attestation.json
    python h45v_to_comet.py attestation.json --output comet_45v.json

As a library:
    from h45v_to_comet import convert_45v_to_comet
    doc = convert_45v_to_comet("attestation.json")
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Any

COMET_CONTEXT = "https://comet.carbon/v1/jsonld/context.json"
COMET_TYPE = "comet-pcf:CarbonIntensity"

# Full-rate credit with prevailing-wage & apprenticeship multiplier (USD/kgH2).
_FULL_RATE = 3.00

# (ci_low_inclusive, ci_high_exclusive, fraction_of_full_rate, label)
_TIERS: list[tuple[float, float, float, str]] = [
    (0.0, 0.45, 1.000, "Tier 1 (<0.45 kgCO2e/kgH2)"),
    (0.45, 1.5, 0.334, "Tier 2 (0.45-1.5)"),
    (1.5, 2.5, 0.250, "Tier 3 (1.5-2.5)"),
    (2.5, 4.0, 0.200, "Tier 4 (2.5-4.0)"),
]
_MAX_ELIGIBLE_CI = 4.0


def classify_45v_tier(ci: float) -> dict[str, Any]:
    """Return the statutory 45V tier, credit fraction and USD/kg value for a CI.

    Parameters
    ----------
    ci : lifecycle carbon intensity in kgCO2e per kg H2 (well-to-gate, 45VH2-GREET)

    Returns
    -------
    dict with keys: eligible, tierLabel, creditFraction, creditValue (USD/kgH2)
    """
    if ci < 0 or ci > _MAX_ELIGIBLE_CI:
        return {"eligible": False, "tierLabel": "Not eligible (CI > 4.0)",
                "creditFraction": 0.0, "creditValue": 0.0}
    for low, high, frac, label in _TIERS:
        # Upper bound exclusive except the final tier which is inclusive of 4.0.
        upper_ok = ci < high or (high == 4.0 and ci <= 4.0)
        if low <= ci and upper_ok:
            return {
                "eligible": True,
                "tierLabel": label,
                "creditFraction": frac,
                "creditValue": round(_FULL_RATE * frac, 4),
            }
    return {"eligible": False, "tierLabel": "Not eligible",
            "creditFraction": 0.0, "creditValue": 0.0}


# ── Public API ───────────────────────────────────────────────────────

def convert_45v_to_comet(input_path: str | Path) -> dict[str, Any]:
    """Convert a 45V attestation JSON into a COMET JSON-LD document."""
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Attestation file not found: {input_path}")

    rec = json.loads(input_path.read_text(encoding="utf-8"))

    ci = rec.get("lifecycleCarbonIntensity", rec.get("ci"))
    if ci is None:
        raise ValueError("Attestation must include 'lifecycleCarbonIntensity' "
                         "(kgCO2e/kgH2).")
    ci = float(ci)
    tier = classify_45v_tier(ci)

    doc: dict[str, Any] = {
        "@context": COMET_CONTEXT,
        "@type": COMET_TYPE,
        "attestationId": str(uuid.uuid4()),
        "carbonIntensity": {
            "@type": "comet-pcf:CarbonIntensity",
            "value": ci,
            "unit": "kgCO2e/kgH2",
            "functionalBasis": "perKgH2",
            "method": rec.get("method", "45VH2-GREET"),
        },
        "creditTier": {
            "@type": "comet-mkt:CleanHydrogenCreditTier",
            "tierLabel": tier["tierLabel"],
            "eligible": tier["eligible"],
            "creditFraction": tier["creditFraction"],
            "creditValue": tier["creditValue"],
            "creditUnit": "USD/kgH2",
            "statute": "26 USC 45V",
        },
    }

    if rec.get("orgName"):
        doc["producer"] = {"orgName": rec["orgName"]}
        if rec.get("orgId"):
            doc["producer"]["orgId"] = [rec["orgId"]] if isinstance(rec["orgId"], str) else rec["orgId"]

    if rec.get("productionVolumeKg") is not None:
        vol = float(rec["productionVolumeKg"])
        doc["productionVolumeKg"] = vol
        if tier["eligible"]:
            doc["creditTier"]["estimatedCreditUSD"] = round(vol * tier["creditValue"], 2)

    if rec.get("productionPeriod"):
        doc["reportingPeriod"] = rec["productionPeriod"]

    # Optional EAC / book-and-claim backing for clean-power input.
    eac = rec.get("energyAttributeCertificate")
    if isinstance(eac, dict) and eac:
        doc["energyAttributeCert"] = {"@type": "comet-eac:EnergyAttributeCert", **eac}

    ver = rec.get("verification")
    if isinstance(ver, dict) and ver:
        doc["verification"] = {"@type": "comet-ver:VerificationClaim", **ver}

    return doc


# ── CLI bridge ────────────────────────────────────────────────────────

def convert(input_path: str) -> dict[str, Any]:
    """Bridge for comet_cli.py."""
    return convert_45v_to_comet(input_path)


# ── CLI ──────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert an IRA 45V clean-hydrogen attestation to COMET JSON-LD.",
        epilog=(
            "Examples:\n"
            "  python h45v_to_comet.py attestation.json\n"
            "  python h45v_to_comet.py attestation.json -o comet_45v.json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", type=Path, help="Path to the 45V attestation JSON file")
    parser.add_argument("--output", "-o", type=Path, default=None,
                        help="Output file (default: stdout)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        doc = convert_45v_to_comet(args.input)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
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
