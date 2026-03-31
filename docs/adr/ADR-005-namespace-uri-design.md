# ADR-005: Namespace URI Design

**Status**: Accepted

**Date**: 2026-03-15

---

## Context

COMET, as a semantic web ontology, assigns URIs (Uniform Resource Identifiers) to all concepts. These URIs serve multiple purposes:

1. **Global uniqueness**: Two systems won't accidentally define the same concept
2. **Linked data**: Enable RDF triple linking between different datasets
3. **Versioning**: Track ontology changes over time
4. **HTTP resolution**: Potentially dereference to documentation
5. **Authoritatively**: Establish who maintains this concept

Choosing URI structure is critical because:
- URIs are permanent (changing them breaks all data using them)
- URIs must be internationally unique
- URIs should be meaningful and stable
- URIs affect how data is discovered and integrated

---

## Decision

**COMET uses the namespace URI: `https://comet.carbon/ontology/`**

### Structure

```
Core ontology:
  https://comet.carbon/ontology/
  https://comet.carbon/ontology/Product
  https://comet.carbon/ontology/Process
  https://comet.carbon/ontology/Certification
  ... (all core classes and properties)

ResponsibleSteel extension:
  https://comet.carbon/ontology/responsiblesteel/
  https://comet.carbon/ontology/responsiblesteel/SteelProduct
  https://comet.carbon/ontology/responsiblesteel/SteelGrade
  https://comet.carbon/ontology/responsiblesteel/steelGrade
  ... (all RS extension concepts)

Future extensions:
  https://comet.carbon/ontology/textiles/
  https://comet.carbon/ontology/automotive/
  ... (each with unique namespace)
```

### Prefix Usage

In Turtle files:

```turtle
@prefix comet: <https://comet.carbon/ontology/> .
@prefix rs: <https://comet.carbon/ontology/responsiblesteel/> .

comet:Product a owl:Class .
rs:SteelProduct rdfs:subClassOf comet:Product .
```

### Why This Design?

1. **Domain ownership**: `comet.carbon` establishes COMET authority
2. **Path structure**: `/ontology/` separates from other COMET resources
3. **Version-agnostic**: Namespace doesn't include version (0.2.0)
   - Same namespace across all versions
   - Avoids breaking data with version changes
4. **Extension hierarchy**: Extensions nest under main namespace
   - Clear relationship to core
   - Discoverable structure
5. **HTTP resolvable**: Can dereference to documentation
   - `https://comet.carbon/ontology/Product` → documentation page
   - Follows linked data best practices

---

## Consequences

### Positive

1. **Globally Unique**: Uses registered domain `comet.carbon`
   - No conflicts with other ontologies
   - Permanent authority establishment
   - Reduces namespace collisions

2. **Version-stable**: Namespace doesn't change between versions
   - COMET 0.1.0 and 0.2.0 use same URIs
   - Data doesn't become invalid with upgrades
   - Clean versioning story

3. **Extension-friendly**: Clear namespace hierarchy for extensions
   - Each extension gets distinct namespace
   - Can be discovered via URL pattern
   - No ambiguity about ownership

4. **Documentation-friendly**: Namespace can resolve to docs
   - `https://comet.carbon/ontology/Product` → Product class docs
   - Supports linked data dereferencing
   - Human-readable while machine-parseable

5. **Alignment with W3C Practices**: Follows semantic web best practices
   - Similar to `https://xmlns.com/` (FOAF)
   - Similar to `http://purl.org/` (PURL)
   - Recognized pattern in linked data community

### Negative

1. **Domain Dependency**: Requires stable `comet.carbon` domain
   - If domain expires, namespace URIs broken
   - Architectural risk if organization changes
   - Mitigation: Permanent registration, Zenodo archival

2. **HTTP Resolution Not Automatic**: URIs don't automatically resolve
   - Requires web server setup
   - Additional infrastructure overhead
   - Not all systems dereference URIs

3. **Extension Coordination**: Extensions must register their namespace
   - Central approval process required
   - Prevents ad-hoc extensions under different domains
   - Coordination overhead

### Neutral

1. **Length**: Full URIs are verbose in SPARQL
   - Mitigated by prefixes (`@prefix comet:`)
   - Standard practice in semantic web
   - Not a real problem in practice

---

## Alternatives Considered

### Alternative 1: Version-specific namespaces

**Approach**: `https://comet.carbon/ontology/0.2.0/`

**Pros**:
- Clear version in URI
- Different versions can coexist

**Cons**:
- Breaking change: old data refers to 0.1.0 namespace, new data to 0.2.0
- Proliferation of namespaces
- Complex version migration
- Defeats interoperability goal

### Alternative 2: Organization domain prefix

**Approach**: `https://comet.carbon/ontology/comet/product` (includes "comet" twice)

**Pros**:
- Follows some ontology conventions

