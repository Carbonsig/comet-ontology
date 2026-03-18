"""COMET → CSV converter.

Flatten one or more COMET JSON-LD files into a spreadsheet-friendly CSV
with COMET-aligned column headers matching the PCF or EAC templates.

Usage:
    python comet_to_csv.py input.comet.json
    python comet_to_csv.py input.comet.json --output footprints.csv
    python comet_to_csv.py ./data/ --type pcf --descriptions

Reads a single COMET JSON-LD file, an array within a file, or every
.json / .comet.json file in a directory. Outputs one CSV row per object.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from pathlib import Path
from typing import Any, Optional, Sequence


# ---------------------------------------------------------------------------
# Column definitions — order matches the COMET CSV templates from the spec
# ---------------------------------------------------------------------------

PCF_COLUMNS: list[str] = [
    "org_name",
    "org_id",
    "product_name",
    "product_id",
    "cpc_code",
    "declared_unit",
    "amount",
    "fossil_gwp",
    "total_gwp",
    "biogenic_carbon",
    "land_use_change",
    "biogenic_uptake",
    "aircraft_emissions",
    "packaging_emissions",
    "exempted_percent",
    "boundary_description",
    "period_start",
    "period_end",
    "country",
    "region",
    "primary_data_share",
    "dqi_coverage",
    "dqi_technology",
    "dqi_temporality",
    "dqi_geography",
    "dqi_reliability",
    "standard_ref",
    "pcr_name",
    "allocation_description",
    "has_assurance",
    "assurance_level",
    "verifier_name",
    "verification_date",
]

PCF_DESCRIPTIONS: dict[str, str] = {
    "org_name": "Organization name",
    "org_id": "Organization identifier (LEI, DUNS, etc.)",
    "product_name": "Product / material description",
    "product_id": "Product identifier (GTIN, etc.)",
    "cpc_code": "UN CPC product category code",
    "declared_unit": "Functional unit (kilogram, litre, etc.)",
    "amount": "Unitary product amount",
    "fossil_gwp": "Fossil GWP (kgCO2e per declared unit)",
    "total_gwp": "Total GWP incl. biogenic (kgCO2e per declared unit)",
    "biogenic_carbon": "Biogenic carbon content (kgCO2e)",
    "land_use_change": "Direct land use change emissions (kgCO2e)",
    "biogenic_uptake": "Biogenic carbon withdrawal (kgCO2e)",
    "aircraft_emissions": "Aircraft GHG emissions (kgCO2e)",
    "packaging_emissions": "Packaging GHG emissions (kgCO2e)",
    "exempted_percent": "Exempted emissions (0-100%)",
    "boundary_description": "System boundary description",
    "period_start": "Reference period start (ISO date)",
    "period_end": "Reference period end (ISO date)",
    "country": "Site country (ISO 3166-2)",
    "region": "Geographic region or subregion",
    "primary_data_share": "Primary data share (0-100%)",
    "dqi_coverage": "DQI coverage percent",
    "dqi_technology": "DQI technology rating (1-3)",
    "dqi_temporality": "DQI temporal rating (1-3)",
    "dqi_geography": "DQI geographic rating (1-3)",
    "dqi_reliability": "DQI reliability/completeness rating (1-3)",
    "standard_ref": "Standards used (semicolon-separated)",
    "pcr_name": "Product category rule name",
    "allocation_description": "Allocation rules description",
    "has_assurance": "Has third-party assurance (TRUE/FALSE)",
    "assurance_level": "Assurance level (limited/reasonable)",
    "verifier_name": "Verification body name",
    "verification_date": "Verification completion date",
}

EAC_COLUMNS: list[str] = [
    "eac_type",
    "sub_type",
    "registry_name",
    "registry_id",
    "project_name",
    "project_id",
    "project_type",
    "country",
    "methodology",
    "vintage_start",
    "vintage_end",
    "quantity",
    "unit",
    "status",
    "verifier_name",
    "verification_date",
    "verification_standard",
]

EAC_DESCRIPTIONS: dict[str, str] = {
    "eac_type": "Certificate type (EnergyAttributeCertificate, CarbonRemovalCertificate, etc.)",
    "sub_type": "Sub-type (IREC, GuaranteeOfOrigin, DACCredit, VCU, etc.)",
    "registry_name": "Registry name (Verra, Gold Standard, etc.)",
    "registry_id": "Registry identifier",
    "project_name": "Project name",
    "project_id": "Project identifier",
    "project_type": "Project type classification",
    "country": "Project country (ISO 3166-2)",
    "methodology": "Methodology reference",
    "vintage_start": "Vintage start date",
    "vintage_end": "Vintage end date",
    "quantity": "Number of units/credits",
    "unit": "Unit of measurement (tCO2e, MWh, kg)",
    "status": "Status (issued, active, retired, cancelled)",
    "verifier_name": "Verification body name",
    "verification_date": "Verification date",
    "verification_standard": "Verification standard reference",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Walk nested dicts and return the first non-None value."""
    for key in keys:
        parts = key.split(".")
        obj: Any = data
        for part in parts:
            if isinstance(obj, dict):
                obj = obj.get(part)
            else:
                obj = None
                break
        if obj is not None:
            return obj
    return default


