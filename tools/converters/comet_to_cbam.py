"""COMET → CBAM XML converter.

Generate a CBAM-compliant XML declaration from a COMET JSON-LD file
(either a ProductCarbonFootprint or CBAMDeclaration type).

Usage:
    python comet_to_cbam.py input.comet.json
    python comet_to_cbam.py input.comet.json --output declaration.xml

The output conforms to the DG TAXUD CBAM XML schema with COMET namespace
annotations as documented in docs/data-exchange.html Section 3.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# CN code lookup — map material descriptions / hsCode prefixes to 8-digit CN
# ---------------------------------------------------------------------------

_CN_CODE_KEYWORDS: dict[str, str] = {
    # Steel (CN 7206–7229)
    "steel": "72081000",
    "hot-rolled": "72081000",
    "cold-rolled": "72091500",
    "stainless steel": "72181000",
    "iron": "72061000",
    "pig iron": "72011100",
    "ferro-alloy": "72021100",
    # Aluminium (CN 7601–7616)
    "aluminium": "76011000",
    "aluminum": "76011000",
    "aluminium alloy": "76012000",
    # Cement (CN 2523)
    "cement": "25231000",
    "portland cement": "25232100",
    "clinker": "25231000",
    # Hydrogen (CN 2804)
    "hydrogen": "28041000",
    # Fertilisers (CN 3102–3105)
    "fertiliser": "31021000",
    "fertilizer": "31021000",
    "urea": "31021010",
    "ammonium nitrate": "31023000",
    "ammonia": "28141000",
    # Electricity
    "electricity": "27160000",
}

_HS_PREFIX_TO_CN: dict[str, str] = {
    "7206": "72061000",
    "7207": "72071100",
    "7208": "72081000",
    "7209": "72091500",
    "7210": "72101100",
    "7218": "72181000",
    "7601": "76011000",
    "7602": "76020000",
    "2523": "25231000",
    "2804": "28041000",
    "3102": "31021000",
    "3105": "31051000",
}


def _detect_cn_code(comet: dict[str, Any]) -> str:
    """Auto-detect an 8-digit CN code from the COMET data.

    Priority: explicit cnCode > hsCode > material description keywords.
    """
    # 1. Explicit CN code
    cn = _get(comet, "cnCode", "material.cnCode")
    if cn and len(str(cn)) == 8:
        return str(cn)

    # 2. HS code prefix lookup
    hs = _get(comet, "hsCode", "material.hsCode")
    if hs:
        hs_str = str(hs).replace(".", "").replace(" ", "")
        prefix = hs_str[:4]
        if prefix in _HS_PREFIX_TO_CN:
            return _HS_PREFIX_TO_CN[prefix]

    # 3. Material description keyword matching
    desc_fields = [
        _get(comet, "material.materialName", default=""),
        _get(comet, "material.tradeName", default=""),
        _get(comet, "productDescription", default=""),
        _get(comet, "boundaryDescription", default=""),
    ]
    combined = " ".join(str(f) for f in desc_fields).lower()
    for keyword, code in _CN_CODE_KEYWORDS.items():
        if keyword in combined:
            return code

    return "00000000"  # fallback — user should fill in


# ---------------------------------------------------------------------------
# Namespaces
# ---------------------------------------------------------------------------

_NS_CBAM = "urn:ec:taxud:cbam:v1"
_NS_COMET = "https://comet.carbon/v1/core#"
_NS_COMET_PCF = "https://comet.carbon/v1/pcf#"
_NS_COMET_MKT = "https://comet.carbon/v1/market#"
_NS_COMET_VER = "https://comet.carbon/v1/ver#"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Walk nested dicts and return the first non-None value found."""
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


def _generate_declaration_ref(comet: dict[str, Any]) -> str:
    """Generate a unique declaration reference number.

    Uses a hash of key fields to produce a reproducible reference.
    """
    seed_parts = [
        str(_get(comet, "pcfId", "eacId", default="")),
        str(_get(comet, "organization.orgName", default="")),
        str(date.today().isoformat()),
    ]
    seed = "|".join(seed_parts)
    hash_hex = hashlib.sha256(seed.encode()).hexdigest()[:12].upper()
    return f"CBAM-{hash_hex}"


