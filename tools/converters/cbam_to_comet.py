#!/usr/bin/env python3
"""Convert a CBAM XML embedded-emissions declaration into COMET JSON-LD.

Parses the XML structure issued by DG TAXUD and maps elements to COMET
classes as defined in the data-exchange spec (Section 3).

Usage:
    python cbam_to_comet.py declaration.xml
    python cbam_to_comet.py declaration.xml --output comet_cbam.json

As a library:
    from cbam_to_comet import convert_cbam_to_comet
    doc = convert_cbam_to_comet("declaration.xml")
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

# ── COMET constants ──────────────────────────────────────────────────
COMET_CONTEXT = "https://comet.carbon/v1/jsonld/context.json"
COMET_TYPE = "comet-pcf:CBAMDeclaration"

# ── CN code → product description look-up ────────────────────────────
# Covers CBAM Annex I: steel, aluminium, cement, hydrogen, fertilisers
_CN_DESCRIPTIONS: dict[str, str] = {
    # Iron & steel (7206–7229)
    "7206": "Iron — remelted",
    "7207": "Iron — semi-finished (ingots/billets)",
    "7208": "Flat-rolled iron/steel — hot-rolled, width >= 600mm",
    "7209": "Flat-rolled iron/steel — cold-rolled, width >= 600mm",
    "7210": "Flat-rolled iron/steel — clad/plated/coated, width >= 600mm",
    "7211": "Flat-rolled iron/steel — width < 600mm",
    "7212": "Flat-rolled iron/steel — clad/plated/coated, width < 600mm",
    "7213": "Bars & rods — hot-rolled, coils",
    "7214": "Bars & rods — hot-rolled, other",
    "7215": "Bars & rods — cold-formed/cold-finished",
    "7216": "Angles, shapes & sections — iron/steel",
    "7217": "Wire of iron/steel",
    "7218": "Stainless steel — semi-finished",
    "7219": "Flat-rolled stainless — width >= 600mm",
    "7220": "Flat-rolled stainless — width < 600mm",
    "7221": "Bars & rods of stainless — hot-rolled",
    "7222": "Bars, rods, angles of stainless — other",
    "7223": "Wire of stainless steel",
    "7224": "Alloy steel — semi-finished",
    "7225": "Flat-rolled alloy steel — width >= 600mm",
    "7226": "Flat-rolled alloy steel — width < 600mm",
    "7227": "Bars & rods of alloy steel — hot-rolled",
    "7228": "Bars, rods, angles of alloy steel — other",
    "7229": "Wire of alloy steel",
    # Aluminium (7601–7616)
    "7601": "Unwrought aluminium",
    "7602": "Aluminium waste & scrap",
    "7603": "Aluminium powders & flakes",
    "7604": "Aluminium bars, rods & profiles",
    "7605": "Aluminium wire",
    "7606": "Aluminium plates, sheets, strip — thickness > 0.2mm",
    "7607": "Aluminium foil — thickness <= 0.2mm",
    "7608": "Aluminium tubes & pipes",
    "7609": "Aluminium tube/pipe fittings",
    "7610": "Aluminium structures & parts",
    "7611": "Aluminium reservoirs & tanks",
    "7612": "Aluminium casks, drums, cans",
    "7613": "Aluminium containers for compressed gas",
    "7614": "Aluminium stranded wire/cables",
    "7615": "Aluminium table, kitchen, sanitary articles",
    "7616": "Other articles of aluminium",
    # Cement (2523)
    "2523": "Portland cement, aluminous cement, slag cement",
    # Hydrogen (2804)
    "2804": "Hydrogen",
    # Fertilisers (3102–3105)
    "3102": "Mineral/chemical nitrogenous fertilisers",
    "3103": "Mineral/chemical phosphatic fertilisers",
    "3104": "Mineral/chemical potassic fertilisers",
    "3105": "Mineral/chemical fertilisers (two or three nutrients)",
}


def _cn_to_description(cn_code: str) -> str | None:
    """Look up a CN code (4- or 8-digit) in the known CBAM product map."""
    cn = cn_code.strip()
    # Try full code, then first 4 digits
    if cn in _CN_DESCRIPTIONS:
        return _CN_DESCRIPTIONS[cn]
    prefix = cn[:4]
    if prefix in _CN_DESCRIPTIONS:
        return _CN_DESCRIPTIONS[prefix]
    return None


def _validate_eori(eori: str) -> bool:
    """Validate EORI format: 2-letter ISO country code + up to 15 alphanumeric chars."""
    return bool(re.match(r"^[A-Z]{2}[A-Za-z0-9]{1,15}$", eori.strip()))


def _text(el: ET.Element | None) -> str:
    """Safely extract text from an XML element."""
    if el is None:
        return ""
    return (el.text or "").strip()


def _float_text(el: ET.Element | None) -> float | None:
    """Safely extract a float from an XML element."""
    t = _text(el)
    if not t:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def _find(parent: ET.Element, tag: str, ns: dict[str, str]) -> ET.Element | None:
    """Find an element, trying with each namespace prefix and also unqualified."""
    # Try with every registered namespace
    for prefix, uri in ns.items():
        found = parent.find(f"{{{uri}}}{tag}")
        if found is not None:
            return found
    # Try unqualified
    found = parent.find(tag)
    if found is not None:
        return found
    # Try case-insensitive on local names
    for child in parent:
        local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        if local.lower() == tag.lower():
            return child
    return None


def _findall(parent: ET.Element, tag: str, ns: dict[str, str]) -> list[ET.Element]:
    """Find all matching elements, namespace-aware."""
    results: list[ET.Element] = []
    for prefix, uri in ns.items():
        results.extend(parent.findall(f"{{{uri}}}{tag}"))
    if not results:
        results.extend(parent.findall(tag))
    if not results:
        tag_lower = tag.lower()
        for child in parent:
            local = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            if local.lower() == tag_lower:
                results.append(child)
    return results


def _extract_namespaces(xml_path: Path) -> dict[str, str]:
    """Extract namespace prefixes declared in the XML root."""
    ns: dict[str, str] = {}
    # Parse namespace declarations from raw text (ET strips them)
    raw = xml_path.read_text(encoding="utf-8")
    for m in re.finditer(r'xmlns:?(\w*)\s*=\s*"([^"]+)"', raw):
        prefix = m.group(1) or ""
        uri = m.group(2)
        ns[prefix] = uri
    return ns


def _parse_declarant(root: ET.Element, ns: dict[str, str]) -> dict[str, Any] | None:
    """Parse <AuthorisedDeclarant> or <declarant> element."""
    declarant_el = (
        _find(root, "AuthorisedDeclarant", ns)
        or _find(root, "declarant", ns)
    )
    if declarant_el is None:
        return None

    result: dict[str, Any] = {}

    # Look for EORI
    eori_el = _find(declarant_el, "EORI", ns) or _find(declarant_el, "orgId", ns)
    eori = _text(eori_el)
    if eori:
        if not _validate_eori(eori):
            print(f"Warning: invalid EORI format: {eori}", file=sys.stderr)
        result["orgId"] = eori
        result["orgIdType"] = "EORI"

    # Name
    name_el = (
        _find(declarant_el, "Name", ns)
        or _find(declarant_el, "orgName", ns)
        or _find(declarant_el, "name", ns)
    )
    name = _text(name_el)
    if name:
        result["orgName"] = name

    # Address
    addr_el = _find(declarant_el, "Address", ns) or _find(declarant_el, "address", ns)
    if addr_el is not None:
        result["address"] = _text(addr_el) or _collect_child_text(addr_el)

    # Try to get elements from Organization sub-element
    org_el = _find(declarant_el, "Organization", ns)
    if org_el is not None:
        if "orgId" not in result:
            eid = _find(org_el, "orgId", ns)
            if eid is not None:
                result["orgId"] = _text(eid)
        if "orgName" not in result:
            en = _find(org_el, "orgName", ns)
            if en is not None:
                result["orgName"] = _text(en)

    return result if result else None


def _collect_child_text(el: ET.Element) -> str:
    """Concatenate text from all children of an element."""
    parts = []
    for child in el:
        t = _text(child)
        if t:
            parts.append(t)
    return ", ".join(parts)


def _parse_goods(root: ET.Element, ns: dict[str, str]) -> list[dict[str, Any]]:
    """Parse <CoveredGoods> / <goods> / <goodsItem> elements."""
    goods: list[dict[str, Any]] = []

    # Try multiple element names
    goods_container = _find(root, "goods", ns) or _find(root, "CoveredGoods", ns) or root
    items = (
        _findall(goods_container, "goodsItem", ns)
        or _findall(goods_container, "CoveredGood", ns)
        or _findall(goods_container, "Good", ns)
    )
    if not items and goods_container is not root:
        items = list(goods_container)

    for item_el in items:
        good: dict[str, Any] = {}

        # CN code
        cn_el = _find(item_el, "CNCode", ns) or _find(item_el, "cnCode", ns)
        cn_code = _text(cn_el)
        if cn_code:
            good["cnCode"] = cn_code
            desc = _cn_to_description(cn_code)
            if desc:
                good["productDescription"] = desc

        # Country of origin
        country_el = (
            _find(item_el, "CountryOfOrigin", ns)
            or _find(item_el, "countryOfOrigin", ns)
            or _find(item_el, "siteCountry", ns)
        )
        country = _text(country_el)
        if country:
            good["site"] = {"siteCountry": country.upper()}

        # Installation
        install_el = (
            _find(item_el, "Installation", ns)
            or _find(item_el, "installation", ns)
            or _find(item_el, "Site", ns)
        )
        if install_el is not None:
            site = good.get("site", {})
            sid = _find(install_el, "InstallationId", ns) or _find(install_el, "siteId", ns)
            if sid is not None:
                site["siteId"] = _text(sid)
            sname = _find(install_el, "InstallationName", ns) or _find(install_el, "siteName", ns)
            if sname is not None:
                site["siteName"] = _text(sname)
            sc = _find(install_el, "siteCountry", ns) or _find(install_el, "Country", ns)
            if sc is not None and "siteCountry" not in site:
                site["siteCountry"] = _text(sc).upper()
            if site:
                good["site"] = site

        # Embedded emissions
        ee_el = (
            _find(item_el, "EmbeddedEmissions", ns)
            or _find(item_el, "embeddedEmissions", ns)
        )
        if ee_el is not None:
            emissions: dict[str, Any] = {}
            for xml_tag, comet_key in [
                ("SpecificDirectEmissions", "directEmissions"),
                ("directEmissions", "directEmissions"),
                ("SpecificIndirectEmissions", "indirectEmissions"),
                ("indirectEmissions", "indirectEmissions"),
                ("SpecificEmbeddedEmissions", "specificEmbeddedEmissions"),
                ("specificEmbeddedEmissions", "specificEmbeddedEmissions"),
                ("TotalEmbeddedEmissions", "totalEmbeddedEmissions"),
                ("totalEmbeddedEmissions", "totalEmbeddedEmissions"),
                ("ProductionRoute", "productionRoute"),
                ("productionRoute", "productionRoute"),
            ]:
                sub = _find(ee_el, xml_tag, ns)
                if sub is not None:
                    if comet_key == "productionRoute":
                        emissions[comet_key] = _text(sub)
                    else:
                        val = _float_text(sub)
                        if val is not None:
                            emissions[comet_key] = val
            # Calculate specific embedded from direct + indirect if missing
            if "specificEmbeddedEmissions" not in emissions:
                d = emissions.get("directEmissions")
                i = emissions.get("indirectEmissions")
                if d is not None and i is not None:
                    emissions["specificEmbeddedEmissions"] = round(d + i, 6)
            if emissions:
                good["embeddedEmissions"] = emissions
                # Map to top-level fossilGWP (direct emissions as proxy)
                if "directEmissions" in emissions:
                    good["fossilGWP"] = emissions["directEmissions"]
        else:
            # Try direct child elements
            for xml_tag, comet_key in [
                ("SpecificDirectEmissions", "directEmissions"),
                ("SpecificIndirectEmissions", "indirectEmissions"),
            ]:
                sub = _find(item_el, xml_tag, ns)
                if sub is not None:
                    val = _float_text(sub)
                    if val is not None:
                        good.setdefault("embeddedEmissions", {})[comet_key] = val

        # Quantity imported
        qty_el = (
            _find(item_el, "QuantityImported", ns)
            or _find(item_el, "quantity", ns)
            or _find(item_el, "qudtValue", ns)
        )
        qty = _float_text(qty_el)
        if qty is not None:
            good["quantityImported"] = qty
            # Calculate total embedded emissions
            spec = (good.get("embeddedEmissions") or {}).get("specificEmbeddedEmissions")
            if spec is not None:
                good.setdefault("embeddedEmissions", {})["totalEmbeddedEmissions"] = round(spec * qty, 6)

        # Carbon price paid
        cp_el = (
            _find(item_el, "CarbonPricePaid", ns)
            or _find(item_el, "carbonPricePaid", ns)
            or _find(item_el, "thirdCountryCarbonPrice", ns)
        )
        if cp_el is not None:
            price_val = _float_text(cp_el)
            if price_val is not None:
                currency = cp_el.get("currency", "EUR")
                good["carbonPricePaid"] = {
                    "amount": price_val,
                    "currency": currency,
                }
            else:
                # Carbon price might be a container element
                amt_el = _find(cp_el, "amount", ns) or _find(cp_el, "thirdCountryCarbonPrice", ns)
                cur_el = _find(cp_el, "currency", ns)
                amt = _float_text(amt_el)
                if amt is not None:
                    good["carbonPricePaid"] = {
                        "amount": amt,
                        "currency": _text(cur_el) or "EUR",
                    }

        # Also check for CBAMDeclaration wrapper inside goodsItem
        cbam_inner = _find(item_el, "CBAMDeclaration", ns)
        if cbam_inner is not None and cbam_inner is not item_el:
            # Recurse — parse the inner element as another goods item
            inner_goods = _parse_goods_from_element(cbam_inner, ns)
            if inner_goods:
                # Merge inner into current good
                for k, v in inner_goods.items():
                    if k not in good:
                        good[k] = v
                    elif isinstance(v, dict) and isinstance(good[k], dict):
                        good[k].update(v)

        if good:
            goods.append(good)

    return goods


def _parse_goods_from_element(el: ET.Element, ns: dict[str, str]) -> dict[str, Any]:
    """Parse goods fields from a single element (non-recursive helper)."""
    good: dict[str, Any] = {}
    cn_el = _find(el, "cnCode", ns) or _find(el, "CNCode", ns)
    if cn_el is not None:
        cn_code = _text(cn_el)
        good["cnCode"] = cn_code
        desc = _cn_to_description(cn_code)
        if desc:
            good["productDescription"] = desc

    ee_el = _find(el, "embeddedEmissions", ns) or _find(el, "EmbeddedEmissions", ns)
    if ee_el is not None:
        emissions: dict[str, Any] = {}
        for xml_tag, comet_key in [
            ("specificEmbeddedEmissions", "specificEmbeddedEmissions"),
            ("directEmissions", "directEmissions"),
            ("indirectEmissions", "indirectEmissions"),
            ("productionRoute", "productionRoute"),
        ]:
            sub = _find(ee_el, xml_tag, ns)
            if sub is not None:
                if comet_key == "productionRoute":
                    emissions[comet_key] = _text(sub)
                else:
                    val = _float_text(sub)
                    if val is not None:
                        emissions[comet_key] = val
        if emissions:
            good["embeddedEmissions"] = emissions

    site_el = _find(el, "Site", ns)
    if site_el is not None:
        site: dict[str, Any] = {}
        for tag, key in [("siteCountry", "siteCountry"), ("siteId", "siteId")]:
            s = _find(site_el, tag, ns)
            if s is not None:
                site[key] = _text(s)
        if site:
            good["site"] = site

    tariff_el = _find(el, "CBAMShadowTariff", ns)
    if tariff_el is not None:
        cp: dict[str, Any] = {}
        for tag, key in [
            ("euETSPrice", "euETSPrice"),
            ("thirdCountryCarbonPrice", "thirdCountryCarbonPrice"),
        ]:
            s = _find(tariff_el, tag, ns)
            if s is not None:
                val = _float_text(s)
                if val is not None:
                    currency = s.get("currency", "EUR")
                    cp[key] = {"amount": val, "currency": currency}
        if cp:
            good["carbonPricePaid"] = cp

    qty_el = _find(el, "FunctionalUnit", ns)
    if qty_el is not None:
        v = _find(qty_el, "qudtValue", ns)
        if v is not None:
            val = _float_text(v)
            if val is not None:
                good["quantityImported"] = val

    return good


def _parse_reporting_period(root: ET.Element, ns: dict[str, str]) -> dict[str, str] | None:
    """Parse <reportingPeriod> element."""
    rp_el = _find(root, "reportingPeriod", ns) or _find(root, "ReportingPeriod", ns)
    if rp_el is None:
        return None
    period: dict[str, str] = {}

    # May contain TimePeriod sub-element
    tp = _find(rp_el, "TimePeriod", ns) or rp_el
    start = _find(tp, "startDate", ns) or _find(tp, "Start", ns) or _find(tp, "start", ns)
    end = _find(tp, "endDate", ns) or _find(tp, "End", ns) or _find(tp, "end", ns)
    if start is not None:
        period["startDate"] = _text(start)
    if end is not None:
        period["endDate"] = _text(end)
    return period if period else None


def _parse_verification(root: ET.Element, ns: dict[str, str]) -> dict[str, Any] | None:
    """Parse <verification> element."""
    ver_el = _find(root, "verification", ns) or _find(root, "Verification", ns)
    if ver_el is None:
        return None

    ver: dict[str, Any] = {}
    # May wrap a VerificationClaim
    vc = _find(ver_el, "VerificationClaim", ns) or ver_el

    for xml_tag, comet_key in [
        ("verifierName", "verifierName"),
        ("VerifierName", "verifierName"),
        ("assuranceLevel", "levelType"),
        ("AssuranceLevel", "levelType"),
        ("standardRef", "standardRef"),
        ("StandardRef", "standardRef"),
        ("verificationDate", "verificationDate"),
        ("VerificationDate", "verificationDate"),
    ]:
        el = _find(vc, xml_tag, ns)
        if el is not None:
            ver[comet_key] = _text(el)

    return ver if ver else None


# ── Public API ───────────────────────────────────────────────────────

def convert_cbam_to_comet(xml_path: str | Path) -> dict[str, Any]:
    """Parse a CBAM XML declaration and return a COMET JSON-LD document.

    Parameters
    ----------
    xml_path : path to the CBAM XML file

    Returns
    -------
    COMET JSON-LD dict with @type "comet-pcf:CBAMDeclaration"
    """
    xml_path = Path(xml_path)
    if not xml_path.exists():
        raise FileNotFoundError(f"XML file not found: {xml_path}")

    ns = _extract_namespaces(xml_path)

    tree = ET.parse(xml_path)
    root = tree.getroot()

    doc: dict[str, Any] = {
        "@context": COMET_CONTEXT,
        "@type": COMET_TYPE,
        "declarationId": str(uuid.uuid4()),
    }

    # Declarant
    declarant = _parse_declarant(root, ns)
    if declarant:
        doc["declarant"] = declarant

    # Reporting period
    period = _parse_reporting_period(root, ns)
    if period:
        doc["reportingPeriod"] = period

    # Covered goods
    goods = _parse_goods(root, ns)
    if goods:
        doc["coveredGoods"] = goods

    # Verification
    verification = _parse_verification(root, ns)
    if verification:
        doc["verification"] = verification

    return doc


# ── CLI bridge ────────────────────────────────────────────────────────

def convert(input_path: str) -> dict[str, Any]:
    """Bridge for comet_cli.py: convert an input file to COMET JSON-LD."""
    return convert_cbam_to_comet(input_path)


# ── CLI ──────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert CBAM XML declaration to COMET JSON-LD.",
        epilog=(
            "Examples:\n"
            "  python cbam_to_comet.py declaration.xml\n"
            "  python cbam_to_comet.py declaration.xml --output comet_cbam.json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", type=Path, help="Path to the CBAM XML file")
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

    try:
        doc = convert_cbam_to_comet(args.input)
    except (FileNotFoundError, ET.ParseError) as exc:
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
