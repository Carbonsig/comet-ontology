# ADR-002: OWL 2 over RDFS

**Status**: Accepted

**Date**: 2026-03-15

---

## Context

COMET needed to choose a semantic web language for expressing the ontology. The primary candidates were:

1. **RDFS** (RDF Schema): Simpler, minimal semantics
2. **OWL 1**: Older W3C standard, widely supported
3. **OWL 2**: Current W3C standard, richer expressiveness

The choice significantly impacts:
- Tool support and interoperability
- Query complexity
- Reasoning capabilities
- Learning curve for new contributors
- Implementation performance

Early discussions showed that COMET's requirements demanded more expressiveness than RDFS offers, but the team was concerned about OWL 2's complexity.

---

## Decision

**We adopt OWL 2 DL (Description Logic) as the formal language for COMET.**

### Rationale

COMET's semantic requirements exceed what RDFS can express:

1. **Cardinality constraints**: "A Product must have at least one Material"
   - RDFS: No way to express this
   - OWL 2: `sh:minCount 1` (via SHACL)

2. **Property restrictions**: "Steel products have steel grades, not other material grades"
   - RDFS: No way to restrict ranges by domain
   - OWL 2: `rdfs:range rs:SteelGrade` within `rdfs:domain rs:SteelProduct`

3. **Inverse properties**: "If product X uses material Y, then material Y is used-in product X"
   - RDFS: No automatic inference
   - OWL 2: `owl:inverseOf` enables automatic linkage

4. **Transitivity**: "Supplier A's supplier B's carbon footprint affects A"
   - RDFS: No way to express
   - OWL 2: `owl:TransitiveProperty` on `hasSupplier`

5. **Datatype constraints**: "Emissions value must be ≥ 0"
   - RDFS: No enforcement
   - OWL 2: XSD datatypes + SHACL constraints

### Profile Choice: OWL 2 DL vs OWL 2 Full

We chose **OWL 2 DL** (Description Logic profile) rather than OWL 2 Full:

- **OWL 2 DL**: Restricted syntax ensuring decidability
  - Guarantees reasoning algorithms will terminate
  - Tools can provide full inference
  - Better performance
  - Can be translated to first-order logic

- **OWL 2 Full**: Unrestricted (actually almost as powerful as RDF)
  - Allows arbitrary RDF (classes can be instances, properties are objects)
  - Makes reasoning undecidable
  - Few tools support full reasoning
  - Defeats purpose of structured ontology

**Decision**: OWL 2 DL because COMET prioritizes reliable reasoning and tool support over theoretical expressiveness.

---

## Implementation

### Serialization

COMET ontology is serialized in **Turtle** format:
```turtle
@prefix comet: <https://comet.carbon/ontology/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

comet:Product
  a owl:Class ;
  rdfs:label "Product"@en ;
  rdfs:comment "Any product or material in the supply chain" .
```

Turtle is:
- Human-readable (unlike RDF/XML)
- Concise (unlike N-Triples)
- Standardized (W3C standard)
- Widely supported

### OWL 2 DL Constraints

COMET enforces OWL 2 DL rules to ensure interoperability:

1. **No punning**: A URI cannot be both a class and individual
2. **Property cardinality**: Use SHACL for complex cardinality (not OWL restrictions)
3. **No class cycles**: Avoid infinite inheritance chains
4. **Datatype restrictions**: Use XSD datatypes + SHACL

### Validation

All COMET ontology files are validated with:
```bash
# Check OWL 2 DL profile compliance
owltools comet.ttl --validate-owl
```

---

## Consequences

### Positive

1. **Standards Alignment**: OWL 2 is the W3C standard for ontologies
   - Industry recognition
   - Tool support (Protégé, Stardog, etc.)
   - Academic compatibility

2. **Expressive Power**: Can represent necessary constraints
   - Cardinality requirements for quality control
   - Domain/range restrictions for semantic clarity
   - Transitivity for supply chain reasoning

3. **Reasoning Capabilities**: Automated inference discovers implicit facts
   - If A supplies B, and B supplies C, infer A supplies C (transitivity)
   - If Product is Class X and Class X has property P, infer Product has property P (inheritance)
   - Automatic consistency checking

4. **Future-Proofing**: OWL 2 can express concepts we may need later
   - Domain extension without paradigm shift
   - Adding new constraint types
   - Supporting complex reasoning scenarios

