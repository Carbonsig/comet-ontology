#!/usr/bin/env python3
"""Convert a corporate GHG inventory (GHG Protocol / ESRS E1-6 shape) to COMET JSON-LD.

Accepts a flat JSON or CSV inventory of the kind companies file for CDP, CSRD/
ESRS E1, ISSB S2 and ISO 14064-1 reporting, and emits a COMET JSON-LD document
populating the v0.3.0 aggregate-inventory terms:

    comet-sc:Scope1Emissions
    comet-sc:Scope2Emissions   (location-based + market-based)
    comet-sc:Scope3Emissions   (per category 1-15)
    comet-sc:BaseYearEmissions
    comet-sc:EmissionIntensity

Usage:
    python ghgprotocol_to_comet.py inventory.json
    python ghgprotocol_to_comet.py inventory.csv --output comet_inventory.json

As a library:
    from ghgprotocol_to_comet import convert_ghgprotocol_to_comet
    doc = convert_ghgprotocol_to_comet("inventory.json")

Input JSON shape (all fields optional except orgName + reportingYear):
    {
      "orgName": "Acme Corp",
      "orgId": "LEI:5493001KJTIIGC8Y1R12",
      "reportingYear": 2025,
      "baseYear": 2019,
      "scope1": 120000.0,
      "scope2_location": 80000.0,
      "scope2_market": 65000.0,
      "scope3": {"1": 450000, "11": 1200000},
      "baseYearTotal": 1800000.0,
      "intensity": {"value": 12.4, "unit": "tCO2e/MEUR revenue"},
      "verification": {"verifierName": "DNV", "levelType": "limited",
                       "standardRef": "ISO 14064-3"}
    }

CSV shape: header row with columns scope1, scope2_location, scope2_market,
scope3_1 … scope3_15, base_year_total, intensity_value, intensity_unit,
org_name, reporting_year, base_year.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import uuid
from pathlib import Path
from typing import Any

COMET_CONTEXT = "https://comet.carbon/v1/jsonld/context.json"
COMET_TYPE = "comet-sc:OrganizationalInventory"

_VALID_SCOPE3 = {str(i) for i in range(1, 16)}


def _num(v: Any) -> float | None:
    """Coerce a value to float, returning None for blanks/garbage."""
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _build_scope3(raw: Any) -> list[dict[str, Any]]:
    """Normalise a scope-3 mapping {category: value} into COMET category records."""
    out: list[dict[str, Any]] = []
    if not isinstance(raw, dict):
        return out
    for cat, val in raw.items():
        cat_str = str(cat).strip()
        num = _num(val)
        if cat_str not in _VALID_SCOPE3:
            print(f"Warning: skipping invalid Scope 3 category {cat!r} "
                  f"(must be 1-15).", file=sys.stderr)
            continue
        if num is None:
            continue
        out.append({
            "@type": "comet-sc:Scope3Emissions",
            "category": int(cat_str),
            "value": num,
            "unit": "tCO2e",
        })
    return sorted(out, key=lambda r: r["category"])


def _inventory_from_csv(path: Path) -> dict[str, Any]:
    """Read the first data row of a flat CSV inventory into the JSON shape."""
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise ValueError("CSV inventory is empty.")
    r = rows[0]
    scope3 = {str(i): r[f"scope3_{i}"] for i in range(1, 16)
              if r.get(f"scope3_{i}") not in (None, "")}
    return {
        "orgName": r.get("org_name") or r.get("orgName"),
        "orgId": r.get("org_id") or r.get("orgId"),
        "reportingYear": r.get("reporting_year") or r.get("reportingYear"),
        "baseYear": r.get("base_year") or r.get("baseYear"),
        "scope1": r.get("scope1"),
        "scope2_location": r.get("scope2_location"),
        "scope2_market": r.get("scope2_market"),
        "scope3": scope3,
        "baseYearTotal": r.get("base_year_total"),
        "intensity": {
            "value": r.get("intensity_value"),
            "unit": r.get("intensity_unit"),
        } if r.get("intensity_value") else None,
    }


# ── Public API ───────────────────────────────────────────────────────

def convert_ghgprotocol_to_comet(input_path: str | Path) -> dict[str, Any]:
    """Convert a GHG Protocol / ESRS inventory file into a COMET JSON-LD document."""
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Inventory file not found: {input_path}")

    if input_path.suffix.lower() == ".csv":
        inv = _inventory_from_csv(input_path)
    else:
        inv = json.loads(input_path.read_text(encoding="utf-8"))

    if not inv.get("orgName"):
        raise ValueError("Inventory must include 'orgName'.")

    doc: dict[str, Any] = {
        "@context": COMET_CONTEXT,
        "@type": COMET_TYPE,
        "inventoryId": str(uuid.uuid4()),
        "organization": {"orgName": inv["orgName"]},
    }
    if inv.get("orgId"):
        doc["organization"]["orgId"] = [inv["orgId"]] if isinstance(inv["orgId"], str) else inv["orgId"]
    if inv.get("reportingYear"):
        doc["reportingPeriod"] = {
            "startDate": f"{inv['reportingYear']}-01-01T00:00:00Z",
            "endDate": f"{inv['reportingYear']}-12-31T23:59:59Z",
        }

    s1 = _num(inv.get("scope1"))
    if s1 is not None:
        doc["scope1Emissions"] = {"@type": "comet-sc:Scope1Emissions",
                                  "value": s1, "unit": "tCO2e"}

    s2_loc = _num(inv.get("scope2_location"))
    s2_mkt = _num(inv.get("scope2_market"))
    if s2_loc is not None or s2_mkt is not None:
        s2: dict[str, Any] = {"@type": "comet-sc:Scope2Emissions", "unit": "tCO2e"}
        if s2_loc is not None:
            s2["locationBased"] = s2_loc
        if s2_mkt is not None:
            s2["marketBased"] = s2_mkt
        doc["scope2Emissions"] = s2

    scope3 = _build_scope3(inv.get("scope3"))
    if scope3:
        doc["scope3Emissions"] = scope3

    by = _num(inv.get("baseYearTotal"))
    if by is not None:
        doc["baseYearEmissions"] = {
            "@type": "comet-sc:BaseYearEmissions",
            "value": by, "unit": "tCO2e",
            "baseYear": inv.get("baseYear"),
        }

    intensity = inv.get("intensity")
    if isinstance(intensity, dict) and _num(intensity.get("value")) is not None:
        doc["emissionIntensity"] = {
            "@type": "comet-sc:EmissionIntensity",
            "value": _num(intensity["value"]),
            "unit": intensity.get("unit") or "tCO2e/unit",
        }

    ver = inv.get("verification")
    if isinstance(ver, dict) and ver:
        doc["verification"] = {"@type": "comet-ver:VerificationClaim", **ver}

    return doc


# ── CLI bridge ────────────────────────────────────────────────────────

def convert(input_path: str) -> dict[str, Any]:
    """Bridge for comet_cli.py."""
    return convert_ghgprotocol_to_comet(input_path)


# ── CLI ──────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert a GHG Protocol / ESRS corporate inventory to COMET JSON-LD.",
        epilog=(
            "Examples:\n"
            "  python ghgprotocol_to_comet.py inventory.json\n"
            "  python ghgprotocol_to_comet.py inventory.csv -o comet_inventory.json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", type=Path, help="Path to the inventory JSON or CSV file")
    parser.add_argument("--output", "-o", type=Path, default=None,
                        help="Output file (default: stdout)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        doc = convert_ghgprotocol_to_comet(args.input)
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