def _to_str(value: Any) -> str:
    """Convert a value to its CSV string representation."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, list):
        return ";".join(str(v) for v in value)
    return str(value)


def _detect_type(comet: dict[str, Any]) -> str:
    """Auto-detect COMET document type from @type field.

    Returns 'pcf' or 'eac'.
    """
    doc_type = comet.get("@type", "")
    if isinstance(doc_type, list):
        doc_type = " ".join(doc_type)
    doc_type_lower = doc_type.lower()

    eac_indicators = (
        "eac",
        "certificate",
        "carbonremoval",
        "energyattribute",
        "carbonavoidance",
        "materialstewardship",
    )
    if any(ind in doc_type_lower for ind in eac_indicators):
        return "eac"

    # Check for EAC-specific fields
    if "eacId" in comet or "eacType" in comet or "registry" in comet:
        return "eac"

    return "pcf"


# ---------------------------------------------------------------------------
# Flattening logic
# ---------------------------------------------------------------------------


def _flatten_pcf(comet: dict[str, Any]) -> dict[str, str]:
    """Flatten a COMET PCF JSON-LD object into a CSV row dict."""
    row: dict[str, str] = {}

    # Organization
    row["org_name"] = _to_str(_get(comet, "organization.orgName"))
    org_id = _get(comet, "organization.orgId")
    row["org_id"] = _to_str(org_id)

    # Material / product
    row["product_name"] = _to_str(_get(comet, "material.materialName", "productDescription"))
    mat_id = _get(comet, "material.materialId", "productIds")
    row["product_id"] = _to_str(mat_id)
    row["cpc_code"] = _to_str(_get(comet, "material.cpcCode", "productCategoryCpc"))

    # Core PCF fields
    row["declared_unit"] = _to_str(_get(comet, "declaredUnit"))
    row["amount"] = _to_str(_get(comet, "unitaryProductAmount"))
    row["fossil_gwp"] = _to_str(_get(comet, "fossilGWP"))
    row["total_gwp"] = _to_str(_get(comet, "totalGWP"))

    # Biogenic
    row["biogenic_carbon"] = _to_str(
        _get(comet, "biogenicCarbonContent", "biogenicCarbon.biogenicCarbonContent")
    )
    row["land_use_change"] = _to_str(
        _get(comet, "landUseChange", "biogenicCarbon.landUseChange")
    )
    row["biogenic_uptake"] = _to_str(
        _get(comet, "biogenicUptake", "biogenicCarbon.biogenicUptake")
    )

    # Transport / packaging
    row["aircraft_emissions"] = _to_str(_get(comet, "aircraftEmissions"))
    row["packaging_emissions"] = _to_str(_get(comet, "packagingEmissions"))

    # Exempted
    row["exempted_percent"] = _to_str(_get(comet, "exemptedPercent"))

    # Boundary
    row["boundary_description"] = _to_str(_get(comet, "boundaryDescription"))

    # Reference period
    row["period_start"] = _to_str(
        _get(comet, "referencePeriod.startDate", "reportingPeriod.startDate")
    )
    row["period_end"] = _to_str(
        _get(comet, "referencePeriod.endDate", "reportingPeriod.endDate")
    )

    # Geography
    row["country"] = _to_str(
        _get(comet, "site.siteCountry", "organization.country")
    )
    row["region"] = _to_str(_get(comet, "site.region"))

    # Primary data share
    row["primary_data_share"] = _to_str(_get(comet, "primaryDataShare"))

    # DQI
    dqi = comet.get("dqi", comet.get("dataQuality", {}))
    row["dqi_coverage"] = _to_str(
        _get(dqi, "coveragePercent", "coverageDQI") if dqi else None
    )
    row["dqi_technology"] = _to_str(
        _get(dqi, "technologyDQI", "technologicalDQR") if dqi else None
    )
    row["dqi_temporality"] = _to_str(
        _get(dqi, "temporalityDQI", "temporalDQR") if dqi else None
    )
    row["dqi_geography"] = _to_str(
        _get(dqi, "geographyDQI", "geographicalDQR") if dqi else None
    )
    row["dqi_reliability"] = _to_str(
        _get(dqi, "reliabilityDQI", "completenessDQR") if dqi else None
    )

    # Standards
    row["standard_ref"] = _to_str(_get(comet, "standardRef", "standardName"))
    row["pcr_name"] = _to_str(_get(comet, "pcrName"))
    row["allocation_description"] = _to_str(_get(comet, "allocationDescription"))

    # Verification
    ver = comet.get("verification", comet.get("assurance", {}))
    row["has_assurance"] = _to_str(
        _get(ver, "hasAssurance") if ver else None
    )
    row["assurance_level"] = _to_str(
        _get(ver, "levelType", "level") if ver else None
    )
    row["verifier_name"] = _to_str(
        _get(ver, "verifierName", "providerName") if ver else None
    )
    row["verification_date"] = _to_str(
        _get(ver, "verificationDate", "completedAt") if ver else None
    )

    return row


def _flatten_eac(comet: dict[str, Any]) -> dict[str, str]:
    """Flatten a COMET EAC JSON-LD object into a CSV row dict."""
    row: dict[str, str] = {}

    row["eac_type"] = _to_str(_get(comet, "eacType", "@type"))
    row["sub_type"] = _to_str(_get(comet, "subType"))

    # Registry
    row["registry_name"] = _to_str(_get(comet, "registry.registryName"))
    row["registry_id"] = _to_str(_get(comet, "registry.registryId"))

    # Project
    row["project_name"] = _to_str(_get(comet, "project.projectName"))
    row["project_id"] = _to_str(_get(comet, "project.projectId"))
    row["project_type"] = _to_str(_get(comet, "project.projectType"))
    row["country"] = _to_str(_get(comet, "project.country", "site.siteCountry"))
    row["methodology"] = _to_str(_get(comet, "project.methodology"))

    # Vintage
    row["vintage_start"] = _to_str(_get(comet, "vintage.startDate"))
    row["vintage_end"] = _to_str(_get(comet, "vintage.endDate"))

    # Quantity
    row["quantity"] = _to_str(_get(comet, "quantity", "unitCount"))
    row["unit"] = _to_str(_get(comet, "unit", default="tCO2e"))
    row["status"] = _to_str(_get(comet, "status", "unitStatus"))

    # Verification
    ver = comet.get("verification", {})
    row["verifier_name"] = _to_str(
        _get(ver, "verifierName") if ver else None
    )
    row["verification_date"] = _to_str(
        _get(ver, "verificationDate") if ver else None
    )
    row["verification_standard"] = _to_str(
        _get(ver, "standardRef") if ver else None
    )

    return row


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def comet_to_csv(
    objects: Sequence[dict[str, Any]],
    *,
    force_type: Optional[str] = None,
    include_descriptions: bool = False,
) -> str:
    """Convert a sequence of COMET JSON-LD dicts to a CSV string.

    Parameters
    ----------
    objects : Sequence[dict]
        One or more parsed COMET JSON-LD documents.
    force_type : str, optional
        Force output type: 'pcf' or 'eac'. Auto-detected if None.
    include_descriptions : bool
        If True, add a comment row (#) with field descriptions.

    Returns
    -------
    str
        CSV content as a string.
    """
    if not objects:
        return ""

    # Determine type from first object or forced flag
    if force_type:
        doc_type = force_type.lower()
    else:
        doc_type = _detect_type(objects[0])

    if doc_type == "eac":
        columns = EAC_COLUMNS
        descriptions = EAC_DESCRIPTIONS
        flatten_fn = _flatten_eac
    else:
        columns = PCF_COLUMNS
        descriptions = PCF_DESCRIPTIONS
        flatten_fn = _flatten_pcf

    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=columns,
        extrasaction="ignore",
        lineterminator="\n",
    )

    # Optional description row
    if include_descriptions:
        desc_row = {col: f"# {descriptions.get(col, '')}" for col in columns}
        writer.writerow(desc_row)

    writer.writeheader()

    for obj in objects:
        row = flatten_fn(obj)
        writer.writerow(row)

    return output.getvalue()


# ---------------------------------------------------------------------------
# File loading
# ---------------------------------------------------------------------------


def _load_objects(input_path: Path) -> list[dict[str, Any]]:
    """Load COMET JSON-LD objects from a file or directory.

    Returns a flat list of dicts.
    """
    objects: list[dict[str, Any]] = []

    if input_path.is_dir():
        json_files = sorted(
            p for p in input_path.iterdir()
            if p.suffix == ".json" and p.is_file()
        )
        if not json_files:
            raise FileNotFoundError(
                f"No .json files found in directory: {input_path}"
            )
        for fp in json_files:
            with open(fp, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                objects.extend(data)
            else:
                objects.append(data)
    else:
        with open(input_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            objects.extend(data)
        else:
            objects.append(data)

    return objects


def convert_file(
    input_path: Path,
    *,
    force_type: Optional[str] = None,
    include_descriptions: bool = False,
) -> str:
    """Read COMET JSON-LD and return CSV string.

    Parameters
    ----------
    input_path : Path
        Path to a COMET JSON-LD file or directory of files.
    force_type : str, optional
        Force output type: 'pcf' or 'eac'.
    include_descriptions : bool
        Include a descriptions comment row.

    Returns
    -------
    str
        CSV content.
    """
    objects = _load_objects(input_path)
    return comet_to_csv(
        objects,
        force_type=force_type,
        include_descriptions=include_descriptions,
    )


# ---------------------------------------------------------------------------
# CLI bridge
# ---------------------------------------------------------------------------


def export(input_path: str) -> str:
    """Bridge for comet_cli.py: export a COMET file to CSV."""
    return convert_file(Path(input_path))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point.

    Returns
    -------
    int
        Exit code: 0 on success, 1 on error.
    """
    parser = argparse.ArgumentParser(
        prog="comet_to_csv",
        description="Flatten COMET JSON-LD to CSV.",
        epilog=(
            "Example: python comet_to_csv.py ./data/ --type pcf "
            "--descriptions --output footprints.csv"
        ),
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to a COMET JSON-LD file or directory of files",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output CSV file path (default: stdout)",
    )
    parser.add_argument(
        "--type", "-t",
        dest="force_type",
        choices=["pcf", "eac"],
        default=None,
        help="Force output type (auto-detected by default)",
    )
    parser.add_argument(
        "--descriptions",
        action="store_true",
        default=False,
        help="Include a comment row with field descriptions",
    )

    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"Error: input path not found: {args.input}", file=sys.stderr)
        return 1

    try:
        result_csv = convert_file(
            args.input,
            force_type=args.force_type,
            include_descriptions=args.descriptions,
        )
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON: {exc}", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error converting: {exc}", file=sys.stderr)
        return 1

    if not result_csv.strip():
        print("Warning: no data found to convert.", file=sys.stderr)
        return 1

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result_csv, encoding="utf-8")
        print(f"Wrote CSV to {args.output}", file=sys.stderr)
    else:
        print(result_csv, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
