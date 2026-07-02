#!/usr/bin/env python3
"""Plain-assert test suite for the shared registry, extension TTL, and validator.
Run: python test/test_registry.py   (exit 0 = pass)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from validate_curies import load_registry, validate_curies, class_base  # noqa: E402

FAILS: list[str] = []


def check(name: str, cond: bool) -> None:
    print(("PASS" if cond else "FAIL") + f"  {name}")
    if not cond:
        FAILS.append(name)


def main() -> int:
    reg_path = ROOT / "registry" / "comet-curies.json"
    check("registry file exists", reg_path.exists())
    reg = json.loads(reg_path.read_text())

    allow = load_registry(reg_path)
    check("registry non-trivial (>200 CURIEs)", len(allow) > 200)
    # total must equal the sum of all known parts (published + all *_pending lists)
    pending_total = sum(
        v for k, v in reg["counts"].items()
        if k.endswith("_pending") and isinstance(v, int)
    )
    check("counts internally consistent",
          reg["counts"]["total"] == reg["counts"]["comet_published"] + pending_total)

    # Every pending comet-pcr CURIE must actually be defined in the TTL.
    ttl = (ROOT / "extensions" / "comet-pcr.ttl").read_text()
    for curie in reg["comet_pcr_pending"]:
        check(f"comet-pcr term defined in TTL: {curie}", f"{curie} " in ttl or f"{curie}\n" in ttl)

    # Every pending comet-pj CURIE must be defined in the ext/pcr-japan TTL.
    pj_ttl = (ROOT / "ext" / "pcr-japan" / "comet-ext-pcr-japan.ttl").read_text()
    for curie in reg.get("comet_pj_pending", []):
        check(f"comet-pj term defined in TTL: {curie}", f"{curie} " in pj_ttl or f"{curie}\n" in pj_ttl)

    # Keystone + headline terms present.
    for must in ["comet-pcr:PCRDocument", "comet-pcr:governedByPCR",
                 "comet-pcr:CutOffRule", "comet-pcr:DeclaredModule"]:
        check(f"registry contains {must}", must in allow)

    # Validator: good terms pass.
    good = validate_curies(["comet:Process", "comet-pcf:FunctionalUnit",
                            "comet-pcr:PCRDocument", "comet-ef:EmissionFactor.efValue"], allow)
    check("known-good CURIEs all valid", good["invalid"] == [])

    # Validator catches the three real pcrbase bugs.
    bugs = validate_curies(["comet-core:GeographyScope", "comet:FunctionalUnit",
                            "comet-pcf:biogenicCarbon"], allow)
    check("pcrbase bug comet-core:GeographyScope flagged", "comet-core:GeographyScope" in bugs["invalid"])
    check("pcrbase bug comet:FunctionalUnit flagged", "comet:FunctionalUnit" in bugs["invalid"])
    check("pcrbase bug comet-pcf:biogenicCarbon flagged", "comet-pcf:biogenicCarbon" in bugs["invalid"])

    # The corrected forms are valid.
    fixed = validate_curies(["comet-ef:GeographyScope", "comet-pcf:FunctionalUnit",
                             "comet-pcf:BiogenicCarbon"], allow)
    check("corrected CURIEs all valid", fixed["invalid"] == [])

    # property-base leniency
    check("class_base strips property", class_base("comet-pcf:FunctionalUnit.referenceFlow") == "comet-pcf:FunctionalUnit")

    # None ignored.
    check("None entries ignored", validate_curies([None, "comet:Process"], allow)["valid"] == ["comet:Process"])

    print(f"\n{'ALL PASS' if not FAILS else str(len(FAILS)) + ' FAILED: ' + ', '.join(FAILS)}")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    raise SystemExit(main())
