# COMET FAQ - Frequently Asked Questions

## General Questions (5)

### 1. What is COMET?

COMET (Carbon Ontology for Materials and Emissions Tracking) is a semantic ontology—a machine-readable representation of knowledge about carbon accounting and emissions tracking across supply chains. It uses the Web Ontology Language (OWL 2) to define classes, properties, and relationships that enable consistent carbon measurement and reporting.

Unlike spreadsheets or databases, COMET is semantic: it encodes *meaning* so that different systems can understand and integrate carbon data automatically.

### 2. Who should use COMET?

COMET is designed for:
- **Companies** tracking their scope 1, 2, and 3 emissions
- **Standards bodies** building domain-specific extensions
- **Software developers** building carbon accounting applications
- **Researchers** studying supply chain sustainability
- **Supply chain participants** sharing emissions data consistently

If you measure, report, or use carbon emissions data, COMET can help.

### 3. How is COMET different from the GHG Protocol?

**GHG Protocol** = accounting methodology (how to count emissions)

**COMET** = semantic representation (how to structure and share that data)

COMET *implements* GHG Protocol concepts. For example:
- GHG Protocol defines "Scope 3" emissions
- COMET defines the `ScopeThreeEmission` class to represent that concept in data
- Together they ensure accurate, interoperable emissions accounting

### 4. What license is COMET under?

COMET uses dual licensing:
- **CC BY 4.0** (Creative Commons Attribution): For the ontology data itself
- **Apache 2.0**: For software tools and implementations

You can use COMET freely in commercial and non-commercial projects, with attribution.

### 5. Is COMET only for carbon, or does it cover other environmental impacts?

Currently COMET focuses on carbon (CO2, CO2e) and is designed with carbon accounting as the primary use case. The seven-layer architecture is flexible enough to extend to other environmental impacts (water, waste, biodiversity) in future versions. Extensions are already exploring this (see [Creating Extensions](creating-extensions.md)).

---

## Technical Questions (8)

### 6. How is COMET structured?

COMET uses a seven-layer stack architecture:

1. **Data Layer**: Raw measurements, units, timestamps
2. **Process Layer**: Manufacturing, logistics, operations
3. **Product Layer**: Materials, specifications, BOM
4. **Certification Layer**: Standards, compliance, audit status
5. **Calculation Layer**: Factors, methodologies, formulas
6. **Reporting Layer**: Assertions, disclosures, compliance
7. **Impact Layer**: Boundaries, pathways, metrics

Each layer builds on the previous one. See [ADR-001](adr/ADR-001-seven-layer-stack.md) for details.

### 7. What's the difference between the core ontology and extensions?

**Core**: Common concepts used across all domains (Product, Emissions, Certification)

**Extensions**: Domain-specific specializations (e.g., ResponsibleSteel for steel, TextileTrace for textiles)

You can use COMET core alone, or combine it with extensions for your industry.

### 8. How is DPL (Detailed Product-Level) emissions calculated in COMET?

DPL calculation uses the Calculation Layer:

```
Total Emissions = Quantity × Emissions Factor × Adjustment Factors
```

In COMET:
```sparql
PREFIX comet: <https://comet.carbon/ontology/>

SELECT ?product (SUM(?amount) AS ?totalEmissions) WHERE {
  ?product comet:hasMaterial ?material ;
           comet:quantity ?quantity ;
           comet:unit ?unit .
  
  ?material comet:emissionsFactor ?factor ;
            comet:factorUnit ?factorUnit .
  
  BIND(?quantity * ?factor AS ?amount)
}
GROUP BY ?product
```

See [examples/calculate-emissions.sparql](../examples/calculate-emissions.sparql) for working examples.

### 9. How do I validate data against COMET constraints?

COMET includes SHACL (Shapes Constraint Language) files that define validation rules. To validate your RDF data:

```bash
comet validate --data my-data.ttl --shapes comet-shapes.ttl
```

Or programmatically:
```python
from comet import validate_data
report = validate_data('my-data.ttl', 'comet-shapes.ttl')
print(report)
```

Common constraints: required properties, datatype checks, cardinality, value ranges.

### 10. What RDF serialization formats does COMET support?

COMET ontology is defined in Turtle (`.ttl`) format because it's human-readable. However, you can use COMET with:
- **Turtle** (.ttl) - Recommended, human-readable
- **RDF/XML** (.rdf) - XML serialization
- **N-Triples** (.nt) - Line-based format
- **JSON-LD** (.jsonld) - JSON serialization with semantic context
- **N-Quads** (.nq) - Supports named graphs

Use JSON-LD if integrating with web applications; use Turtle for interchange and readability.

### 11. How does COMET align with external standards?

