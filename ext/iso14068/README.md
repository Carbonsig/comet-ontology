# COMET Extension: ISO 14068-1 Carbon Neutrality

**Module:** `comet-ext:iso14068`
**Namespace:** `https://comet.carbon/ext/iso14068#`
**Prefix:** `comet-cn:`
**Version:** 0.1.0
**Status:** RFC Open
**License:** CC BY 4.0 + Apache 2.0
**Standard:** ISO 14068-1:2023 *Climate change management — Transition to net zero — Part 1: Carbon neutrality*

---

## 1. What ISO 14068 actually is

ISO 14068-1:2023 is the first International Standard that defines, requires, and constrains a *carbon neutrality claim*. Before it existed, "carbon neutral" was a marketing term with no agreed meaning; greenwashing litigation, Advertising Standards Authority rulings, and the EU Green Claims Directive draft were filling the void with case law. ISO 14068 closes that gap.

The standard is built on four pillars:

1. **Hierarchy of mitigation (Clause 4.4 + 5.2).** An entity MUST first reduce in-boundary emissions, then enhance in-boundary removals, and only THEN offset what remains. Offsetting first is non-conformant.
2. **Footprint quantification by reference (Clause 8).** It does not invent a new accounting method — it requires ISO 14064-1 for organizations and ISO 14067 for products, with GHG Protocol consistency carve-outs in Annex C.
3. **Carbon-credit gatekeeping (Clause 11).** Five mandatory criteria — REAL · ADDITIONAL · MEASURABLE · PERMANENT · CERTIFIED — plus nine programme-level requirements covering registries, leakage, double-counting, and corresponding adjustments.
4. **Mandatory public reporting (Clause 12).** A 24-element carbon neutrality report, including the verification opinion, must be published for each reporting period.

The standard is normative for any entity making a public carbon-neutrality claim. It is the regulatory anchor for the EU Green Claims Directive, the UK CMA Green Claims Code, and the FTC Green Guides revisions.

## 2. Where COMET already covers ISO 14068 (MERGE)

Sixteen ISO 14068 terms map directly onto concepts COMET already encodes. The extension asserts these alignments via `owl:equivalentClass` / `owl:equivalentProperty` so reasoners can flow data between vocabularies without lossy conversion. **No new class is created here — only the bridge.**

| ISO 14068 § | ISO 14068 term | Existing COMET class | Notes |
|---|---|---|---|
| 3.2.4 | carbon footprint | `comet-pcf:PCFResult` | Identical for products via ISO 14067; for organizations the same class is used with an organizational boundary |
| 3.2.5 | direct GHG emission | `comet-pcf:Scope1Emission` | Direct = GHG Protocol Scope 1 |
| 3.2.6 | indirect GHG emission | `comet-pcf:IndirectGHGEmission` | Covers Scope 2 + Scope 3 — disambiguate downstream |
| 3.2.7 | GHG removal | `comet-pcf:GHGRemoval` | Reforestation, soil sequestration, BECCS, DAC + storage |
| 3.2.9 | GHG source | `comet-sc:GHGSource` | |
| 3.2.10 | GHG sink | `comet-sc:GHGSink` | |
| 3.2.11 | global warming potential | `comet-pcf:GlobalWarmingPotential` | |
| 3.2.12 | CO2e | `comet-pcf:CO2Equivalent` | |
| 3.2.16 | boundary `<organization>` | `comet:OrganizationalBoundary` | |
| 3.2.17 | boundary `<product>` | `comet-pcf:SystemBoundary` | |
| 3.3.2 | carbon credit | `comet-eac:CarbonCredit` | New ISO 14068 criteria layered on as `comet-cn:CreditCriterion` |
| 3.3.4 | carbon crediting programme | `comet-eac:CreditingProgramme` | |
| 3.3.5 | public registry | `comet-eac:PublicRegistry` | |
| 3.4.3 | organization | `comet:Organization` | |
| 3.4.4 | product | `comet:Product` | |
| 3.4.5 | stakeholder | `comet:Stakeholder` | |
| 3.4.6 | top management | `comet:TopManagement` | |
| 3.4.7 | value chain | `comet-sc:ValueChain` | |

**Implication:** ~50% of ISO 14068's terminology is already implementable on a COMET dataset today, before any extension classes are loaded. The merge alone makes existing COMET PCFs ISO 14068-readable.

## 3. Where ISO 14068 forces COMET to expand (NEW CLASSES)

