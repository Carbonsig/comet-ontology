#!/usr/bin/env python3
"""Convert CAD Trust v2.0.2 registry data into COMET JSON-LD.

Accepts individual CSV files (one per CAD Trust table) or a combined JSON
export.  Related tables are joined on foreign keys, and output is
denormalised into COMET EAC documents.

Usage:
    python cad_trust_to_comet.py project.csv
    python cad_trust_to_comet.py project.csv --units units.csv --verification ver.csv
    python cad_trust_to_comet.py combined_export.json --output credits.json

As a library:
    from cad_trust_to_comet import convert_cad_trust_to_comet
    documents = convert_cad_trust_to_comet("project.csv")
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import uuid
from pathlib import Path
from typing import Any

# ── COMET constants ──────────────────────────────────────────────────
COMET_CONTEXT = [
    "https://comet.carbon/v1/jsonld/context.json",
    "https://climateactiondata.org/api/v2/context.json",
]
COMET_TYPE = "comet-eac:EAC"

# ── SDG co-benefit code → name ───────────────────────────────────────
SDG_NAMES: dict[int, str] = {
    1: "SDG 1 - No poverty",
    2: "SDG 2 - Zero hunger",
    3: "SDG 3 - Good health and well-being",
    4: "SDG 4 - Quality education",
    5: "SDG 5 - Gender equality",
    6: "SDG 6 - Clean water and sanitation",
    7: "SDG 7 - Affordable and clean energy",
    8: "SDG 8 - Decent work and economic growth",
    9: "SDG 9 - Industry, innovation and infrastructure",
    10: "SDG 10 - Reduced inequalities",
    11: "SDG 11 - Sustainable cities and communities",
    12: "SDG 12 - Responsible consumption and production",
    13: "SDG 13 - Climate action",
    14: "SDG 14 - Life below water",
    15: "SDG 15 - Life on land",
    16: "SDG 16 - Peace, justice and strong institutions",
    17: "SDG 17 - Partnerships for the goals",
}

# ── CAD Trust status → COMET status mapping ──────────────────────────
_STATUS_MAP: dict[str, str] = {
    "issued": "issued",
    "active": "active",
    "held": "active",
    "retired": "retired",
    "cancelled": "cancelled",
    "pending": "issued",
}

# ── Table auto-detection: canonical column sets per table ────────────
# Each entry: table_name → set of characteristic column names (lowered).
# A CSV is assigned to the table whose characteristic columns best match.
_TABLE_SIGNATURES: dict[str, set[str]] = {
    "project": {
        "project_id", "project_name", "project_type", "country",
        "methodology", "standard", "status", "registry_name",
        "cadtrustprojectid", "projectregistryname", "projectsector",
    },
    "unit": {
        "unit_id", "project_id", "serial_number", "vintage_year",
        "unit_status", "unit_count", "unit_type",
        "unitserialid", "unittype", "unitvintageyear", "unitstatus", "unitcount",
    },
    "issuance": {
        "issuance_id", "project_id", "issuance_date", "quantity", "vintage",
    },
    "retirement": {
        "retirement_id", "unit_id", "retired_date", "retired_by",
        "beneficiary", "purpose", "retirement_date",
        "unitretirementbeneficiary",
    },
    "verification": {
        "verification_id", "project_id", "verifier_name", "verification_date",
        "verification_standard", "verification_status",
        "verificationbody",
    },
    "validation": {
        "validation_id", "project_id", "validation_type", "validation_date",
        "validationtype",
    },
    "label": {
        "label_id", "project_id", "label_name", "label_type",
        "label_version", "criteria",
        "labeltype",
    },
    "co_benefit": {
        "cobenefit_id", "project_id", "benefit_type", "sdg_number",
        "description", "cobenefit",
    },
    "design": {
        "design_id", "project_id", "baseline_scenario", "additionality",
        "leakage",
    },
    "pricing": {
        "pricing_id", "unit_id", "price_per_unit", "currency",
        "transaction_date",
    },
    "rating": {
        "rating_id", "project_id", "rating_agency", "rating_value",
        "rating_date", "ratingtype", "ratingprovider",
    },
    "article6_authorization": {
        "authorization_id", "project_id", "authorizing_country",
        "corresponding_adjustment",
    },
    "article6_itmo": {
        "itmo_id", "project_id", "transferring_country",
        "acquiring_country", "amount",
    },
    "corresponding_adjustment": {
        "adjustment_id", "project_id", "adjustment_type",
        "reporting_period",
    },
    "program": {
        "program_id", "program_name", "programname",
    },
    "estimation": {
        "estimation_id", "estimation_unit_count", "estimationunitcount",
    },
    "aef_t2": {
        "authorization_id", "aef_t2",
    },
    "aef_t3": {
        "transfer_id", "aef_t3",
    },
}


def _detect_table(headers: list[str]) -> str | None:
    """Auto-detect which CAD Trust table a CSV represents from its column headers."""
    normed = {h.strip().lower().replace(" ", "_") for h in headers}
    best_table: str | None = None
    best_score = 0
    for table_name, sig in _TABLE_SIGNATURES.items():
        score = len(normed & sig)
        if score > best_score:
            best_score = score
            best_table = table_name
    return best_table if best_score >= 2 else None


def _normalise_key(raw: str) -> str:
    """Normalise a column header to snake_case."""
    return raw.strip().lower().replace(" ", "_").replace("-", "_")


def _read_csv_table(path: Path) -> tuple[str | None, list[dict[str, str]]]:
    """Read a CSV, detect its table type, and return (table_name, rows)."""
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            return None, []
        table = _detect_table(list(reader.fieldnames))
        rows = []
        for row in reader:
            normed = {_normalise_key(k): v.strip() for k, v in row.items()}
            rows.append(normed)
        return table, rows


def _read_json_tables(path: Path) -> dict[str, list[dict[str, str]]]:
    """Read a combined JSON export.  Expected shape: {table_name: [rows]}."""
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        result: dict[str, list[dict[str, str]]] = {}
        for key, rows in data.items():
            table = key.strip().lower().replace(" ", "_")
            if isinstance(rows, list):
                result[table] = [
                    {_normalise_key(k): str(v).strip() for k, v in r.items()}
                    for r in rows
                    if isinstance(r, dict)
                ]
        return result
    raise ValueError("Combined JSON must be an object with table-name keys")


def _safe_int(val: str) -> int | None:
    try:
        return int(float(val)) if val else None
    except (ValueError, TypeError):
        return None


def _safe_float(val: str) -> float | None:
    try:
        return float(val) if val else None
    except (ValueError, TypeError):
        return None


def _map_status(raw: str) -> str:
    """Map CAD Trust status values to COMET enum."""
    return _STATUS_MAP.get(raw.strip().lower(), raw.strip().lower())


def _sdg_name(code: int | str) -> str:
    """Map an SDG number (1-17) to its full UN name."""
    try:
        n = int(code)
    except (ValueError, TypeError):
        return str(code)
    return SDG_NAMES.get(n, f"SDG {n}")


# ── Core conversion ──────────────────────────────────────────────────

def _build_project(row: dict[str, str]) -> dict[str, Any]:
    """Map a project table row to the COMET project sub-object."""
    proj: dict[str, Any] = {}
    for csv_col, json_key in [
        ("project_name", "projectName"),
        ("project_id", "projectId"),
        ("project_type", "projectType"),
        ("country", "country"),
        ("methodology", "methodology"),
        ("standard", "standard"),
        ("status", "status"),
        ("registry_name", "registryName"),
        ("cadtrustprojectid", "cadTrustProjectId"),
        ("projectregistryname", "registryName"),
        ("projectsector", "sector"),
    ]:
        val = row.get(csv_col, "").strip()
        if val:
            proj[json_key] = val
    # Ensure cadTrustProjectId
    if "cadTrustProjectId" not in proj and "project_id" in row:
        proj["cadTrustProjectId"] = row["project_id"].strip()
    return proj


def _build_unit_doc(
    unit_row: dict[str, str],
    project: dict[str, Any] | None,
    tables: dict[str, list[dict[str, str]]],
) -> dict[str, Any]:
    """Build a full COMET EAC document from a unit row and related tables."""
    doc: dict[str, Any] = {
        "@context": COMET_CONTEXT,
        "@type": COMET_TYPE,
        "eacId": str(uuid.uuid4()),
    }

    # Unit-level fields
    serial = unit_row.get("serial_number") or unit_row.get("unitserialid", "")
    if serial:
        doc["serialNumber"] = serial

    unit_type = unit_row.get("unit_type") or unit_row.get("unittype", "")
    if unit_type:
        doc["unitType"] = unit_type

    vintage = unit_row.get("vintage_year") or unit_row.get("unitvintageyear", "")
    if vintage:
        v = _safe_int(vintage)
        if v is not None:
            doc["vintageYear"] = v

    status = unit_row.get("unit_status") or unit_row.get("unitstatus", "")
    if status:
        doc["status"] = _map_status(status)

    count = unit_row.get("unit_count") or unit_row.get("unitcount", "")
    if count:
        n = _safe_float(count)
        if n is not None:
            doc["quantity"] = n
            doc["unit"] = "tCO2e"

    # CAD Trust traceability
    cad: dict[str, Any] = {}
    pid = unit_row.get("project_id", "")
    uid = unit_row.get("unit_id", "")
    if pid:
        cad["cadTrustProjectId"] = pid
    if uid:
        cad["cadTrustUnitId"] = uid
    if cad:
        doc["cadTrust"] = cad

    # Project
    if project:
        doc["project"] = project

    # Join related tables on project_id and unit_id
    project_id = pid
    unit_id = uid

    # Retirement
    retirements = tables.get("retirement", [])
    for r in retirements:
        if r.get("unit_id") == unit_id or (not unit_id and r.get("project_id") == project_id):
            ret: dict[str, Any] = {}
            for csv_col, json_key in [
                ("retired_date", "retiredDate"),
                ("retirement_date", "retiredDate"),
                ("retired_by", "retiredBy"),
                ("beneficiary", "beneficiary"),
                ("unitretirementbeneficiary", "beneficiary"),
                ("purpose", "purpose"),
            ]:
                val = r.get(csv_col, "").strip()
                if val and json_key not in ret:
                    ret[json_key] = val
            if ret:
                doc["retirementInfo"] = ret
            break

    # Issuance
    issuances = tables.get("issuance", [])
    for iss in issuances:
        if iss.get("project_id") == project_id:
            info: dict[str, Any] = {}
            for csv_col, json_key in [
                ("issuance_date", "issuanceDate"),
                ("quantity", "quantity"),
                ("vintage", "vintage"),
            ]:
                val = iss.get(csv_col, "").strip()
                if val:
                    info[json_key] = val
            if "issuance_id" in iss:
                cad["cadTrustIssuanceId"] = iss["issuance_id"]
            if info:
                doc["issuanceInfo"] = info
            break

    # Verification
    verifications = tables.get("verification", [])
    for v in verifications:
        if v.get("project_id") == project_id:
            ver: dict[str, Any] = {}
            for csv_col, json_key in [
                ("verifier_name", "verifierName"),
                ("verificationbody", "verifierName"),
                ("verification_date", "verificationDate"),
                ("verification_standard", "standard"),
                ("verification_status", "status"),
            ]:
                val = v.get(csv_col, "").strip()
                if val and json_key not in ver:
                    ver[json_key] = val
            if ver:
                doc["verification"] = ver
            break

    # Validation
    validations = tables.get("validation", [])
    for v in validations:
        if v.get("project_id") == project_id:
            vld: dict[str, Any] = {}
            for csv_col, json_key in [
                ("validation_type", "validationType"),
                ("validationtype", "validationType"),
                ("validation_date", "validationDate"),
            ]:
                val = v.get(csv_col, "").strip()
                if val and json_key not in vld:
                    vld[json_key] = val
            if vld:
                doc["validation"] = vld
            break

    # Labels
    labels = tables.get("label", [])
    doc_labels: list[dict[str, Any]] = []
    for lb in labels:
        if lb.get("project_id") == project_id:
            label: dict[str, Any] = {}
            for csv_col, json_key in [
                ("label_name", "labelName"),
                ("label_type", "labelType"),
                ("labeltype", "labelType"),
                ("label_version", "labelVersion"),
                ("criteria", "criteria"),
            ]:
                val = lb.get(csv_col, "").strip()
                if val and json_key not in label:
                    label[json_key] = val
            if label:
                doc_labels.append(label)
    if doc_labels:
        doc["labels"] = doc_labels

    # Co-benefits
    cobenefits = tables.get("co_benefit", [])
    doc_cb: list[dict[str, Any]] = []
    for cb in cobenefits:
        if cb.get("project_id") == project_id:
            benefit: dict[str, Any] = {}
            # SDG number
            sdg_raw = cb.get("sdg_number") or cb.get("benefit_type") or cb.get("cobenefit", "")
            if sdg_raw:
                sdg_int = _safe_int(sdg_raw)
                if sdg_int is not None:
                    benefit["sdgGoal"] = _sdg_name(sdg_int)
                    benefit["sdgNumber"] = sdg_int
                else:
                    benefit["sdgGoal"] = sdg_raw
            desc = cb.get("description", "").strip()
            if desc:
                benefit["description"] = desc
            if benefit:
                doc_cb.append(benefit)
    if doc_cb:
        doc["coBenefits"] = doc_cb

    # Design
    designs = tables.get("design", [])
    for d in designs:
        if d.get("project_id") == project_id:
            design: dict[str, Any] = {}
            for csv_col, json_key in [
                ("baseline_scenario", "baselineScenario"),
                ("additionality", "additionality"),
                ("leakage", "leakage"),
            ]:
                val = d.get(csv_col, "").strip()
                if val:
                    design[json_key] = val
            if design and project:
                doc["project"]["design"] = design
            elif design:
                doc["project"] = {"design": design}
            break

    # Pricing
    pricings = tables.get("pricing", [])
    for p in pricings:
        if p.get("unit_id") == unit_id or (not unit_id and p.get("project_id") == project_id):
            pricing: dict[str, Any] = {}
            ppu = p.get("price_per_unit", "").strip()
            if ppu:
                val = _safe_float(ppu)
                if val is not None:
                    pricing["pricePerUnit"] = val
            cur = p.get("currency", "").strip()
            if cur:
                pricing["currency"] = cur
            td = p.get("transaction_date", "").strip()
            if td:
                pricing["transactionDate"] = td
            if pricing:
                doc["pricing"] = pricing
            break

    # Rating
    ratings = tables.get("rating", [])
    for r in ratings:
        if r.get("project_id") == project_id:
            rating: dict[str, Any] = {}
            for csv_col, json_key in [
                ("rating_agency", "ratingAgency"),
                ("ratingtype", "ratingProvider"),
                ("ratingprovider", "ratingProvider"),
                ("rating_value", "ratingValue"),
                ("rating_date", "ratingDate"),
            ]:
                val = r.get(csv_col, "").strip()
                if val and json_key not in rating:
                    rating[json_key] = val
            if rating:
                doc["rating"] = rating
            break

    # Article 6 authorization
    a6_auths = tables.get("article6_authorization", []) + tables.get("aef_t2", [])
    for a in a6_auths:
        if a.get("project_id") == project_id:
            art6: dict[str, Any] = {}
            for csv_col, json_key in [
                ("authorizing_country", "authorizingCountry"),
                ("corresponding_adjustment", "correspondingAdjustment"),
            ]:
                val = a.get(csv_col, "").strip()
                if val:
                    art6[json_key] = val
            if art6:
                doc["article6"] = art6
            break

    # Article 6 ITMO
    itmos = tables.get("article6_itmo", []) + tables.get("aef_t3", [])
    for it in itmos:
        if it.get("project_id") == project_id:
            itmo: dict[str, Any] = {}
            for csv_col, json_key in [
                ("transferring_country", "transferringCountry"),
                ("acquiring_country", "acquiringCountry"),
                ("amount", "amount"),
            ]:
                val = it.get(csv_col, "").strip()
                if val:
                    if json_key == "amount":
                        n = _safe_float(val)
                        if n is not None:
                            itmo[json_key] = n
                    else:
                        itmo[json_key] = val
            if itmo:
                doc.setdefault("article6", {})["itmo"] = itmo
            break

    # Corresponding adjustment
    adj_rows = tables.get("corresponding_adjustment", [])
    for adj in adj_rows:
        if adj.get("project_id") == project_id:
            adjustment: dict[str, Any] = {}
            for csv_col, json_key in [
                ("adjustment_type", "adjustmentType"),
                ("reporting_period", "reportingPeriod"),
            ]:
                val = adj.get(csv_col, "").strip()
                if val:
                    adjustment[json_key] = val
            if adjustment:
                doc.setdefault("article6", {})["adjustment"] = adjustment
            break

    # Program
    programs = tables.get("program", [])
    for prog in programs:
        pname = prog.get("program_name") or prog.get("programname", "")
        if pname:
            doc.setdefault("registry", {})["programName"] = pname.strip()
            break

    # Estimation
    estimations = tables.get("estimation", [])
    for est in estimations:
        eq = est.get("estimation_unit_count") or est.get("estimationunitcount", "")
        if eq:
            n = _safe_float(eq)
            if n is not None:
                doc["estimatedQuantity"] = n
            break

    return doc


# ── Public API ───────────────────────────────────────────────────────

def convert_cad_trust_to_comet(
    primary_path: str | Path,
    *,
    units_path: str | Path | None = None,
    verification_path: str | Path | None = None,
    extra_csvs: dict[str, str | Path] | None = None,
) -> list[dict[str, Any]]:
    """Convert CAD Trust data to COMET JSON-LD EAC documents.

    Parameters
    ----------
    primary_path : main input file (CSV or JSON)
    units_path : optional path to units CSV
    verification_path : optional path to verification CSV
    extra_csvs : optional dict of {table_name: csv_path} for additional tables

    Returns
    -------
    list of COMET JSON-LD dicts (one per credit unit, or one per project
    if no unit table is provided)
    """
    primary_path = Path(primary_path)
    if not primary_path.exists():
        raise FileNotFoundError(f"File not found: {primary_path}")

    tables: dict[str, list[dict[str, str]]] = {}

    # Load primary file
    if primary_path.suffix.lower() == ".json":
        tables = _read_json_tables(primary_path)
    else:
        table_name, rows = _read_csv_table(primary_path)
        if table_name is None:
            print(
                f"Warning: could not auto-detect table type for {primary_path.name}; "
                "assuming 'project'",
                file=sys.stderr,
            )
            table_name = "project"
        tables[table_name] = rows

    # Load extra CSVs
    if units_path:
        units_path = Path(units_path)
        _, rows = _read_csv_table(units_path)
        tables["unit"] = rows

    if verification_path:
        verification_path = Path(verification_path)
        _, rows = _read_csv_table(verification_path)
        tables["verification"] = rows

    if extra_csvs:
        for tname, cpath in extra_csvs.items():
            cpath = Path(cpath)
            _, rows = _read_csv_table(cpath)
            tables[tname] = rows

    # Build project lookup: project_id → project dict
    projects: dict[str, dict[str, Any]] = {}
    for row in tables.get("project", []):
        pid = row.get("project_id", "").strip()
        if pid:
            projects[pid] = _build_project(row)

    # If we have units, emit one doc per unit; otherwise one per project
    unit_rows = tables.get("unit", [])
    documents: list[dict[str, Any]] = []

    if unit_rows:
        for urow in unit_rows:
            pid = urow.get("project_id", "").strip()
            project = projects.get(pid)
            doc = _build_unit_doc(urow, project, tables)
            documents.append(doc)
    elif projects:
        # One doc per project (no unit detail)
        for pid, proj in projects.items():
            dummy_unit: dict[str, str] = {"project_id": pid}
            doc = _build_unit_doc(dummy_unit, proj, tables)
            documents.append(doc)
    else:
        # Fallback: try to build from whatever tables we have
        # Use first table's rows as pseudo-units
        for tname, rows in tables.items():
            for row in rows:
                pid = row.get("project_id", "").strip()
                project = projects.get(pid) if pid else None
                doc = _build_unit_doc(row, project, tables)
                documents.append(doc)
            break

    return documents


# ── CLI bridge ────────────────────────────────────────────────────────

def convert(input_path: str) -> list[dict[str, Any]]:
    """Bridge for comet_cli.py: convert an input file to COMET JSON-LD."""
    return convert_cad_trust_to_comet(input_path)


# ── CLI ──────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert CAD Trust v2.0.2 data to COMET JSON-LD.",
        epilog=(
            "Examples:\n"
            "  python cad_trust_to_comet.py project.csv\n"
            "  python cad_trust_to_comet.py project.csv --units units.csv --verification ver.csv\n"
            "  python cad_trust_to_comet.py combined.json --output credits.json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Primary input file (CSV for one table, or combined JSON)",
    )
    parser.add_argument(
        "--units",
        type=Path,
        default=None,
        help="Path to units table CSV",
    )
    parser.add_argument(
        "--verification",
        type=Path,
        default=None,
        help="Path to verification table CSV",
    )
    parser.add_argument(
        "--retirement",
        type=Path,
        default=None,
        help="Path to retirement table CSV",
    )
    parser.add_argument(
        "--co-benefits",
        type=Path,
        default=None,
        dest="co_benefits",
        help="Path to co-benefits table CSV",
    )
    parser.add_argument(
        "--labels",
        type=Path,
        default=None,
        help="Path to labels table CSV",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output file (default: stdout)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    extra: dict[str, Path] = {}
    if args.retirement:
        extra["retirement"] = args.retirement
    if args.co_benefits:
        extra["co_benefit"] = args.co_benefits
    if args.labels:
        extra["label"] = args.labels

    try:
        docs = convert_cad_trust_to_comet(
            args.input,
            units_path=args.units,
            verification_path=args.verification,
            extra_csvs=extra if extra else None,
        )
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not docs:
        print("Warning: no data found in input", file=sys.stderr)
        return 0

    output = docs if len(docs) > 1 else docs[0]
    text = json.dumps(output, indent=2, ensure_ascii=False) + "\n"

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
