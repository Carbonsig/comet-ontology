# Changelog

All notable changes to COMET (Carbon Ontology for Materials and Emissions Tracking) are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