def _calculate_specific_emissions(comet: dict[str, Any]) -> tuple[float, float, float]:
    """Calculate specific emissions rates (tCO2e per tonne of product).

    Returns (total_specific, direct_specific, indirect_specific).
    """
    # Look for already-calculated specific rates
    specific = _get(comet, "specificEmbeddedEmissions")
    direct_specific = _get(comet, "directEmissions")
    indirect_specific = _get(comet, "indirectEmissions")

    if specific is not None and direct_specific is not None:
        return (
            float(specific),
            float(direct_specific),
            float(indirect_specific or 0),
        )

    # Calculate from totals and quantity
    quantity_tonnes = _get(comet, "quantityImported", "unitaryProductAmount")
    fossil_gwp = _get(comet, "fossilGWP", default=0)

    if quantity_tonnes and float(quantity_tonnes) > 0:
        qty = float(quantity_tonnes)
        # fossilGWP in COMET is kgCO2e per declared unit — convert to tCO2e/t
        # if declared unit is kilogram, multiply by 1000 to get per tonne
        declared_unit = _get(comet, "declaredUnit", default="kilogram")
        gwp_val = float(fossil_gwp)

        if declared_unit in ("kilogram", "kg"):
            total_specific = gwp_val / 1000.0  # kgCO2e/kg → tCO2e/t
        elif declared_unit in ("tonne", "t"):
            total_specific = gwp_val
        else:
            total_specific = gwp_val / 1000.0  # default assumption: kg

        # Split: assume 85% direct / 15% indirect if not specified
        direct_pct = 0.85
        return (
            total_specific,
            total_specific * direct_pct,
            total_specific * (1.0 - direct_pct),
        )

    # Fallback to fossilGWP as kgCO2e/kg → tCO2e/t
    gwp = float(fossil_gwp)
    total_specific = gwp / 1000.0 if gwp > 0 else 0.0
    return (total_specific, total_specific * 0.85, total_specific * 0.15)


# ---------------------------------------------------------------------------
# Core conversion
# ---------------------------------------------------------------------------


