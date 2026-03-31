# ADR-006: SHACL Alongside OWL

**Status**: Accepted

**Date**: 2026-03-15

---

## Context

COMET uses OWL 2 to define the ontology structure (classes, properties, inheritance). However, OWL has limitations for quality control:

1. **OWL cannot express certain constraints**:
   - "This property must have at least 1 value" (cardinality)
   - "These two properties cannot both be present" (disjointness)
   - "This string must match a regex pattern" (pattern validation)
   - "This URI must resolve to specific class" (class restriction)

2. **OWL reasoning is complex**:
   - Inference happens implicitly
   - Difficult to debug validation failures
   - Performance overhead for large datasets
   - Not suitable for data validation pipelines

3. **Different communities use different tools**:
   - Ontology experts use OWL + Protégé
   - Data engineers use JSON Schema, SQL constraints
   - Quality assurance uses validation frameworks

COMET needed both semantic expressiveness (OWL) and practical validation (SHACL).

---

## Decision

**COMET uses OWL 2 for ontology structure and SHACL for data validation.**

### Clear Separation of Concerns

| Aspect | OWL 2 | SHACL |
|--------|-------|-------|
| **Purpose** | Define concepts and relationships | Validate instance data |
| **Level** | Schema (T-Box) | Data (A-Box) |
| **Used by** | Ontologists, knowledge engineers | Data engineers, quality assurance |
| **Tools** | Protégé, owltools | pySHACL, SHACL validator |
| **Reasoning** | Implicit inference | Explicit constraint checking |

### Ontology Files

```
comet-core.ttl          ← OWL 2 DL ontology
comet-shapes.ttl        ← SHACL validation

ext/responsiblesteel/ontology.ttl    ← OWL 2 DL ontology
ext/responsiblesteel/shapes.ttl      ← SHACL validation
```

### Example

**OWL 2 (structure)**:
```turtle
comet:Product a owl:Class ;
  rdfs:label "Product" ;
  rdfs:comment "Any product in supply chain" .

comet:weight a owl:DatatypeProperty ;
  rdfs:domain comet:Product ;
  rdfs:range xsd:decimal ;
  rdfs:label "weight" .
```

**SHACL (validation)**:
```turtle
comet:ProductShape a sh:NodeShape ;
  sh:targetClass comet:Product ;
  sh:property [
    sh:path comet:weight ;
    sh:minCount 1 ;          ← OWL can't express this
    sh:datatype xsd:decimal ;
    sh:minInclusive 0 ;      ← OWL can't express this
    sh:message "Weight required and must be >= 0"@en ;
  ] .
```

### Usage

**1. Design with OWL**:
   - Define classes and properties
   - Establish inheritance hierarchy
   - Create semantic relationships

**2. Validate with SHACL**:
   - Create NodeShapes for key classes
   - Define property constraints
   - Enforce value ranges and patterns
   - Check cardinality and relationships

**3. Run validation**:
   ```bash
   # Validate RDF instance data against shapes
   comet validate --data my-data.ttl --shapes comet-shapes.ttl
   ```

---

## Consequences

### Positive

1. **Complementary Strengths**: Each language does what it does best
   - OWL for semantic expressiveness
   - SHACL for practical validation
   - Together: complete quality framework

2. **Familiar to Communities**: 
   - Ontologists: OWL 2 is standard
   - Data engineers: SHACL like JSON Schema
   - Both communities comfortable

3. **Performance**: Separates inference from validation
   - OWL reasoning only when needed
   - SHACL validation fast for data quality
   - Can choose when to invoke which

4. **Debuggability**: SHACL validation reports are clear
   - Identifies exact constraint violated
   - Points to specific triple/value
   - Actionable error messages
   - Much better than OWL inference debugging

5. **Standards-aligned**: 
   - OWL: W3C standard for ontologies
   - SHACL: W3C standard for validation
   - Both widely supported
   - Future-proof approach

6. **Integration with Data Pipelines**: SHACL fits naturally into ETL
   - Validation as explicit step
   - Can reject invalid data
   - Better error handling
   - Suitable for automated systems

### Negative

1. **Complexity**: Two languages instead of one
   - More to learn
   - More files to maintain
   - Potential duplication (same concepts in OWL and SHACL)
   - Coordination needed between them

2. **Maintenance Burden**: OWL and SHACL can diverge
   - If class changes in OWL, must update SHACL
   - Easy to get out of sync
   - Requires discipline

3. **Redundancy**: Some information repeated
   - Class definition in OWL
   - Class shape in SHACL
   - Both express cardinality/type constraints

4. **Learning Curve**: SHACL is newer and less familiar
   - SHACL adoption slower than OWL
   - Fewer tutorials and examples
   - Smaller community

### Neutral

1. **SHACL interpretation**: Validation results are "closed world"
   - SHACL assumes what's present is all that should be present
   - OWL assumes missing properties might be inferred
   - Different mindsets, both valid

---

## Alternatives Considered

### Alternative 1: OWL Alone (OWL Restrictions)

**Approach**: Use only OWL, with complex owl:allValuesFrom, owl:cardinality

**Pros**:
- Single language
- Simpler conceptually

**Cons**:
- OWL cardinality restrictions are complex and limited
- Cannot express patterns, ranges, detailed constraints
- Performance overhead for validation
- Error messages unhelpful
- Not designed for data quality pipelines

