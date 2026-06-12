# Changelog

All notable changes to COMET (Carbon Ontology for Materials and Emissions Tracking) are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

**Schema Map, Interactive Ontology & Value Lookup** (`docs/schema-map.html`)
- New single-source-of-truth extractor `tools/scripts/build-ontology-map.py` that reads **every** place a COMET term is defined — the seven-layer core vocabulary tables in `docs/glossary.html`, the OWL/SHACL extension modules (`comet-rs`, `comet-cn`), the incorporated CAD Trust v2.0.2 Data Dictionary (`docs/CAD-Trust-Data-Dictionary-v2.0.2.xlsx`), the three JSON Schemas, `comet-context.jsonld` and the alignment crosswalks — and normalises them into one 904-term table plus a node/edge graph
- New interactive page `docs/schema-map.html` with four views: (1) an interactive Cytoscape force-directed **ontology graph** (456 relational nodes, 267 edges incl. synthesised `partOf` property→class links) with namespace legend toggles, layout switching, search-to-isolate and per-node info cards; (2) a layered **schema map** of the COMET seven-layer stack + CAD Trust band with clickable term chips; (3) a sortable, searchable, filterable **value lookup** of all 904 terms (109 classes, 114 properties, 649 CAD Trust fields/picklist values, 32 individuals); (4) a sortable **alignments** crosswalk of 242 standards mappings (ISO 14068/14067, EU CBAM, EU ESRS, GHG Protocol, WBCSD PACT, UN SDG, CAD Trust, schema.org, QUDT, W3C PROV)
- New generated artifacts: `docs/comet-ontology-values.xlsx` (5-sheet workbook — Summary, Terms, Namespaces, Alignments, Schema Fields, with frozen panes + autofilter for in-Excel sorting), `docs/ontology-data.json` and `docs/ontology-data.js` (consolidated graph payload; the `.js` wrapper lets the page run from `file://`)
- The build canonicalises the two divergent `comet-rs` base IRIs so alignment edges connect to their defined term nodes, synthesises stub nodes for referenced-but-upstream COMET core terms and external standard targets, and keeps the flat 649-row CAD Trust dictionary in the table/XLSX (out of the relational graph) so the graph stays readable across the full stack
- Index page (`docs/index.html`) links to the new Schema Map
- `tools/requirements.txt` adds `rdflib` and `openpyxl`

**ISO 14068-1:2023 Carbon Neutrality Extension** (`comet-ext:iso14068`, prefix `comet-cn:`)
- New extension module aligning ISO 14068-1:2023 *Climate change management — Transition to net zero — Part 1: Carbon neutrality* with the COMET seven-layer stack
- 18 `owl:equivalentClass` bridges from ISO 14068 terms to existing COMET classes (carbon footprint, direct/indirect emissions, GHG removals, sources, sinks, GWP, CO2e, organizational + system boundaries, carbon credits, crediting programmes, registries, organization, product, stakeholder, top management, value chain)
- 24 new classes covering concepts COMET did not yet encode: `Subject`, `Entity`, `FinancialInstitution`, `Baseline`, `BasePeriod`, `ReportingPeriod`, `UnabatedGHGEmission`, `ResidualGHGEmission`, `GHGEmissionReduction`, `GHGRemovalEnhancement`, `CarbonNeutralityCommitment`, `CarbonNeutralityPathway`, `CarbonNeutralityManagementPlan`, `CarbonNeutralityClaim`, `CarbonNeutralityReport`, `HierarchyAction`, `CreditCriterion`, `CreditingProgrammeCriterion`, `CreditType`, `OffsettingEvent`, `CorrespondingAdjustment`, `RemovalReversal`, `VerificationOpinion`, `FinancedEmissionsAccount`
- 11 named-individual principles representing ISO 14068 Clause 4 (Transparency, Conservativeness, Hierarchy approach, Supporting transition, Ambition, Urgency, Science-based approach, Avoiding adverse impacts, Accountability, Value chain and life cycle approach)
- 15 object + datatype properties wiring the new classes together (`hasSubject`, `hasBoundary`, `hasCommitment`, `hasPathway`, `hasBaseline`, `hierarchyStep`, `meetsCriterion`, `targetYearResidualOnly`, `vintageEndYear`, `retirementDate`, `correspondingAdjustmentApplied`, `isExPostCredit`, `reportingPeriodStart`, `reportingPeriodEnd`, others)
- New extension files: `ext/iso14068/comet-ext-iso14068.ttl` (OWL ontology in Turtle), `ext/iso14068/README.md` (stakeholder summary report with merge map, expansion map, and benefits by stakeholder type)
- New documentation page: `docs/iso14068.html` — visual presentation of merge / expansion / stakeholder benefits / forbidden practices / adoption checklist
- JSON-LD context updated (`comet-context.jsonld`) with the new `comet-cn:` namespace and key terms
- Index page (`docs/index.html`) and ontology specification (`docs/ontology.html`) link to the new ISO 14068 extension

### Changed
- Top navigation on `docs/ontology.html` now exposes the ISO 14068 extension and the Materials hub

## [0.2.1] - 2026-04-27

### Added

