#!/usr/bin/env python3
"""Smoke / round-trip tests for the v0.3.0 COMET converters.

Run:
    tools/.venv/bin/python tools/converters/tests/test_v030_converters.py

Exits non-zero on first failure. No external deps (stdlib only).
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve()
CONV_DIR = HERE.parents[1]
sys.path.insert(0, str(CONV_DIR))

import ghgprotocol_to_comet as ghg          # noqa: E402
import h45v_to_comet as h45v                  # noqa: E402
import epd_to_comet as epd                    # noqa: E402
import corsia_to_comet as corsia              # noqa: E402
import verra_to_comet as verra                # noqa: E402

_fails = 0


def check(cond: bool, msg: str) -> None:
    global _fails
    status = "PASS" if cond else "FAIL"
    if not cond:
        _fails += 1
    print(f"  [{status}] {msg}")


def _write(tmp: Path, name: str, obj) -> Path:
    p = tmp / name
    p.write_text(json.dumps(obj), encoding="utf-8")
    return p


def test_ghgprotocol(tmp: Path) -> None:
    print("GHG Protocol / ESRS converter (full):")
    inv = {
        "orgName": "Acme Corp", "orgId": "LEI:5493001KJTIIGC8Y1R12",
        "reportingYear": 2025, "baseYear": 2019,
        "scope1": 120000.0, "scope2_location": 80000.0, "scope2_market": 65000.0,
        "scope3": {"1": 450000, "11": 1200000, "99": 1},  # 99 invalid -> skipped
        "baseYearTotal": 1800000.0,
        "intensity": {"value": 12.4, "unit": "tCO2e/MEUR"},
        "verification": {"verifierName": "DNV", "levelType": "limited",
                         "standardRef": "ISO 14064-3"},
    }
    doc = ghg.convert_ghgprotocol_to_comet(_write(tmp, "inv.json", inv))
    check(doc["@type"] == "comet-sc:OrganizationalInventory", "@type is OrganizationalInventory")
    check(doc["scope1Emissions"]["value"] == 120000.0, "scope1 mapped")
    check(doc["scope2Emissions"]["locationBased"] == 80000.0, "scope2 location-based mapped")
    check(doc["scope2Emissions"]["marketBased"] == 65000.0, "scope2 market-based mapped")
    cats = [s["category"] for s in doc["scope3Emissions"]]
    check(cats == [1, 11], "scope3 valid categories kept & sorted; invalid 99 dropped")
    check(doc["baseYearEmissions"]["value"] == 1800000.0, "base-year mapped")
    check(doc["emissionIntensity"]["value"] == 12.4, "intensity mapped")
    check(doc["verification"]["standardRef"] == "ISO 14064-3", "verification passthrough")


def test_45v(tmp: Path) -> None:
    print("IRA 45V converter (full) — statutory tier logic:")
    # Tier boundaries from 26 USC 45V(b).
    check(h45v.classify_45v_tier(0.40)["creditValue"] == 3.00, "CI 0.40 -> $3.00/kg (Tier 1)")
    check(h45v.classify_45v_tier(0.45)["creditFraction"] == 0.334, "CI 0.45 -> 33.4% (Tier 2)")
    check(h45v.classify_45v_tier(2.0)["creditFraction"] == 0.25, "CI 2.0 -> 25% (Tier 3)")
    check(h45v.classify_45v_tier(3.0)["creditFraction"] == 0.20, "CI 3.0 -> 20% (Tier 4)")
    check(h45v.classify_45v_tier(4.0)["eligible"] is True, "CI 4.0 -> eligible (inclusive bound)")
    check(h45v.classify_45v_tier(4.5)["eligible"] is False, "CI 4.5 -> not eligible")

    att = {"orgName": "H2 Producer", "lifecycleCarbonIntensity": 0.4,
           "productionVolumeKg": 1_000_000,
           "verification": {"verifierName": "ERM CVS", "standardRef": "45VH2-GREET"}}
    doc = h45v.convert_45v_to_comet(_write(tmp, "att.json", att))
    check(doc["carbonIntensity"]["value"] == 0.4, "carbonIntensity mapped")
    check(doc["creditTier"]["creditValue"] == 3.00, "credit tier value computed")
    check(doc["creditTier"]["estimatedCreditUSD"] == 3_000_000.0, "estimated credit = vol x value")


def test_scaffolds(tmp: Path) -> None:
    print("Scaffold converters (skeleton JSON path returns a doc):")
    epd_doc = epd.convert_epd_to_comet(
        _write(tmp, "epd.json", {"productName": "Cement CEM I", "gwpTotal": 0.83,
                                 "declaredUnit": "1 kg"}))
    check(epd_doc["@type"] == "comet-pcf:EPDDeclaration", "EPD skeleton @type")
    check(epd_doc["productCarbonFootprint"]["totalGWP"] == 0.83, "EPD gwpTotal mapped")

    corsia_doc = corsia.convert_corsia_to_comet(
        _write(tmp, "corsia.json", {"serialNumber": "CORSIA-001", "vintageYear": 2024}))
    check(corsia_doc["@type"] == "comet-eac:CORSIAEligibleUnit", "CORSIA skeleton @type")
    check(corsia_doc["serialNumber"] == "CORSIA-001", "CORSIA serial mapped")

    verra_doc = verra.convert_verra_to_comet(
        _write(tmp, "verra.json", {"registry": "vcs", "serialNumber": "VCS-123",
                                   "unitType": "Reduction"}))
    check(verra_doc["registry"] == "Verra VCS", "Verra registry normalised")
    check(verra_doc["unitType"] == "Reduction", "Verra unitType mapped")


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        test_ghgprotocol(tmp)
        test_45v(tmp)
        test_scaffolds(tmp)
    print()
    if _fails:
        print(f"RESULT: {_fails} check(s) FAILED")
        return 1
    print("RESULT: all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
