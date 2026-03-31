# COMET Extension: ResponsibleSteel

**Module:** `comet-ext:responsiblesteel`
**Namespace:** `https://comet.carbon/ext/responsiblesteel#`
**Prefix:** `comet-rs:`
**Version:** 0.1.0
**Status:** RFC Open
**License:** CC BY 4.0 + Apache 2.0

## Summary

This extension maps the **ResponsibleSteel International Production Standard V2.1.1** (Oct 2024), the **Fundamentals for GHG Emissions Accounting & Classification V1.0** (Jun 2025), and the **Climate Transition Plans Interpretation** (Dec 2025) onto the COMET seven-layer stack.

| Metric | Count |
|--------|-------|
| RS variables mapped | 87 |
| Direct COMET matches | 34 |
| Extended existing classes | 22 |
| **New classes proposed** | **31** |

## Layer Coverage

| Layer | New Classes | Key Additions |
|-------|------------|---------------|
| L1 Core | 3 | `CertifiedSite`, `CorporateOwner`, `SteelProductionRoute` |
| L3 Supply Chain | 5 | `ScrapCategory`, `RSSupplierTier`, `SupplierESGRisk` |
| L4 PCF | 6 | `CrudeSteelIntensity`, `ScrapShareCalculation`, `DPLThreshold`, `ProcessGasBaseline`, `EnergyRecoveryCredit`, `CCUSCredit` |
| L5 EAC | 7 | `CoreSiteCertification`, `SteelCertification`, `DecarbProgressLevel`, `SourcingProgressLevel`, `CertifiedSteelMark`, `CoCTransferEvent`, `CoCClaim` |
| L6 Verification | 6 | `CertificationAudit`, `AssurancePanelReview`, `NonConformity`, `PrincipleConformity`, `TransitionPlanReview`, `AmbitionGapAnalysis` |
| L7 Market | 2 | `ProgressLevelPricing`, `GreenSteelPremium` |

Plus **13 named individuals** for the RS Principles enumeration (P1–P13).

## Critical Gaps Addressed

1. **Certification lifecycle model** — Full pipeline from audit → Assurance Panel → certification decision → product labelling
2. **Decarbonisation Progress Level (DPL)** — The four-tier sliding-scale classification (y ≤ b − m(x)) linking GHG intensity + scrap share to market access
3. **Chain of Custody** — Transfer events and claims for tracking certified steel through downstream manufacturing
4. **13-Principle ESG conformity vector** — Machine-readable representation of the full RS governance architecture beyond carbon-only
5. **Process gas baseline & credit system** — RS-specific accounting for captured process gases and energy recovery

## Files

| File | Description |
|------|-------------|
| `comet-ext-responsiblesteel.ttl` | OWL ontology in Turtle format (31 classes, 15 object properties, 22 data properties, 13 named individuals) |
| `README.md` | This file |

## Standards References

- ResponsibleSteel International Production Standard V2.1.1 (1 October 2024)
- ResponsibleSteel Fundamentals for GHG Emissions Accounting & Classification V1.0 — Clean (18 June 2025)
- ResponsibleSteel Interpretation: Climate Transition Plans (December 2025)
- ResponsibleSteel Interpretation: Principle 6 Equal Pay (12 June 2025)
- ISO 14067:2018, ISO 14064-3:2019, ISO 20915

## Usage

```turtle
@prefix comet-rs: <https://comet.carbon/ext/responsiblesteel#> .

# Example: A certified site with DPL 2
ex:GentSite a comet-rs:CertifiedSite ;
    comet-rs:certificateId "AB-12345678" ;
    comet-rs:annualCrudeSteelProduction 5200000 .

ex:GentIntensity a comet-rs:CrudeSteelIntensity ;
    comet-rs:ghgIntensityValue 1.45 .

ex:GentScrap a comet-rs:ScrapShareCalculation ;
    comet-rs:scrapSharePercent 22.5 .

ex:GentDPL a comet-rs:DecarbProgressLevel ;
    comet-rs:dplLevel 2 .

ex:GentCert a comet-rs:SteelCertification ;
    comet-rs:hasDPL ex:GentDPL ;
    comet-rs:hasSPL ex:GentSPL .
```

## Contributing

This extension follows the COMET PR workflow (Ontology Specification, Visualization 10). PRs targeting this module should be tagged:

- `layer:L1–L7` (as applicable)
- `type:new-class` or `type:property-extension`
- `std:responsiblesteel`
- `sector:steel`
- `status:rfc-open`
