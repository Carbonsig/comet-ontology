#!/usr/bin/env python3
"""Convert a CSV file with COMET-aligned columns into COMET JSON-LD.

Each row in the CSV produces one ProductCarbonFootprint JSON-LD document.
Column names are fuzzy-matched to COMET field names so that minor variations
(capitalisation, whitespace, common synonyms) are handled automatically.

Usage:
    python csv_to_comet.py input.csv
    python csv_to_comet.py input.csv --output /tmp/out --batch
    python csv_to_comet.py input.csv --output combined.json

As a library:
    from csv_to_comet import convert_csv_to_comet
    documents = convert_csv_to_comet("data.csv")
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import uuid
from pathlib import Path
from typing import Any

# ── COMET context URI ────────────────────────────────────────────────
COMET_CONTEXT = "https://comet.carbon/v1/jsonld/context.json"
COMET_TYPE = "comet-pcf:ProductCarbonFootprint"

# ── Canonical COMET column names (from TOOLS_SPEC.md §B1 / §D1) ─────
CANONICAL_COLUMNS: list[str] = [
    "org_name", "org_id", "product_name", "product_id", "cpc_code",
    "declared_unit", "amount", "fossil_gwp", "total_gwp",
    "biogenic_carbon", "land_use_change", "biogenic_uptake",
    "aircraft_emissions", "packaging_emissions", "exempted_percent",
    "boundary_description", "period_start", "period_end",
    "country", "region", "primary_data_share",
    "dqi_coverage", "dqi_technology", "dqi_temporality",
    "dqi_geography", "dqi_reliability",
    "standard_ref", "pcr_name", "allocation_description",
    "has_assurance", "assurance_level", "verifier_name", "verification_date",
]

# ── Alias map: common variants → canonical name ─────────────────────
_ALIASES: dict[str, str] = {
    # organisation
    "company": "org_name",
    "company_name": "org_name",
    "companyname": "org_name",
    "organisation": "org_name",
    "organization": "org_name",
    "organisation_name": "org_name",
    "organization_name": "org_name",
    "orgname": "org_name",
    "org_name": "org_name",
    "company_id": "org_id",
    "companyid": "org_id",
    "orgid": "org_id",
    "org_id": "org_id",
    # product / material
    "product": "product_name",
    "productname": "product_name",
    "product_name": "product_name",
    "material": "product_name",
    "material_name": "product_name",
    "materialname": "product_name",
    "productid": "product_id",
    "product_id": "product_id",
    "materialid": "product_id",
    "material_id": "product_id",
    "cpc": "cpc_code",
    "cpccode": "cpc_code",
    "cpc_code": "cpc_code",
    # unit / amount
    "declared_unit": "declared_unit",
    "declaredunit": "declared_unit",
    "unit": "declared_unit",
    "amount": "amount",
    "unitaryproductamount": "amount",
    "unitary_product_amount": "amount",
    "quantity": "amount",
    # emissions
    "fossil_gwp": "fossil_gwp",
    "fossilgwp": "fossil_gwp",
    "pcf_excluding_biogenic": "fossil_gwp",
    "pcfexcludingbiogenic": "fossil_gwp",
    "total_gwp": "total_gwp",
    "totalgwp": "total_gwp",
    "pcf_including_biogenic": "total_gwp",
    "pcfincludingbiogenic": "total_gwp",
    "biogenic_carbon": "biogenic_carbon",
    "biogeniccarboncontent": "biogenic_carbon",
    "biogenic_carbon_content": "biogenic_carbon",
    "land_use_change": "land_use_change",
    "landusechange": "land_use_change",
    "dluc": "land_use_change",
    "biogenic_uptake": "biogenic_uptake",
    "biogenicuptake": "biogenic_uptake",
    "biogenic_withdrawal": "biogenic_uptake",
    "aircraft_emissions": "aircraft_emissions",
    "aircraftemissions": "aircraft_emissions",
    "packaging_emissions": "packaging_emissions",
    "packagingemissions": "packaging_emissions",
    "exempted_percent": "exempted_percent",
    "exemptedpercent": "exempted_percent",
    "exempted_emissions_percent": "exempted_percent",
    # boundary
    "boundary_description": "boundary_description",
    "boundarydescription": "boundary_description",
    "boundary": "boundary_description",
    # period
    "period_start": "period_start",
    "periodstart": "period_start",
    "start_date": "period_start",
    "startdate": "period_start",
    "reference_period_start": "period_start",
    "period_end": "period_end",
    "periodend": "period_end",
    "end_date": "period_end",
    "enddate": "period_end",
    "reference_period_end": "period_end",
    # geography
    "country": "country",
    "site_country": "country",
    "sitecountry": "country",
    "geography_country": "country",
    "region": "region",
    "site_region": "region",
    "geography_region": "region",
    # data quality
    "primary_data_share": "primary_data_share",
    "primarydatashare": "primary_data_share",
    "dqi_coverage": "dqi_coverage",
    "dqicoverage": "dqi_coverage",
    "coverage_percent": "dqi_coverage",
    "dqi_technology": "dqi_technology",
    "dqitechnology": "dqi_technology",
    "technological_dqr": "dqi_technology",
    "dqi_temporality": "dqi_temporality",
    "dqitemporality": "dqi_temporality",
    "temporal_dqr": "dqi_temporality",
    "dqi_geography": "dqi_geography",
    "dqigeography": "dqi_geography",
    "geographical_dqr": "dqi_geography",
    "dqi_reliability": "dqi_reliability",
    "dqireliability": "dqi_reliability",
    "completeness_dqr": "dqi_reliability",
    # standards
    "standard_ref": "standard_ref",
    "standardref": "standard_ref",
    "standards": "standard_ref",
    "pcr_name": "pcr_name",
    "pcrname": "pcr_name",
    "allocation_description": "allocation_description",
    "allocationdescription": "allocation_description",
    "allocation": "allocation_description",
    # verification
    "has_assurance": "has_assurance",
    "hasassurance": "has_assurance",
    "assurance": "has_assurance",
    "assurance_level": "assurance_level",
    "assurancelevel": "assurance_level",
    "level_type": "assurance_level",
    "verifier_name": "verifier_name",
    "verifiername": "verifier_name",
    "verifier": "verifier_name",
    "verification_date": "verification_date",
    "verificationdate": "verification_date",
}

# ── Declared-unit normalisation ─────────────────────────────────────
_UNIT_NORMALISE: dict[str, str] = {
    "kg": "kilogram",
    "kilogram": "kilogram",
    "kilograms": "kilogram",
    "t": "kilogram",       # keep in tonnes mapping below
    "tonne": "kilogram",   # override below
    "l": "liter",
    "litre": "liter",
    "liter": "liter",
    "litres": "liter",
    "liters": "liter",
    "m3": "cubic meter",
    "cubic meter": "cubic meter",
    "cubic metre": "cubic meter",
    "cubicmetre": "cubic meter",
    "cubicmeter": "cubic meter",
    "kwh": "kilowatt hour",
    "kilowatt hour": "kilowatt hour",
    "kilowatthour": "kilowatt hour",
    "mj": "megajoule",
    "megajoule": "megajoule",
    "tkm": "tonne kilometre",
    "tonne kilometre": "tonne kilometre",
    "tonnekilometre": "tonne kilometre",
    "tonne kilometer": "tonne kilometre",
    "m2": "square meter",
    "square meter": "square meter",
    "square metre": "square meter",
    "squaremeter": "square meter",
    "squaremetre": "square meter",
}


def _normalise_header(raw: str) -> str | None:
    """Map a raw CSV header to its canonical COMET column name, or None."""
    key = raw.strip().lower().replace(" ", "_").replace("-", "_")
    # direct canonical match
    if key in CANONICAL_COLUMNS:
        return key
    # alias lookup (also strips underscores for camelCase variants)
    no_us = key.replace("_", "")
    return _ALIASES.get(key) or _ALIASES.get(no_us)


def _parse_number(val: str) -> float | None:
    """Try to parse a numeric value; return None on failure."""
    val = val.strip()
    if not val:
        return None
    try:
        return float(val)
    except ValueError:
        return None


def _parse_bool(val: str) -> bool | None:
    """Parse a boolean-ish string."""
    val = val.strip().lower()
    if val in ("true", "yes", "1", "y"):
        return True
    if val in ("false", "no", "0", "n"):
        return False
    if val == "":
        return None
    return None


def _normalise_unit(raw: str) -> str:
    """Normalise a declared-unit string to the COMET enum value."""
    key = raw.strip().lower()
    return _UNIT_NORMALISE.get(key, raw.strip())


def _row_to_comet(mapped: dict[str, str]) -> dict[str, Any]:
    """Convert a single mapped-column dict to a COMET JSON-LD document."""
    doc: dict[str, Any] = {
        "@context": COMET_CONTEXT,
        "@type": COMET_TYPE,
        "pcfId": str(uuid.uuid4()),
    }

    # ── top-level scalars ────────────────────────────────────────────
    unit = mapped.get("declared_unit", "")
    if unit:
        doc["declaredUnit"] = _normalise_unit(unit)

    for csv_col, json_key in [
        ("amount", "unitaryProductAmount"),
        ("fossil_gwp", "fossilGWP"),
        ("total_gwp", "totalGWP"),
        ("biogenic_carbon", "biogenicCarbonContent"),
        ("land_use_change", "landUseChange"),
        ("biogenic_uptake", "biogenicUptake"),
        ("aircraft_emissions", "aircraftEmissions"),
        ("packaging_emissions", "packagingEmissions"),
        ("exempted_percent", "exemptedPercent"),
        ("primary_data_share", "primaryDataShare"),
    ]:
        num = _parse_number(mapped.get(csv_col, ""))
        if num is not None:
            doc[json_key] = num

    for csv_col, json_key in [
        ("boundary_description", "boundaryDescription"),
    ]:
        val = mapped.get(csv_col, "").strip()
        if val:
            doc[json_key] = val

    # standard_ref — semicolon-separated list
    sr = mapped.get("standard_ref", "").strip()
    if sr:
        doc["standardRef"] = [s.strip() for s in sr.split(";") if s.strip()]

    for csv_col, json_key in [
        ("pcr_name", "pcrName"),
        ("allocation_description", "allocationDescription"),
    ]:
        val = mapped.get(csv_col, "").strip()
        if val:
            doc[json_key] = val

    # ── organization ─────────────────────────────────────────────────
    org: dict[str, Any] = {}
    name = mapped.get("org_name", "").strip()
    if name:
        org["orgName"] = name
    oid = mapped.get("org_id", "").strip()
    if oid:
        org["orgId"] = [s.strip() for s in oid.split(";") if s.strip()]
    if org:
        doc["organization"] = org

    # ── material ─────────────────────────────────────────────────────
    mat: dict[str, Any] = {}
    pn = mapped.get("product_name", "").strip()
    if pn:
        mat["materialName"] = pn
    pid = mapped.get("product_id", "").strip()
    if pid:
        mat["materialId"] = [s.strip() for s in pid.split(";") if s.strip()]
    cpc = mapped.get("cpc_code", "").strip()
    if cpc:
        mat["cpcCode"] = cpc
    if mat:
        doc["material"] = mat

    # ── site ─────────────────────────────────────────────────────────
    site: dict[str, Any] = {}
    country = mapped.get("country", "").strip()
    if country:
        site["siteCountry"] = country.upper()
    region = mapped.get("region", "").strip()
    if region:
        site["region"] = region
    if site:
        doc["site"] = site

    # ── referencePeriod ──────────────────────────────────────────────
    rp: dict[str, Any] = {}
    ps = mapped.get("period_start", "").strip()
    if ps:
        rp["startDate"] = ps
    pe = mapped.get("period_end", "").strip()
    if pe:
        rp["endDate"] = pe
    if rp:
        doc["referencePeriod"] = rp

    # ── dqi ──────────────────────────────────────────────────────────
    dqi: dict[str, Any] = {}
    for csv_col, json_key in [
        ("dqi_coverage", "coveragePercent"),
        ("dqi_technology", "technologyDQI"),
        ("dqi_temporality", "temporalityDQI"),
        ("dqi_geography", "geographyDQI"),
        ("dqi_reliability", "reliabilityDQI"),
    ]:
        num = _parse_number(mapped.get(csv_col, ""))
        if num is not None:
            dqi[json_key] = num
    if dqi:
        doc["dqi"] = dqi

    # ── verification ─────────────────────────────────────────────────
    ver: dict[str, Any] = {}
    ha = _parse_bool(mapped.get("has_assurance", ""))
    if ha is not None:
        ver["hasAssurance"] = ha
    al = mapped.get("assurance_level", "").strip().lower()
    if al in ("limited", "reasonable"):
        ver["levelType"] = al
    vn = mapped.get("verifier_name", "").strip()
    if vn:
        ver["verifierName"] = vn
    vd = mapped.get("verification_date", "").strip()
    if vd:
        ver["verificationDate"] = vd
    if ver:
        doc["verification"] = ver

    return doc


def _validate_doc(doc: dict[str, Any], row_num: int) -> list[str]:
    """Run lightweight validation on a COMET document.  Returns a list of warnings."""
    warnings: list[str] = []
    if "fossilGWP" not in doc:
        warnings.append(f"Row {row_num}: missing required field 'fossil_gwp'")
    if "boundaryDescription" not in doc:
        warnings.append(f"Row {row_num}: missing required field 'boundary_description'")
    if "organization" not in doc or "orgName" not in doc.get("organization", {}):
        warnings.append(f"Row {row_num}: missing required field 'org_name'")
    if "referencePeriod" not in doc:
        warnings.append(f"Row {row_num}: missing reference period (period_start/period_end)")
    gwp = doc.get("fossilGWP")
    if gwp is not None and gwp < 0:
        warnings.append(f"Row {row_num}: fossilGWP is negative ({gwp})")
    pds = doc.get("primaryDataShare")
    if pds is not None and not (0 <= pds <= 100):
        warnings.append(f"Row {row_num}: primaryDataShare out of range 0-100 ({pds})")
    return warnings


# ── Public API ───────────────────────────────────────────────────────

def convert_csv_to_comet(
    csv_path: str | Path,
    *,
    strict: bool = False,
) -> list[dict[str, Any]]:
    """Read *csv_path* and return a list of COMET JSON-LD dicts.

    Parameters
    ----------
    csv_path : path to the CSV file
    strict : if True, raise on validation warnings

    Returns
    -------
    list of COMET JSON-LD dicts (one per non-blank row)
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with csv_path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            raise ValueError("CSV file has no header row")

        # Build column mapping: raw header → canonical name
        col_map: dict[str, str] = {}
        unmapped: list[str] = []
        for raw in reader.fieldnames:
            canonical = _normalise_header(raw)
            if canonical:
                col_map[raw] = canonical
            else:
                unmapped.append(raw)

        if unmapped:
            print(
                f"Warning: unmapped columns (ignored): {', '.join(unmapped)}",
                file=sys.stderr,
            )

        documents: list[dict[str, Any]] = []
        all_warnings: list[str] = []

        for row_idx, row in enumerate(reader, start=2):  # row 1 is header
            # Skip completely blank rows
            if all(not v.strip() for v in row.values()):
                continue

            mapped = {col_map[k]: v for k, v in row.items() if k in col_map}
            doc = _row_to_comet(mapped)
            warnings = _validate_doc(doc, row_idx)
            all_warnings.extend(warnings)
            documents.append(doc)

        if all_warnings:
            for w in all_warnings:
                print(f"Warning: {w}", file=sys.stderr)
            if strict:
                raise ValueError(
                    f"Validation failed with {len(all_warnings)} warning(s)"
                )

    return documents


