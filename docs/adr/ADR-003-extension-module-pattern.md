# ADR-003: Extension Module Pattern

**Status**: Accepted

**Date**: 2026-03-15

---

## Context

COMET is designed as a general ontology for carbon accounting, but real-world carbon tracking is highly domain-specific. Steel supply chains differ fundamentally from textile supply chains, which differ from automotive. However, all these domains share common concepts: products, processes, emissions, certifications.

Early attempts to build everything into core COMET created:
- Bloated ontology with 500+ classes
- Unclear separation of concerns
- Difficult maintenance (changing steel stuff broke textile stuff)
- Impossible to provide domain-specific SHACL shapes
- No clear extension path for standards bodies

We needed a modular approach.

---

## Decision

**COMET adopts an extension module pattern where domain-specific concepts are defined in separate, well-governed ontology files.**

### Structure

```
comet/
  comet-core.ttl           # General concepts (Product, Process, etc.)
  comet-shapes.ttl         # Core validation
  
  ext/responsiblesteel/    # Steel domain extension
    ontology.ttl          # Steel-specific classes
    shapes.ttl            # Steel validation rules
    examples.ttl          # Steel instance data
    labels-*.ttl          # Translations
    
  ext/textiles/           # Textile extension (future)
    ontology.ttl
    shapes.ttl
    ...
```

### Module Composition

Extensions are **OWL imports** of core:

```turtle
# ext/responsiblesteel/ontology.ttl
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix comet: <https://comet.carbon/ontology/> .

# Import core ontology
<https://comet.carbon/ontology/responsiblesteel/>
  owl:imports <https://comet.carbon/ontology/> .

# Define extension classes (extend core via rdfs:subClassOf)
rs:SteelProduct rdfs:subClassOf comet:Product .
rs:SteelGrade rdfs:subClassOf comet:Material .
```

### Key Properties

1. **Self-contained**: Extension can stand alone but works better with core
2. **Non-invasive**: Doesn't modify core classes
3. **Discoverable**: Clear namespace and documentation
4. **Governed**: Follows lifecycle (RFC → Draft → Stable)
5. **Versionable**: Separate version from core

---

## Lifecycle

Each extension progresses through stages:

| Stage | Status | Audience | Support |
|-------|--------|----------|---------|
| **RFC** | Proposal | Community feedback | Proposal owner |
| **Draft** | Beta | Early adopters | Best-effort |
| **Stable** | Production | General use | Committed |
| **Deprecated** | Superseded | Migration path | 6-month notice |
| **Retired** | Archived | Historical reference | None |

See [GOVERNANCE.md](../../GOVERNANCE.md) and [CONTRIBUTING.md](../../CONTRIBUTING.md) for detailed process.

---

## Consequences

### Positive

1. **Modularity**: Use only what you need
   - Load core for general tracking
   - Add steel extension for steel supply chains
   - Combine extensions if needed

2. **Clear Scope**: Each extension owns its domain
   - Steel expert maintains steel extension
   - Textile expert maintains textile extension
   - Separation of concerns

3. **Governance**: Extensions have clear lifecycle and review process
   - Prevents low-quality code
   - Ensures standards alignment
   - Community input before promotion

4. **Maintainability**: Core doesn't bloat with domain-specific code
   - Core stays stable
   - Core can be released independently
   - Easier to find what you're looking for

5. **Standards Alignment**: Extensions can target specific standards
   - ResponsibleSteel extension aligns with ResponsibleSteel standard
   - PACT extension aligns with PACT standard
   - Easier to achieve compliance

6. **Parallel Development**: Teams can work independently
   - Steel team doesn't wait for textile team
   - Release cadence decoupled
   - Faster time to value

### Negative

1. **Coordination Required**: Managing multiple modules is harder than single file
   - Need version coordination between core and extensions
   - Breaking changes in core affect extensions
   - Documentation must cover integration

2. **Complexity for Users**: "Which extension do I need?" questions
   - Requires discovery and documentation
   - May need multiple extensions (e.g., steel + renewable energy)
   - Initial setup is more complex than flat ontology

3. **Dependency Management**: Extensions depend on core
   - Breaking changes in core break extensions
   - Version mismatch errors possible
   - Backward compatibility burden