ISO 14068 introduces concepts that have no current COMET representation. These live in the new `comet-cn:` namespace and are organized by the COMET layer they extend.

| Layer | New class | ISO 14068 § | Why it is needed |
|---|---|---|---|
| L1 Core | `Subject` | 3.4.2 | The unit being claimed neutral — can be Org OR Product. COMET previously had no union concept |
| L1 Core | `Entity` | 3.4.1 | The body MAKING the claim. Distinct from the Subject (e.g. parent claims for a subsidiary product) |
| L1 Core | `FinancialInstitution` | 3.4.3.1 + B.3 | Triggers the financed-emissions accounting requirement |
| L4 PCF | `Baseline` | 3.2.13 | Quantified base-period footprint, against which reductions are measured |
| L4 PCF | `BasePeriod` | 3.2.14 | Historical comparison period |
| L4 PCF | `ReportingPeriod` | 3.1.6 | Period for which the claim is made — typically annual |
| L4 PCF | `UnabatedGHGEmission` | 3.1.4 | Emission left after in-boundary reductions |
| L4 PCF | `ResidualGHGEmission` | 3.1.5 | Sub-class — what remains after ALL technically + economically feasible reductions. Anchors the long-term pathway target |
| L4 PCF | `GHGEmissionReduction` | 3.2.3 | First-class reduction artefact, baseline-relative |
| L4 PCF | `GHGRemovalEnhancement` | 3.2.8 | First-class enhancement artefact, distinct from a one-off removal |
| L4–L7 | `CarbonNeutralityCommitment` | 6 | Required precondition — top management commitment |
| L4–L7 | `CarbonNeutralityPathway` | 5.3, Annex A | Trajectory with short, long, and residual-only targets |
| L4–L7 | `CarbonNeutralityManagementPlan` | 9 | The full plan composed of pathway + baseline + targets + safeguards |
| L4–L7 | `CarbonNeutralityClaim` | 3.1.3 | The public declaration |
| L4–L7 | `CarbonNeutralityReport` | 12 | The 24-element public report (sub-class of `comet-ver:DisclosureRecord`) |
| L4–L7 | `HierarchyAction` | 4.4, 5.2 | Enum: reduce / enhance / offset — mandatory tag on every plan action |
| L5 EAC | `CreditCriterion` | 11.2 | The 5 mandatory criteria a credit must satisfy |
| L5 EAC | `CreditingProgrammeCriterion` | 11.3 | The 9 mandatory programme-level criteria |
| L5 EAC | `CreditType` | 3.3.2 N2 | Avoidance / Reduction / Removal — drives whether the credit can be used after residual |
| L5 EAC | `OffsettingEvent` | 3.3.1 | Sub-class of `comet-eac:RetirementEvent` with vintage + 12-month retirement constraints |
| L5 EAC | `CorrespondingAdjustment` | 11.1 NOTE | Article 6.4 disclosure (§12 t) |
| L6 Ver | `RemovalReversal` | 10.2 | Re-class as emission in the reporting period of reversal |
| L6 Ver | `VerificationOpinion` | 12 w | Bridges to ISO 14064-3 |
| L7 / Annex B | `FinancedEmissionsAccount` | Annex B.3 | Financial-institution-specific boundary component aligned to PCAF |

That is **24 new classes**, **11 SKOS principles** (Clause 4 enumerated as `comet-cn:Principle` instances), and **15 properties** linking them.

### Summary count

| Metric | Count |
|---|---|
| ISO 14068 terms mapped to existing COMET (`owl:equivalentClass`) | 18 |
| New classes proposed | 24 |
| Named-individual principles (Clause 4) | 11 |
| Object + datatype properties added | 15 |
| Total triples added by extension | ~280 |

## 4. What ISO 14068 means to each stakeholder

### Industrial buyers and product owners
- **Defends premium pricing.** A "carbon neutral" claim with no ISO 14068 documentation is now a regulatory risk. With the extension, every premium product has a structured `CarbonNeutralityReport` referenced from the PCF — auditors, customers and regulators see the full chain in one query.
- **Forces hierarchy discipline.** The plan cannot leap to offsets. Because every action carries a `comet-cn:hierarchyStep` tag, finance can audit whether reductions came before purchases and refuse to sign off plans that invert the order.
- **Replaces ad-hoc spreadsheets.** Baseline, base period, reporting period and target year become typed, versioned artefacts instead of cells in an Excel file owned by one person.