def comet_to_cbam_xml(comet: dict[str, Any]) -> str:
    """Convert a COMET JSON-LD dict to CBAM XML string.

    Parameters
    ----------
    comet : dict
        Parsed COMET JSON-LD document (PCF or CBAMDeclaration type).

    Returns
    -------
    str
        Pretty-printed CBAM XML.
    """

    # Register namespaces so they appear as prefixes, not ns0/ns1
    ET.register_namespace("cbam", _NS_CBAM)
    ET.register_namespace("comet", _NS_COMET)
    ET.register_namespace("comet-pcf", _NS_COMET_PCF)
    ET.register_namespace("comet-mkt", _NS_COMET_MKT)
    ET.register_namespace("comet-ver", _NS_COMET_VER)

    # Root element
    root = ET.Element(f"{{{_NS_CBAM}}}CBAMDeclaration")
    root.set(f"xmlns:cbam", _NS_CBAM)
    root.set(f"xmlns:comet", _NS_COMET)
    root.set(f"xmlns:comet-pcf", _NS_COMET_PCF)
    root.set(f"xmlns:comet-mkt", _NS_COMET_MKT)
    root.set(f"xmlns:comet-ver", _NS_COMET_VER)

    # Declaration reference
    decl_ref = _generate_declaration_ref(comet)
    ref_el = ET.SubElement(root, f"{{{_NS_CBAM}}}declarationReference")
    ref_el.text = decl_ref

    # --- Declarant -----------------------------------------------------------
    declarant_el = ET.SubElement(root, f"{{{_NS_CBAM}}}declarant")
    org_el = ET.SubElement(declarant_el, f"{{{_NS_COMET}}}Organization")

    eori = _get(comet, "declarant.eori", "organization.orgId")
    if isinstance(eori, list):
        eori = eori[0] if eori else ""
    org_id_el = ET.SubElement(org_el, f"{{{_NS_COMET}}}orgId")
    org_id_el.set("type", "EORI")
    org_id_el.text = str(eori) if eori else ""

    org_name = _get(
        comet, "declarant.name", "organization.orgName", default=""
    )
    org_name_el = ET.SubElement(org_el, f"{{{_NS_COMET}}}orgName")
    org_name_el.text = str(org_name)

    # --- Reporting period ----------------------------------------------------
    period_el = ET.SubElement(root, f"{{{_NS_CBAM}}}reportingPeriod")
    tp_el = ET.SubElement(period_el, f"{{{_NS_COMET}}}TimePeriod")

    start_date = _get(
        comet,
        "reportingPeriod.startDate",
        "referencePeriod.startDate",
        default=date.today().replace(month=1, day=1).isoformat(),
    )
    end_date = _get(
        comet,
        "reportingPeriod.endDate",
        "referencePeriod.endDate",
        default=date.today().isoformat(),
    )
    # Strip time portions for CBAM (date only)
    if "T" in str(start_date):
        start_date = str(start_date).split("T")[0]
    if "T" in str(end_date):
        end_date = str(end_date).split("T")[0]

    start_el = ET.SubElement(tp_el, f"{{{_NS_COMET}}}startDate")
    start_el.text = str(start_date)
    end_el = ET.SubElement(tp_el, f"{{{_NS_COMET}}}endDate")
    end_el.text = str(end_date)

    # --- Goods ---------------------------------------------------------------
    goods_el = ET.SubElement(root, f"{{{_NS_CBAM}}}goods")

    # Handle coveredGoods array, or treat the whole object as one goods item
    covered_goods = comet.get("coveredGoods", [comet])
    if not isinstance(covered_goods, list):
        covered_goods = [covered_goods]

    for goods_item in covered_goods:
        item_el = ET.SubElement(goods_el, f"{{{_NS_CBAM}}}goodsItem")
        cbam_decl = ET.SubElement(item_el, f"{{{_NS_COMET_PCF}}}CBAMDeclaration")

        # CN Code
        cn_code = _detect_cn_code(goods_item if goods_item != comet else comet)
        cn_el = ET.SubElement(cbam_decl, f"{{{_NS_COMET_PCF}}}cnCode")
        cn_el.text = cn_code

        # Embedded emissions
        ee_el = ET.SubElement(cbam_decl, f"{{{_NS_COMET_PCF}}}embeddedEmissions")

        total_specific, direct_specific, indirect_specific = \
            _calculate_specific_emissions(goods_item if goods_item != comet else comet)

        see_el = ET.SubElement(ee_el, f"{{{_NS_COMET_PCF}}}specificEmbeddedEmissions")
        see_el.set("unit", "tCO2e/t")
        see_el.text = f"{total_specific:.4f}"

        de_el = ET.SubElement(ee_el, f"{{{_NS_COMET_PCF}}}directEmissions")
        de_el.set("unit", "tCO2e/t")
        de_el.text = f"{direct_specific:.4f}"

        ie_el = ET.SubElement(ee_el, f"{{{_NS_COMET_PCF}}}indirectEmissions")
        ie_el.set("unit", "tCO2e/t")
        ie_el.text = f"{indirect_specific:.4f}"

        # Production route
        prod_route = _get(
            goods_item if goods_item != comet else comet,
            "productionRoute",
            "boundaryDescription",
        )
        if prod_route:
            pr_el = ET.SubElement(ee_el, f"{{{_NS_COMET_PCF}}}productionRoute")
            pr_el.text = str(prod_route)

        # Site / Installation
        site_country = _get(
            goods_item if goods_item != comet else comet,
            "site.siteCountry",
            "installation.country",
            "organization.country",
        )
        site_id = _get(
            goods_item if goods_item != comet else comet,
            "site.siteId",
            "installation.installationId",
        )
        if site_country or site_id:
            site_el = ET.SubElement(cbam_decl, f"{{{_NS_COMET}}}Site")
            if site_country:
                sc_el = ET.SubElement(site_el, f"{{{_NS_COMET}}}siteCountry")
                sc_el.text = str(site_country)
            if site_id:
                si_el = ET.SubElement(site_el, f"{{{_NS_COMET}}}siteId")
                si_el.text = str(site_id)

        # Carbon price
        carbon_price = _get(
            goods_item if goods_item != comet else comet,
            "carbonPricePaid",
            "thirdCountryCarbonPrice",
            "carbonPrice.amount",
        )
        ets_price = _get(
            goods_item if goods_item != comet else comet,
            "euETSPrice",
            "carbonPrice.euETS",
        )
        if carbon_price or ets_price:
            tariff_el = ET.SubElement(cbam_decl, f"{{{_NS_COMET_MKT}}}CBAMShadowTariff")
            if ets_price:
                ets_el = ET.SubElement(tariff_el, f"{{{_NS_COMET_MKT}}}euETSPrice")
                ets_el.set("currency", "EUR")
                ets_el.text = str(ets_price)
            if carbon_price:
                cp_el = ET.SubElement(tariff_el, f"{{{_NS_COMET_MKT}}}thirdCountryCarbonPrice")
                cp_el.set("currency", "EUR")
                cp_el.text = str(carbon_price)

        # Quantity
        quantity = _get(
            goods_item if goods_item != comet else comet,
            "quantityImported",
            "unitaryProductAmount",
        )
        if quantity:
            fu_el = ET.SubElement(cbam_decl, f"{{{_NS_COMET_PCF}}}FunctionalUnit")
            qv_el = ET.SubElement(fu_el, f"{{{_NS_COMET_PCF}}}qudtValue")
            qv_el.text = str(quantity)
            qu_el = ET.SubElement(fu_el, f"{{{_NS_COMET_PCF}}}qudtUnit")
            qu_el.text = "tonne"

    # --- Verification --------------------------------------------------------
    ver = comet.get("verification", {})
    verifier_name = _get(ver, "verifierName", default=None)
    if verifier_name or _get(ver, "hasAssurance"):
        ver_el = ET.SubElement(root, f"{{{_NS_CBAM}}}verification")
        vc_el = ET.SubElement(ver_el, f"{{{_NS_COMET_VER}}}VerificationClaim")

        if verifier_name:
            vn_el = ET.SubElement(vc_el, f"{{{_NS_COMET_VER}}}verifierName")
            vn_el.text = str(verifier_name)

        level = _get(ver, "levelType", "level")
        if level:
            al_el = ET.SubElement(vc_el, f"{{{_NS_COMET_VER}}}assuranceLevel")
            al_el.text = str(level)

        std_ref = _get(ver, "standardRef")
        if std_ref:
            sr_el = ET.SubElement(vc_el, f"{{{_NS_COMET_VER}}}standardRef")
            sr_el.text = str(std_ref)

    # --- Serialize to pretty XML ---------------------------------------------
    raw_xml = ET.tostring(root, encoding="unicode", xml_declaration=False)

    # Add XML declaration header
    xml_decl = '<?xml version="1.0" encoding="UTF-8"?>\n'

    # Pretty-print with 2-space indentation
    try:
        dom = minidom.parseString(raw_xml)
        pretty = dom.toprettyxml(indent="  ", encoding=None)
        # minidom adds its own xml declaration — remove it and use ours
        lines = pretty.split("\n")
        if lines and lines[0].startswith("<?xml"):
            lines = lines[1:]
        body = "\n".join(line for line in lines if line.strip())
        return xml_decl + body + "\n"
    except Exception:
        return xml_decl + raw_xml + "\n"