COMET has alignment files mapping to:
- **GHG Protocol**: Scope definitions, calculation methodology
- **ISO 14001**: Environmental management system concepts
- **PACT**: Product Attribute Communication standard
- **CBAM**: Carbon Border Adjustment Mechanism reporting
- **ISO 14040/44**: Lifecycle Assessment methodology

See `alignments/` directory for mapping files.

### 12. Can I use COMET with my existing database?

Yes. COMET data is RDF, which can be:
- **Generated** from SQL databases (use RDF mapping tools)
- **Stored** in graph databases (triple stores)
- **Queried** with SPARQL
- **Linked** to your application data using URIs

Tools like D2RQ and Virtuoso can map your SQL schema to COMET OWL. See [Integration Guide](integration-guide.md) (coming soon).

### 13. What's the SPARQL endpoint?

COMET provides a public SPARQL endpoint at:

```
https://sparql.comet.carbon/
```

Example query:
```bash
curl -H "Accept: application/sparql-results+json" \
  "https://sparql.comet.carbon/?query=SELECT%20%3Fclass%20WHERE%20%7B%20%3Fclass%20a%20owl%3AClass%20.%20%7D%20LIMIT%205"
```

---

## Contributing Questions (4)

### 14. How do I add a new language/translation to COMET?

Translations in COMET use RDFS labels with language tags. To add a language:

1. **Locate**: Check `labels/` directory
2. **Create/Update**: Add RDFS labels with language code (e.g., `@de` for German)
3. **Submit**: PR with branch `translation/de`

See [CONTRIBUTING.md#adding-translations](../CONTRIBUTING.md#adding-translations) for full process.

### 15. How do I create an extension for my industry?

Follow the [Extension Creation Cookbook](creating-extensions.md). Quick summary:
1. **Inventory** concepts in your domain
2. **Map** to COMET layers
3. **Generate** extension from template
4. **Add** SHACL shapes and examples
5. **Submit** RFC, then Draft PR

The ResponsibleSteel extension is a worked example.

### 16. What's the difference between Draft and Stable extensions?

| Aspect | Draft | Stable |
|--------|-------|--------|
| **Maturity** | Beta, testing | Production-ready |
| **Stability** | May change | Backward compatible |
| **Support** | Best-effort | Committed |
| **Backward compat** | No guarantees | Guaranteed |
| **Use case** | Pilot projects | Production deployments |

See [GOVERNANCE.md](../GOVERNANCE.md) for extension lifecycle details.

### 17. How do I report a bug or suggest a feature?

**Bugs**: File an issue with label `bug` and reproduce steps

**Features**: Use label `enhancement` and explain your use case

**Security**: Email conduct@comet.carbon (don't file public issues)

See [CONTRIBUTING.md#reporting-issues](../CONTRIBUTING.md#reporting-issues) for templates.

---

## Integration Questions (3)

### 18. How does COMET integrate with PACT?

PACT (Product Attribute Communication) is a standard for sharing product environmental data. COMET and PACT are complementary:

- **PACT** = exchange format (standardized data dictionary)
- **COMET** = semantic representation (RDF/OWL)

You can:
1. Export PACT data to COMET RDF
2. Validate using COMET SHACL shapes
3. Query with COMET SPARQL
4. Integrate with other systems

Alignment file: `alignments/pact-alignment.ttl`

### 19. Can COMET help with CBAM compliance?

Yes. CBAM (Carbon Border Adjustment Mechanism) requires tracking emissions across supply chains. COMET provides:

- **Structured data**: Represent CBAM-required emissions data (Scope 1, 2, 3)
- **Traceability**: Link emissions to products and suppliers
- **Validation**: SHACL constraints for CBAM-required fields
- **Reporting**: Export data in formats required by authorities

See `examples/cbam-compliance.sparql` for reporting queries.

### 20. What's the difference between COMET's Core ontology and COMET vs. OWL/RDF?

| Layer | Purpose |
|-------|---------|
| **RDF** | Graph data format (triple: subject-predicate-object) |
| **OWL** | Ontology language (defines classes, properties, constraints) |
| **COMET** | Domain ontology (specific to carbon accounting) |

Think of it as:
- **RDF** = the infrastructure (how to represent data)
- **OWL** = the grammar (how to define structure)
- **COMET** = the dictionary (specific concepts for carbon)

You need all three: RDF to store, OWL to structure, COMET to define carbon concepts.

---

## More Help

- **Getting started?** Read [Getting Started in 5 Minutes](getting-started.md)
- **Building something?** See [Creating Extensions](creating-extensions.md)
- **Have a question not here?** Open a discussion: https://github.com/comet-ontology/comet/discussions
- **Code of Conduct question?** Email conduct@comet.carbon
- **General inquiry?** Email contact@comet.carbon