### Financial institutions
- **Directly addressed by Annex B.3.** A bank or asset manager claiming neutrality must account for financed emissions of its investee book. `comet-cn:FinancedEmissionsAccount` integrates the PCAF methodology into the COMET portfolio model — the same JSON-LD payload supports both ISO 14068 and a PCAF disclosure.
- **Prudential value.** Supervisors (ECB, PRA, FSB) increasingly require evidence that "net-zero" pledges have hierarchy and pathway substance. A COMET + ISO 14068 dataset is materially harder to dismiss than a sustainability-report PDF.
- **Tradeable signal.** Verified residual-only credits priced via `comet-cn:RemovalCredit` carry different risk than `comet-cn:AvoidanceCredit` — the L7 Market layer can finally price the difference.

### Carbon verifiers (BV / SGS / DNV / TÜV / etc.)
- **Machine-readable verification scope.** Instead of re-deriving boundaries from a sustainability report, the verifier ingests the `CarbonNeutralityManagementPlan` directly and checks each clause against ISO 14068 mandatory elements.
- **Audit trail by construction.** `RemovalReversal`, `CorrespondingAdjustment`, `OffsettingEvent` with vintage + retirement dates are first-class objects. Re-issuing a reasonable-assurance opinion year over year becomes diff-on-graph rather than re-walk.
- **Bridge to ISO 14064-3.** `VerificationOpinion` is a sub-class of `comet-ver:AuditClaim`, so existing COMET verification workflows extend cleanly.

### Regulators (EU Commission / DG ENV, UK CMA, FTC, member-state competent authorities)
- **EU Green Claims Directive enforcement asset.** The directive requires substantiation of climate claims with internationally recognized standards. COMET + ISO 14068 produces a canonical JSON-LD document set per claim — easier to subpoena, easier to compare across firms, easier to prosecute when missing.
- **Hierarchy compliance is queryable.** A SPARQL query over a dataset answers "did this entity use offsets before exhausting in-boundary reductions?" without reading any prose.
- **Cross-border consistency.** Same vocabulary in Brussels, London and Washington reduces forum shopping.

### LCA practitioners (SimaPro, openLCA, GaBi, ecoinvent users)
- **PCF outputs become claim-ready.** Already produce ISO 14067 PCFs — the extension wraps the existing result in `Baseline`, `BasePeriod`, `ReportingPeriod` so no parallel methodology is needed.
- **Sectoral pathway alignment.** `CarbonNeutralityPathway` carries the science-based pathway reference (IPCC / IEA / SBTi / ACT) so practitioners can validate whether a client's targets are commensurate with the sector's transition.

### Carbon-market platforms and registries
- **Programme-level conformance.** `CreditingProgrammeCriterion` enumerates the nine ISO 14068 §11.3 requirements. Verra, Gold Standard, ART TREES, Climate Action Reserve etc. can publish a one-time `owl:sameAs` mapping to declare conformance and inherit access to ISO 14068 buyers.
- **Vintage and retirement enforcement.** Datatype properties `vintageEndYear`, `retirementDate`, `correspondingAdjustmentApplied` and `isExPostCredit` make the §11.2 timing rules computable — a registry can refuse a retirement that violates them.

### Investors and analysts (ESG funds, transition-debt issuers, rating agencies)
- **Cuts through claim noise.** Distinguishes a claim with hierarchy + pathway + verification from one without, in machine-readable form. Ratings can be derived rather than asserted.
- **Pathway-aware exposure.** Portfolio models can integrate `targetYearResidualOnly` directly — exclude or weight names whose pathway slips beyond 2050 without requiring narrative interpretation.

## 5. Architecture — how it threads through the seven-layer stack

```
L7 Market           CarbonPremium  ←  hierarchy-aware pricing of residual-only credits
                       ↑
L6 Verification     VerificationOpinion · RemovalReversal · CorrespondingAdjustment
                       ↑
L5 EAC              CarbonCredit + CreditCriterion · OffsettingEvent
                       ↑
L4 PCF              PCFResult · Baseline · BasePeriod · ReportingPeriod
                    UnabatedGHGEmission · ResidualGHGEmission
                    GHGEmissionReduction · GHGRemovalEnhancement
                       ↑
L1 Core             Subject (Org ∪ Product) · Entity · FinancialInstitution
```