**Cons**:
- Redundant ("comet" appears twice)
- Less clean
- Unnecessary complexity

### Alternative 3: URN-based identifiers

**Approach**: `urn:comet:ontology:Product`

**Pros**:
- Doesn't depend on HTTP domain
- More permanent

**Cons**:
- Not resolvable to documentation
- Less discoverable
- Not linked data friendly
- No standard registration authority

### Alternative 4: GitHub raw content URIs

**Approach**: `https://raw.githubusercontent.com/comet-ontology/comet/main/comet.ttl#Product`

**Pros**:
- Uses GitHub infrastructure
- Clear version control

**Cons**:
- Depends on GitHub (business risk)
- Version-specific (GitHub branch)
- Not appropriate for stable reference
- Too volatile for persistent URIs

### Alternative 5: Decentralized (local) namespaces

**Approach**: Let each organization use their own namespace

**Pros**:
- No coordination required
- Full independence

**Cons**:
- No interoperability
- Defeats ontology purpose
- Data can't be shared
- Different organizations define "Product" differently

---

## Implementation

### HTTP Resolution Setup

While not yet implemented, `https://comet.carbon/ontology/Product` can resolve to:

```
HTTP GET https://comet.carbon/ontology/Product
Accept: text/html

Response: 302 Found
Location: https://comet.carbon/docs/classes/product.html
```

This requires:
1. Web server at `comet.carbon`
2. Content negotiation setup
3. Redirect rules

### In RDF Files

```turtle
@prefix comet: <https://comet.carbon/ontology/> .

comet:Product
  a owl:Class ;
  rdfs:label "Product"@en ;
  rdfs:isDefinedBy <https://comet.carbon/ontology/> ;
  rdfs:seeAlso <https://comet.carbon/docs/product> .
```

### In SPARQL Queries

```sparql
PREFIX comet: <https://comet.carbon/ontology/>

SELECT ?product WHERE {
  ?product a comet:Product .
}
```

### In Applications

```python
from rdflib import Namespace

COMET = Namespace("https://comet.carbon/ontology/")
RS = Namespace("https://comet.carbon/ontology/responsiblesteel/")

# Use like:
subject = COMET.Product
predicate = COMET.hasWeight
object_prop = RS.SteelProduct
```

---

## Extension Namespace Allocation

Extensions register their namespace:

| Extension | Namespace |
|-----------|-----------|
| ResponsibleSteel | `https://comet.carbon/ontology/responsiblesteel/` |
| Textiles (planned) | `https://comet.carbon/ontology/textiles/` |
| Automotive (planned) | `https://comet.carbon/ontology/automotive/` |
| Custom user extension | Cannot use comet.carbon domain (must use own domain) |

**Rules**:
1. Standard body extensions use `comet.carbon` namespace
2. Private/organizational extensions use their own domain
3. Community extensions can request `comet.carbon` namespace (requires approval)

---

## Stability Commitments

COMET commits to:

1. **Permanent URIs**: All COMET namespace URIs are permanent
   - No removal once published
   - Deprecated classes stay but marked obsolete
   - Version 1.0 and forward: strict backward compatibility

2. **Zenodo Archival**: All COMET releases archived
   - Permanent DOI for each version
   - Available even if comet.carbon goes offline
   - Citation-enabled

3. **Domain Continuity**: 
   - Domain registered for 10+ years
   - Renewal automated
   - Disaster recovery plan in place

---

## Related Decisions

- **ADR-004**: Dual licensing (CC BY 4.0 affects permanence expectations)
- **ADR-002**: OWL 2 (requires proper RDF namespace handling)

---

## References

- **W3C Namespace Best Practices**: https://www.w3.org/TR/curie/#BNF
- **Linked Data Dereferencing**: https://www.w3.org/DesignIssues/LinkedData.html
- **PURL Permanent URLs**: https://purl.org/
- **Zenodo Archival**: https://zenodo.org/
- **OWL namespace URIs**: https://www.w3.org/TR/owl2-syntax/#Ontology_IRI_and_Version_IRI

---

## Maintenance

Namespace stability is enforced:

1. **CI checks**: Never allow namespace URIs to change
2. **CHANGELOG tracking**: Document all new namespace additions
3. **Versioning**: Only extend namespaces, never modify
4. **Archival**: Zenodo maintains permanent copies

---

## Future Considerations

If COMET evolves to version 2.0:

Option A: Keep namespace, version in metadata
```
https://comet.carbon/ontology/Product (same URI for 1.0 and 2.0)
dc:issued "2026-03-30" (for 0.2.0)
dc:issued "2030-03-30" (for 2.0.0)
```

Option B: Create new namespace only if semantics change
```
https://comet.carbon/ontology/Product (unchanged in meaning)
https://comet.carbon/ontology/v2/SpecialProduct (new concept)
```

Decision deferred until approach to 2.0 is clear.
