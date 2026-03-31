# ADR-001: Seven-Layer Stack Architecture

**Status**: Accepted

**Date**: 2026-03-15

---

## Context

COMET needed to represent carbon accounting across complex supply chains. Traditional approaches (flat databases, spreadsheets) struggle with the semantic complexity:

- **Different stakeholders** need different views (manufacturer sees production processes; retailer sees final product)
- **Multiple standards** apply simultaneously (GHG Protocol, ISO 14001, PACT, CBAM)
- **Integration challenges** across company boundaries and tools
- **Temporal dynamics** (supply chains change; certifications expire; factors evolve)

Early design attempts using a single flat class structure became unwieldy. We needed a principled way to organize the ontology that reflected the natural layers of carbon accounting.

---

## Decision

We adopt a **seven-layer stack architecture** for COMET, where each layer builds upon and extends the previous:

### Layer 1: Data Layer
**Concern**: Raw measurements and observations

**Concepts**: Measurement, Unit, Timestamp, Uncertainty, Source

**Purpose**: Foundation for all other layers; enables transparent, auditable data collection

**Example**: "1000 kg of raw material, measured on 2026-03-30"

### Layer 2: Process Layer
**Concern**: Activities and transformations in supply chain

**Concepts**: Process, Activity, Equipment, Duration, Input, Output

**Purpose**: Represents what happens to materials; links to emissions sources

**Example**: "Cold rolling process at temperature 20C for 4 hours"

### Layer 3: Product Layer
**Concern**: Materials, goods, and specifications

**Concepts**: Product, Material, BOM (Bill of Materials), Specification, Variant

**Purpose**: Defines what flows through supply chains; enables product-level tracking

**Example**: "Cold-rolled steel coil, 1000 kg, HSLA grade, thickness 2mm"

### Layer 4: Certification Layer
**Concern**: Standards compliance and verification

**Concepts**: Certification, Standard, Audit, Claim, VerificationScope

**Purpose**: Proves claims about products and processes; enables trust between parties

**Example**: "ResponsibleSteel certified, audited 2026-02-15"

### Layer 5: Calculation Layer
**Concern**: Methodology for computing emissions

**Concepts**: EmissionsFactor, CalculationMethod, Scope, GWP (Global Warming Potential)

**Purpose**: Transforms data into emissions using agreed methodologies; implements GHG Protocol

**Example**: "2.1 kg CO2e per kg steel (using primary fuel data)"

### Layer 6: Reporting Layer
**Concern**: Assertions and disclosure of results

**Concepts**: Assertion, Report, Scope1Emissions, Scope2Emissions, Scope3Emissions

**Purpose**: Communicates emissions results; enables regulatory compliance and stakeholder reporting

**Example**: "Total scope 1 emissions: 1,000,000 kg CO2e in 2025"

### Layer 7: Impact Layer
**Concern**: Connection to planetary boundaries and climate action

**Concepts**: PlanetaryBoundary, DecarbonizationTarget, ScienceBasedTarget, ClimateAction

**Purpose**: Links emissions to sustainability goals; enables impact assessment

**Example**: "Requires 50% emissions reduction by 2030 to meet 1.5C pathway"

---

## Architecture Diagram

```
┌──────────────────────────────────┐
│   7. Impact Layer                 │  Sustainability goals, climate pathways
├──────────────────────────────────┤
│   6. Reporting Layer              │  Emissions assertions, disclosures
├──────────────────────────────────┤
│   5. Calculation Layer            │  Methodologies, factors, scopes
├──────────────────────────────────┤
│   4. Certification Layer          │  Standards, audits, verification
├──────────────────────────────────┤
│   3. Product Layer                │  Materials, goods, specifications
├──────────────────────────────────┤
│   2. Process Layer                │  Activities, transformations
├──────────────────────────────────┤
│   1. Data Layer                   │  Measurements, units, timestamps
└──────────────────────────────────┘

Each layer:
- Builds on layers below
- Specializes concepts from lower layers
- Can be used independently
- Provides hooks for external extensions
```

---

## Consequences

### Positive