**COMET Materials hub** (`docs/materials.html`)
- New page pairing the *A Shared Carbon Language* explainer video (~6 min, MP4, 33 MB) with the v0.1 Carbon Protocol stakeholder deck (14 slides, PPTX, 15 MB)
- Slide-by-slide summaries linking each visualization to the COMET layers, namespaces, and governance model it depicts
- Banner + TOC link on `docs/ontology.html` and three-card row on `docs/index.html` make the materials discoverable from the home page and the spec

## [0.2.0] - 2026-03-30

### Added

**Core Ontology Enhancements**
- SHACL constraint shapes for all core classes and properties
- Multilingual labels and definitions in 10 languages (English, Spanish, German, French, Mandarin, Portuguese, Japanese, Italian, Dutch, Swedish)
- RDF example datasets demonstrating emissions calculations, supply chain tracking, and carbon accounting scenarios
- Competency questions for each ontology domain with corresponding SPARQL query solutions
- JSON-LD context files for easier integration with web applications and APIs

**Infrastructure & Quality**
- Continuous Integration (CI) pipeline with automated testing and validation
- Community governance structure with decision-making processes and roles
- Extension module framework for domain-specific specialization
- SKOS concept schemes for controlled vocabularies and translations
- Alignment files mapping COMET to external standards (GHG Protocol, ISO 14001, PACT)
- Comprehensive documentation suite with tutorials, FAQs, and architectural decisions

**Documentation**
- Getting Started guide (5-minute quick start)
- Frequently Asked Questions (20 entries)
- Extension creation cookbook with worked examples
- Architecture Decision Records (ADRs 001-006)
- VoID dataset description for semantic web integration

### Changed
- Improved semantic clarity in core emissions calculation layer
- Enhanced domain-specific constraint definitions for better validation
- Strengthened alignment with international standards

### Fixed
- Resolved namespace URI conflicts with external vocabularies
- Improved SPARQL query performance with better indexing recommendations

## [0.1.0] - 2026-03-30

### Added

**ResponsibleSteel Extension Module**
- 31 new ontology classes for steel supply chain domain
- 15 object properties for relationships between steel entities
- 22 data properties for steel-specific attributes
- 13 named individuals representing common steel certifications and standards
- SHACL validation shapes for steel-specific constraints
- Example instance data for representative steel products and supply chains
- Multilingual labels (minimum 3 languages)
- Documentation and use cases for steel emissions tracking

**Core Infrastructure**
- Extension module pattern for building domain-specific specializations
- Support for extension integration with main ontology
- Framework for managing extension lifecycle (RFC → Draft → Stable)

## [0.0.1] - 2026-03-15

### Added

**Initial Release: Seven-Layer Stack Architecture**

Core ontology foundation with 7 semantic layers:

1. **Data Layer**: Raw emissions data, measurement units, temporal information
2. **Process Layer**: Manufacturing processes, supply chain operations, activity data
3. **Product Layer**: Material definitions, product specifications, bill of materials
4. **Certification Layer**: Standards compliance, certifications (ISO, PACT, CBAM), metadata
5. **Calculation Layer**: Emissions factors, calculation methodologies, accounting rules
6. **Reporting Layer**: Emissions assertions, report generation, disclosure requirements
7. **Impact Layer**: Planetary boundaries, decarbonization pathways, sustainability metrics

**Core Components**
- OWL 2 DL ontology definition with 250+ classes and properties
- Dual licensing (CC BY 4.0 for data, Apache 2.0 for software)
- Namespace URI design (https://comet.carbon/ontology/)
- RDF serialization in Turtle format
- Example SPARQL queries for common use cases

**Documentation**
- Ontology specification document
- Seven-layer architecture overview
- Example instance data in RDF/Turtle
- SPARQL query examples

---

## Deprecation Timeline

**Deprecations are announced 6+ months in advance with clear migration paths.**

Currently no active deprecations.

## Version Support

| Version | Status | Support Until |
|---------|--------|---------------|
| 0.2.0   | Current | 2026-09-30 (or until 1.0.0) |
| 0.1.0   | Deprecated | 2026-06-30 |
| 0.0.1   | Retired | Available in history |

## Future Releases

**Planned for Q2 2026**:
- Additional extensions (textiles, automotive, renewable energy)
- SPARQL endpoint reference implementation
- Python SDK enhancements
- Performance optimization for large datasets

**Planned for Q3 2026**:
- Version 1.0.0 candidate
- Governance review and refinement
- Integration guides for major platforms

---

## How to Upgrade

### From 0.1.0 to 0.2.0

No breaking changes. All queries and data remain compatible. To take advantage of new features:

1. **Update namespace references** to include new vocabulary if using new layers
2. **Add SHACL validation** to your applications for improved data quality
3. **Incorporate multilingual labels** if supporting international users
4. **Review example datasets** for best practices on new features

### From 0.0.1 to 0.1.0

No breaking changes. Add ResponsibleSteel classes to your ontology imports:
```
@prefix rs: <https://comet.carbon/ontology/responsiblesteel/> .
```

Then use steel classes as needed in your instance data.

---

## Reporting Issues

Found an issue with a specific release? File a bug report at https://github.com/comet-ontology/comet/issues with the version tag.

## Credits

COMET development is community-driven. See CONTRIBUTING.md for recognition and contribution guidelines.