4. **Testing Burden**: Each extension must validate independently
   - Extension A might be valid, but break when combined with extension B
   - Cross-extension testing required
   - More complex CI/CD

### Neutral

1. **Performance Trade-off**: Modular design may increase query complexity
   - More files to load
   - More namespace prefixes to manage
   - Performance acceptable for typical use cases

---

## Alternatives Considered

### Alternative 1: Single Monolithic Ontology

**Approach**: Everything in one comet.ttl file

**Pros**:
- Simple to understand and use
- Single version number
- No dependency management

**Cons**:
- Bloated (500+ classes)
- Unclear separation
- Difficult for domain experts to contribute
- Mixing of concerns

### Alternative 2: Separate Ontologies with No Integration

**Approach**: Each domain has its own independent ontology (steel.ttl, textiles.ttl)

**Pros**:
- Complete independence
- No version coupling

**Cons**:
- No interoperability between domains
- Duplicated common concepts
- Impossible to combine steel+textile data
- Defeats purpose of shared ontology

### Alternative 3: Plugin Architecture with Semantic Protocols

**Approach**: Loose coupling via interfaces/protocols

**Pros**:
- Maximum flexibility
- Can add extensions dynamically

**Cons**:
- Requires external coordination mechanism
- Hard to understand what's available
- Difficult to ensure compatibility
- Too complex for typical use cases

---

## Design Rules

Extensions must follow these rules:

1. **Use semantic imports**: `owl:imports` for loading core
2. **Never modify core**: Extend via `rdfs:subClassOf`, not modification
3. **Clear namespaces**: Use distinct URIs for extension classes
4. **SHACL shapes**: Provide validation specific to extension
5. **Comprehensive examples**: At least 3 worked examples
6. **Translations**: English + 2+ additional languages
7. **Documentation**: Clear README explaining domain and usage

### Template

```turtle
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix comet: <https://comet.carbon/ontology/> .
@prefix myext: <https://comet.carbon/ontology/my-extension/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

# 1. Import core
<https://comet.carbon/ontology/my-extension/>
  owl:imports <https://comet.carbon/ontology/> ;
  owl:versionInfo "0.1.0" ;
  rdfs:label "My Extension"@en .

# 2. Extend core classes
myext:MyClass
  rdfs:subClassOf comet:Product ;
  rdfs:label "My Specialized Class"@en ;
  rdfs:comment "A domain-specific type of product" .

# 3. Define extension properties
myext:myProperty
  a owl:ObjectProperty ;
  rdfs:domain myext:MyClass ;
  rdfs:range comet:Material ;
  rdfs:label "my property"@en .
```

---

## Related Decisions

- **ADR-001**: Seven-layer stack (provides extension attachment points)
- **ADR-006**: SHACL alongside OWL (extensions include SHACL shapes)

---

## References

- **OWL Imports**: https://www.w3.org/TR/owl2-syntax/#Ontology_IRI_and_Version_IRI
- **Modular Ontology Design**: https://github.com/cmungall/obo-dashboard/blob/master/Modular%20Ontology%20Design.md
- **ROBOT Tool**: http://robot.obolibrary.org/ (for managing modular ontologies)

---

## Migration Path

**Existing codebases moving from monolithic to modular**:

1. Export core concepts to `comet-core.ttl`
2. For each domain: create `ext/[domain]/ontology.ttl`
3. Replace domain-specific classes with imports
4. Update all references to use new namespaces
5. Test with Protégé and owltools
6. Update SPARQL queries to use new prefixes

Example:
```sparql
# Old
PREFIX comet: <https://comet.carbon/ontology/>
SELECT ?product WHERE {
  ?product a comet:SteelProduct .
}

# New
PREFIX comet: <https://comet.carbon/ontology/>
PREFIX rs: <https://comet.carbon/ontology/responsiblesteel/>
SELECT ?product WHERE {
  ?product a rs:SteelProduct .
}
```

---

## Governance Integration

Extension review process:

1. **RFC**: Proposal reviewed by Owner/Maintainers
2. **Draft**: Domain Expert assigned, 4-6 weeks review
3. **Stable**: Production use demonstrated
4. **Deprecated**: 6-month notice period
5. **Retired**: Archived on Zenodo

See [CONTRIBUTING.md](../../CONTRIBUTING.md#extension-submission-process) for full process.