5. **Ecosystem Support**: Rich tooling around OWL 2
   - Protégé editor for ontology design
   - Stardog for semantic web database
   - OWLAPI for programmatic access
   - TopBraid for validation

### Negative

1. **Complexity**: OWL 2 has steep learning curve
   - New contributors need training
   - More constructs to learn
   - Easier to make mistakes

2. **Performance**: Reasoning can be expensive
   - Some queries may be slower than flat database
   - Graph reasoning over large datasets needs optimization
   - Not suitable for real-time transaction processing

3. **Tool Ecosystem Overhead**: Managing OWL files requires tooling
   - Not as simple as JSON or CSV
   - Requires RDF-aware tools
   - Visualization/debugging less straightforward

4. **Specification Burden**: OWL 2 specification is complex
   - 600+ page specification
   - Multiple profiles and profiles
   - Few people understand entire spec

### Neutral

1. **Performance Trade-offs**: OWL 2 enables inference, which is computationally costly
   - Acceptable for design-time reasoning
   - Acceptable for periodic batch processing
   - Not suitable for sub-millisecond query latency (use database queries instead)

---

## Alternatives Considered

### Alternative 1: RDFS Only

**Approach**: Simpler semantic web language

**Pros**:
- Easier to learn and teach
- Better performance
- Simpler tooling

**Cons**:
- Cannot express required constraints
- No cardinality checking
- No automated reasoning
- Extensions would need custom validation

### Alternative 2: JSON Schema

**Approach**: Use JSON for serialization, JSON Schema for validation

**Pros**:
- Very familiar to developers
- Excellent tooling ecosystem
- Simple to understand

**Cons**:
- Not semantic web compatible
- Cannot express OWL-level semantics
- No linking to external ontologies
- Proprietary format (not W3C standard)

### Alternative 3: Property Graph (Neo4j)

**Approach**: Use property graph model like Neo4j

**Pros**:
- Excellent query performance
- Good visualization tools
- Simpler semantics than OWL

**Cons**:
- Proprietary format
- Not interoperable with semantic web standards
- Cannot link to external data sources
- Limited reasoning capabilities

### Alternative 4: UML + XSD

**Approach**: Use UML for modeling, XSD for serialization

**Pros**:
- Familiar to enterprise architects
- Good tool support in UML editors

**Cons**:
- Not suitable for semantic web integration
- Limited reasoning capabilities
- Closed ecosystem
- Not interoperable with carbon accounting standards

---

## Related Decisions

- **ADR-001**: Seven-layer architecture (requires OWL semantics)
- **ADR-006**: SHACL alongside OWL (complementary languages)
- **ADR-004**: Dual licensing (CC BY + Apache; semantic data needs license)

---

## References

- **OWL 2 Specification**: https://www.w3.org/TR/owl2/
- **OWL 2 DL Profile**: https://www.w3.org/TR/owl2-profiles/#OWL_2_DL
- **Semantic Web Best Practices**: https://www.w3.org/TR/swbp-skos-core/
- **RDF Concepts**: https://www.w3.org/TR/rdf11-concepts/
- **Protégé Ontology Editor**: https://protege.stanford.edu/

---

## Implementation Guidelines

When extending COMET, follow these OWL 2 DL rules:

1. **Define classes with `owl:Class`**
   ```turtle
   comet:Product a owl:Class .
   ```

2. **Use inheritance, not properties, for classification**
   ```turtle
   # DO THIS:
   rs:SteelProduct rdfs:subClassOf comet:Product .
   
   # NOT THIS:
   ?product comet:type "steel" .
   ```

3. **Define properties clearly**
   ```turtle
   comet:hasSupplier a owl:ObjectProperty ;
     rdfs:domain comet:Company ;
     rdfs:range comet:Supplier ;
     owl:inverseOf comet:suppliedBy .
   ```

4. **Validate with Protégé or owltools**
   ```bash
   owltools my-extension.ttl --validate-owl
   ```

5. **Use SHACL for validation** (see ADR-006)
   ```turtle
   comet:ProductShape a sh:NodeShape ;
     sh:targetClass comet:Product ;
     sh:property [ sh:path comet:weight ; sh:minCount 1 ] .
   ```

---

## Maintenance

OWL 2 DL compliance is checked in CI/CD:
- Every PR runs `owltools --validate-owl`
- Failing builds prevent merge
- Regular review of spec updates from W3C