# ---------------------------------------------------------------------------
# File-level I/O
# ---------------------------------------------------------------------------


def convert_file(input_path: Path) -> str:
    """Read a COMET JSON-LD file and return CBAM XML string.

    Parameters
    ----------
    input_path : Path
        Path to the COMET JSON-LD file.

    Returns
    -------
    str
        Pretty-printed CBAM XML.
    """
    with open(input_path, "r", encoding="utf-8") as fh:
        comet = json.load(fh)

    if isinstance(comet, list):
        # Multiple declarations — wrap in a single root with multiple goods
        # Use the first item for declarant/period info
        merged = dict(comet[0])
        merged["coveredGoods"] = comet
        return comet_to_cbam_xml(merged)

    return comet_to_cbam_xml(comet)


# ---------------------------------------------------------------------------
# CLI bridge
# ---------------------------------------------------------------------------


def export(input_path: str) -> str:
    """Bridge for comet_cli.py: export a COMET file to CBAM XML."""
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
        prog="comet_to_cbam",
        description="Generate CBAM XML from a COMET JSON-LD file.",
        epilog=(
            "Example: python comet_to_cbam.py steel-pcf.comet.json "
            "--output declaration.xml"
        ),
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to a COMET JSON-LD file (.comet.json)",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output file path (default: stdout)",
    )

    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"Error: input file not found: {args.input}", file=sys.stderr)
        return 1

    try:
        result_xml = convert_file(args.input)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON in {args.input}: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error converting {args.input}: {exc}", file=sys.stderr)
        return 1

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result_xml, encoding="utf-8")
        print(f"Wrote CBAM XML to {args.output}", file=sys.stderr)
    else:
        print(result_xml, end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