### Alternative 2: SHACL Alone

**Approach**: Skip OWL, use only SHACL for everything

**Pros**:
- Single language
- Good for validation

**Cons**:
- SHACL not designed for ontology definition
- Loses semantic expressiveness
- No reasoning capabilities
- Can't use OWL tools (Protégé, reasoners)
- Not suitable for semantic web integration

### Alternative 3: Schematron (ISO/IEC 19757-3)

**Approach**: Use Schematron for validation instead of SHACL

**Pros**:
- Older standard, some tools
- XPath-based (familiar to XML developers)

**Cons**:
- Designed for XML, not RDF
- Not part of semantic web standards
- Less RDF-aware
- Smaller adoption in linked data community

### Alternative 4: JSON Schema (for JSON-LD serialization)

**Approach**: Provide JSON Schema for JSON-LD version of data

**Pros**:
- Familiar to web developers
- Good tool support
- Works with JSON-LD context

**Cons**:
- Only covers JSON serialization
- Doesn't help with RDF/Turtle
- Adds complexity (multiple validation languages)
- Not semantic-web native

---

## Design Patterns

### Pattern 1: Complete Coverage

Every core class has corresponding shape:

```turtle
# OWL definition
comet:Product a owl:Class .

# SHACL validation
comet:ProductShape a sh:NodeShape ;
  sh:targetClass comet:Product ;
  sh:property [ ... ] .
```

**Rule**: All core classes must have shapes.

### Pattern 2: Constraint Escalation

Some constraints only in SHACL:

```turtle
# OWL: permissive (accept the structure)
comet:emissionsFactor a owl:DatatypeProperty ;
  rdfs:domain comet:Product ;
  rdfs:range xsd:decimal .

# SHACL: strict (enforce quality)
[ sh:path comet:emissionsFactor ;
  sh:minCount 1 ;              ← Must be present
  sh:minInclusive 0 ;          ← Must be >= 0
  sh:maxInclusive 1000 ;       ← Must be <= 1000
  sh:message "..." ]
```

### Pattern 3: Domain-specific Shapes

Extensions add tighter SHACL shapes:

```turtle
# Core shape: loose
comet:ProductShape a sh:NodeShape ;
  sh:targetClass comet:Product ;
  sh:property [ sh:path comet:weight ; sh:minCount 0 ] .

# Extension shape: tight
rs:SteelProductShape a sh:NodeShape ;
  sh:targetClass rs:SteelProduct ;
  sh:property [ sh:path comet:weight ; sh:minCount 1 ] .
```

---

## Implementation Guidelines

### 1. Write OWL First

Start with ontology design (classes, properties):

```turtle
@prefix comet: <https://comet.carbon/ontology/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

comet:Product
  a owl:Class ;
  rdfs:label "Product"@en ;
  rdfs:comment "Any product or material in the supply chain" .

comet:weight
  a owl:DatatypeProperty ;
  rdfs:domain comet:Product ;
  rdfs:range xsd:decimal ;
  rdfs:label "weight"@en .
```

### 2. Define Shapes Next

Add validation constraints:

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .

comet:ProductShape
  a sh:NodeShape ;
  sh:targetClass comet:Product ;
  sh:property [
    sh:path comet:weight ;
    sh:minCount 1 ;
    sh:datatype xsd:decimal ;
    sh:minInclusive 0 ;
    sh:message "Product must have weight >= 0 kg" ;
  ] ;
  sh:property [
    sh:path comet:label ;
    sh:minCount 1 ;
    sh:datatype xsd:string ;
    sh:message "Product must have a label" ;
  ] .
```

### 3. Test Data Against Shapes

```bash
comet validate --data instance-data.ttl --shapes comet-shapes.ttl
```

### 4. Iterate

If validation failures reveal issues:
- Tighten shapes if data quality needs it
- Relax shapes if constraints are too strict
- Update OWL if semantics need clarifying

---

## Validation Pipeline

```
RDF Instance Data
       ↓
   SHACL Validation
       ↓
   ┌─────────┐
   │ Valid?  │
   └────┬────┘
        ├─→ Yes → Accept data
        │
        └─→ No → Generate report
             ├─ Constraint violated
             ├─ Specific triple/value
             ├─ Suggested fix
             └─ Reject data
```

---

## Related Decisions

- **ADR-002**: OWL 2 over RDFS (provides structure for SHACL to validate)
- **ADR-003**: Extension module pattern (extensions include SHACL shapes)

---

## References

- **SHACL Specification**: https://www.w3.org/TR/shacl/
- **SHACL Best Practices**: https://www.w3.org/TR/shacl-ucr/
- **pySHACL Validator**: https://github.com/RDFLib/pySHACL
- **OWL and SHACL Together**: https://www.w3.org/TR/owl2-overview/
- **Semantic Web Validation**: https://www.w3.org/2011/prov/

---

## Tools Integration

**Recommended toolchain**:

1. **Protégé**: Design OWL ontology visually
2. **pySHACL**: Validate RDF data (Python)
3. **owltools**: Check OWL 2 DL compliance
4. **SHACL Playground**: Interactive SHACL development
5. **CI/CD**: Automated validation in GitHub Actions

See [Getting Started](../getting-started.md) for installation instructions.