# ── CLI bridge ────────────────────────────────────────────────────────

def convert(input_path: str) -> list[dict[str, Any]]:
    """Bridge for comet_cli.py: convert an input file to COMET JSON-LD."""
    return convert_csv_to_comet(input_path)


# ── CLI ──────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert a CSV file to COMET JSON-LD.",
        epilog=(
            "Examples:\n"
            "  python csv_to_comet.py pcf_data.csv\n"
            "  python csv_to_comet.py pcf_data.csv --output /tmp/out --batch\n"
            "  python csv_to_comet.py pcf_data.csv --output combined.json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", type=Path, help="Path to the input CSV file")
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output file or directory (default: stdout)",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Write one file per row into --output directory instead of a single array",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with error if any validation warnings occur",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        docs = convert_csv_to_comet(args.input, strict=args.strict)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not docs:
        print("Warning: no data rows found in CSV", file=sys.stderr)
        return 0

    if args.batch and args.output:
        # Write individual files
        outdir = args.output
        outdir.mkdir(parents=True, exist_ok=True)
        for i, doc in enumerate(docs, start=1):
            outfile = outdir / f"pcf_{i:04d}.comet.json"
            outfile.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
        print(f"Wrote {len(docs)} file(s) to {outdir}", file=sys.stderr)
    elif args.output:
        # Write combined array to single file
        args.output.parent.mkdir(parents=True, exist_ok=True)
        output = docs if len(docs) > 1 else docs[0]
        args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        # stdout
        output = docs if len(docs) > 1 else docs[0]
        print(json.dumps(output, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