1. **Modularity**: Applications can use just the layers they need
   - Simple tracking: Layers 1-3
   - Certified supply chains: Layers 1-4
   - Full accounting: Layers 1-7

2. **Extensibility**: Domain extensions inherit natural attachment points
   - Steel extension specializes Product and Certification layers
   - Textile extension reuses Calculation layer
   - New domains don't need to reinvent foundations

3. **Standards Alignment**: Layer structure mirrors GHG Protocol and ISO standards
   - Scopes map to Reporting layer
   - Methodologies map to Calculation layer
   - Makes COMET recognizable to domain experts

4. **Semantic Clarity**: Each layer has well-defined concerns
   - Reduces ambiguity when integrating with external systems
   - Makes it easier to add constraints and validation rules
   - Facilitates stakeholder communication

5. **Temporal Modeling**: Layers naturally handle changes over time
   - Data is measured at moments (Layer 1)
   - Processes occur during periods (Layer 2)
   - Certifications have validity windows (Layer 4)
   - Factors evolve (Layer 5)

### Negative

1. **Complexity**: Seven layers is more to understand than a simple schema
   - Steeper learning curve for new users
   - More OWL constructs to learn

2. **Potential redundancy**: Some information could be represented at multiple layers
   - Requires clear design guidelines
   - Domain experts need training on when to use which layer

3. **Cross-layer queries**: Getting data across layers requires careful SPARQL design
   - Performance impact if not optimized
   - More joins than flat schema

### Neutral

1. **Scope-limited abstraction**: Layers are domain-specific to carbon/emissions
   - Not designed for general supply chain data
   - Would need significant modification for other environmental impacts

2. **Version management complexity**: Updates to one layer may affect layers above
   - Backward compatibility requires careful planning
   - Semantic versioning rules needed

---

## Alternatives Considered

### Alternative 1: Flat Class Hierarchy

**Approach**: Single inheritance tree without layer structure

**Pros**:
- Simpler to learn
- Fewer queries (no cross-layer joins)

**Cons**:
- Classes at different abstraction levels mixed together
- Hard to extend without breaking existing code
- Doesn't mirror how domain experts think about problem
- Difficult to implement standards (GHG Protocol) that have layer-like concepts

### Alternative 2: Three-Layer Model

**Approach**: Simpler version with only Data, Product, Reporting

**Pros**:
- Easier to implement and learn
- Covers 80% of use cases

**Cons**:
- Can't represent intermediate concerns (processes, certifications)
- Harder to achieve compatibility with external standards
- Certifications have to be bolted on awkwardly

### Alternative 3: Graph with Arbitrary Associations

**Approach**: Minimal ontology; let users define relationships freely

**Pros**:
- Maximum flexibility
- Simplest initial implementation

**Cons**:
- No interoperability between systems
- Impossible to validate
- Each company invents their own structure
- Defeats purpose of ontology

---

## Related Decisions

- **ADR-002**: Choice to use OWL 2 over RDFs (implements this architecture)
- **ADR-003**: Extension module pattern (built on layer structure)
- **ADR-004**: Dual licensing (CC BY + Apache; required for semantic web)

---

## References

- **GHG Protocol**: https://ghgprotocol.org/ (defines Scope 1, 2, 3)
- **ISO 14001**: Environmental management standards (influenced layer names)
- **PACT Standard**: Product Attribute Communication (validation of Layer 3-4)
- **Semantic Web Best Practices**: https://www.w3.org/TR/owl2-primer/ (implementation guidance)

---

## Discussion

The seven-layer stack emerged from analysis of existing carbon accounting systems (SAP, Salesforce, Higg, PACT) and carbon standards (GHG Protocol, ISO 14040). Common patterns across these systems showed that practitioners naturally think in terms of layers, even if not explicitly named.

The layers are *not* arbitrary; they represent distinct concerns in carbon accounting:
- Do you have the data? (Layer 1)
- How did you get it? (Layer 2)
- What are you measuring? (Layer 3)
- Who verified it? (Layer 4)
- How do you calculate? (Layer 5)
- What's your result? (Layer 6)
- What does it mean? (Layer 7)

This layering proved essential for supporting multiple standards simultaneously, which was a key requirement.