**Cross-cutting:** `CarbonNeutralityManagementPlan`, `CarbonNeutralityPathway`, `CarbonNeutralityClaim`, `CarbonNeutralityReport`, `HierarchyAction`. These reach across L4 → L7.

## 6. Implementation checklist for adopters

1. Stand up an `Entity` and the `Subject` it claims for; bind a `Boundary` per ISO 14064-1 (orgs) or ISO 14067 (products).
2. Set `BasePeriod`, compute `Baseline` (reuse `comet-pcf:PCFResult`), set `ReportingPeriod`.
3. Build `CarbonNeutralityPathway` with `targetYearResidualOnly` and short/long-term targets.
4. Compose `CarbonNeutralityManagementPlan`; tag every action with `comet-cn:hierarchyStep`.
5. Execute reductions, then enhancements; quantify each with `GHGEmissionReduction` / `GHGRemovalEnhancement` against `Baseline`.
6. Determine remaining `ResidualGHGEmission` / `UnabatedGHGEmission`; size offsetting volume.
7. Source carbon credits — assert each meets the five `CreditCriterion`. Encode `vintageEndYear`, `correspondingAdjustmentApplied`, `isExPostCredit`. Retire as `OffsettingEvent` ≤12 months after reporting-period end.
8. Commission `VerificationOpinion` (ISO 14064-3). Publish `CarbonNeutralityReport` with all 24 elements.
9. Re-evaluate plan annually; reclassify any `RemovalReversal` as emission in the reporting period of reversal.

## 7. What ISO 14068 forbids (and the extension makes auditable)

| Forbidden practice | How the extension catches it |
|---|---|
| Offsetting before reducing | Every action tagged with `comet-cn:hierarchyStep`; SPARQL surfaces plans where step 3 precedes steps 1–2 |
| Using credits whose vintage ended >5 years before claim period | `vintageEndYear` ≥ `reportingPeriodStart − 5y` is a SHACL constraint |
| Retiring credits more than 12 months after period end | `retirementDate` ≤ `reportingPeriodEnd + 12 months` is a SHACL constraint |
| Double counting between entity and host country (Article 6) | `correspondingAdjustmentApplied` boolean must be present and disclosed |
| Forward-flow credits (ex-ante) used for a current claim | `isExPostCredit = true` is required |
| Quietly dropping a reversed removal | `RemovalReversal` must be re-classed as emission in period of reversal |
| Using only avoidance credits to offset residual emissions | When `ResidualGHGEmission > 0`, accompanying credits must be `RemovalCredit` (per §11.1) |

## 8. Files

| File | Description |
|---|---|
| `comet-ext-iso14068.ttl` | OWL ontology in Turtle — 24 new classes, 11 principle individuals, 15 properties, 18 `owl:equivalentClass` mappings |
| `README.md` | This document — merge analysis, expansion analysis, stakeholder benefits, adoption guidance |

## 9. Standards references

- **ISO 14068-1:2023** — Climate change management — Transition to net zero — Part 1: Carbon neutrality (Nov 2023, First edition)
- **ISO 14064-1:2018** — GHG quantification & reporting at organization level (normative reference)
- **ISO 14067:2018** — Carbon footprint of products (normative reference)
- **ISO 14064-2:2019** — GHG quantification at project level (referenced for credit methodologies)
- **ISO 14064-3:2019** — Validation and verification (referenced for §12 w)
- **GHG Protocol Corporate / Product Standards** — consistency comparison in Annex C
- **PCAF Global GHG Accounting and Reporting Standard** — referenced for Annex B.3 financed emissions
- **Paris Agreement Article 6.4** — corresponding adjustments mechanism

## 10. Open RFC questions

1. Should `Subject` be a single `owl:unionOf` class, or two parallel sub-classes `OrganizationSubject` / `ProductSubject`? Current draft uses union; flag if reasoner performance is impacted.
2. Annex B covers events, financial institutions, market-vs-location-based electricity, and groups of organizations. Each may need its own sub-extension; this v0.1 covers Annex B.3 only.
3. The 24-element `CarbonNeutralityReport` is currently a single class. Do we encode each `§12 a–x` element as a required property (SHACL) or as a sub-property? Default: SHACL nodeshape — see `comet-ext-iso14068-shapes.ttl` (next milestone).
4. Should the `comet-cn:` prefix become `comet-iso14068:` for consistency with future ISO 14068-2 (entity-level) and 14068-3 if published? Vote in the Carbon-Neutrality-WG.
