# COMET Extension Cookbook

This guide walks you through creating a standards-aligned extension for COMET. We'll use the ResponsibleSteel extension as a worked example.

## Overview

A COMET extension specializes the ontology for a specific domain (steel, textiles, automotive, etc.). Extensions follow a standard pattern to ensure compatibility and quality.

**Time estimate**: 4-6 weeks from RFC to Stable

**Deliverables**:
- Ontology file (OWL/RDF)
- SHACL validation shapes
- Example instance data
- Multilingual labels
- Documentation
- Use case demonstration

---

## Step 1: Gather Requirements (1-2 weeks)

### 1.1 Inventory Domain Concepts

List all concepts you need to represent. For steel, this includes:

**Entities**:
- Steel products (coils, plates, sections)
- Steel grades (HSLA, mild, stainless)
- Manufacturing processes (rolling, heat treatment)
- Certifications (ResponsibleSteel, ISO 14001)

**Attributes**:
- Steel grade / alloy composition
- Thickness, width, surface finish
- Heat treatment conditions
- Certification status

**Relationships**:
- Product uses steel grade
- Product undergoes process
- Product has certification
- Supplier produces product

### 1.2 Map to COMET Core

Identify which core COMET classes and properties your concepts align with:

| Domain Concept | COMET Class | COMET Property |
|---|---|---|
| Steel Product | Product | - |
| Steel Grade | Material | - |
| Rolling Process | Process | - |
| Certification | Certification | hasCertification |
| Emissions Value | Emission | emissionsValue |

### 1.3 Identify New Concepts

Concepts not in COMET core will become new classes/properties in your extension:

- `SteelGrade` (specializes Material)
- `HeatTreatment` (specializes Process)
- `SteelProduct` (specializes Product)
- `steelGrade` (object property)
- `alloyComposition` (data property)

### 1.4 Check External Standards

Align with relevant standards:
- **ResponsibleSteel Standard**: Defines responsible sourcing criteria
- **ISO 14001**: Environmental management system
- **EN standards**: European steel grades and specifications
- **ASTM standards**: American Society for Testing and Materials

---

## Step 2: File RFC (1-2 weeks)

### 2.1 Prepare RFC Document

Create a GitHub issue or Discussion with title: `RFC: [Domain] Extension for COMET`

**Template**:
```markdown
## Proposal

Create a COMET extension for [Domain Name].

## Motivation

Why is this domain important? What problems does it solve?

## Scope

Core concepts to include:
- Class 1
- Class 2
- Property 1
- Property 2

## Alignment

Relevant standards:
- Standard 1
- Standard 2

## Example Use Case

Scenario where this extension would be used...

## Expected Timeline

4-6 weeks to Draft stage
```

### 2.2 Gather Feedback

Give community 2 weeks to comment. Address questions about:
- Necessity (is this the right scope?)
- Alignment (conflicts with other extensions?)
- Technical feasibility

### 2.3 RFC Acceptance

If feedback is positive and no major concerns:
- **Owner/Maintainer** approves → Move to Draft stage
- Assign a **Domain Expert** reviewer (if available in field)

---

## Step 3: Build Extension (3-4 weeks)

### 3.1 Create Ontology File

Structure your extension in `ext/[domain]/ontology.ttl`:

```turtle
@prefix comet: <https://comet.carbon/ontology/> .
@prefix rs: <https://comet.carbon/ontology/responsiblesteel/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# Define base class specializing COMET Product
rs:SteelProduct
  rdfs:subClassOf comet:Product ;
  rdfs:label "Steel Product"@en ;
  rdfs:label "Acier Product"@fr ;
  rdfs:comment "A steel product that has undergone transformation" .

# Define a new domain property
rs:steelGrade
  a owl:ObjectProperty ;
  rdfs:domain rs:SteelProduct ;
  rdfs:range rs:SteelGrade ;
  rdfs:label "steel grade"@en ;
  rdfs:comment "The grade or specification of steel" .

# Define referenced class
rs:SteelGrade
  rdfs:subClassOf comet:Material ;
  rdfs:label "Steel Grade"@en ;
  rdfs:comment "A specific grade or specification of steel" .

# Data property
rs:alloyComposition
  a owl:DatatypeProperty ;
  rdfs:domain rs:SteelGrade ;
  rdfs:range xsd:string ;
  rdfs:label "alloy composition"@en .
```

**Guidelines**:
- Use descriptive labels and comments
- Follow OWL 2 DL profile (ensures good tool support)
- Reuse COMET classes when possible
- Define only new concepts

### 3.2 Create SHACL Shapes

Create `ext/[domain]/shapes.ttl` for validation:

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix rs: <https://comet.carbon/ontology/responsiblesteel/> .
@prefix comet: <https://comet.carbon/ontology/> .

# Validate SteelProduct instances
rs:SteelProductShape
  a sh:NodeShape ;
  sh:targetClass rs:SteelProduct ;
  sh:property [
    sh:path rs:steelGrade ;
    sh:minCount 1 ;
    sh:message "Each SteelProduct must have a steelGrade"@en ;
  ] ;
  sh:property [
    sh:path comet:weight ;
    sh:minCount 1 ;
    sh:datatype xsd:decimal ;
    sh:message "Weight must be a decimal number"@en ;
  ] .
```

**Best practices**:
- Validate required properties
- Enforce data types and ranges
- Check cardinality constraints
- Provide clear error messages

### 3.3 Create Example Data

Create `ext/[domain]/examples.ttl` with 3-5 realistic instances:

```turtle
@prefix comet: <https://comet.carbon/ontology/> .
@prefix rs: <https://comet.carbon/ontology/responsiblesteel/> .
@prefix ex: <https://example.com/responsiblesteel/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# Example 1: Cold-rolled steel coil
ex:SteelCoil001
  a rs:SteelProduct ;
  rdfs:label "Cold-rolled HSLA coil"@en ;
  rs:steelGrade ex:HSLA ;
  comet:weight "1000"^^xsd:decimal ;
  comet:weightUnit comet:Kilogram ;
  comet:emissionsFactor "2.1"^^xsd:decimal ;
  comet:emissionsFactorUnit comet:kgCO2ePerKg ;
  comet:hasCertification ex:ResponsibleSteel2024 ;
  comet:hasSupplier ex:ArcelorMittal .

# Example 2: Steel grade definition
ex:HSLA
  a rs:SteelGrade ;
  rdfs:label "High Strength Low Alloy Steel"@en ;
  rs:alloyComposition "Fe-C-Mn-Si-Nb-V"@en ;
  comet:emissionsFactor "2.1"^^xsd:decimal .

# Example 3: Data with multiple certifications
ex:PremiumSteel
  a rs:SteelProduct ;
  rdfs:label "Premium certified steel"@en ;
  rs:steelGrade ex:StainlessSteel ;
  comet:weight "500"^^xsd:decimal ;
  comet:hasCertification ex:ISO14001, ex:ResponsibleSteel2024 .
```

**Requirements**:
- At least 3 complete examples
- Demonstrate all key concepts
- Include valid data (will validate with SHACL)
- Cover different use cases

### 3.4 Create Translations

Add labels in at least 3 languages: `ext/[domain]/labels-[lang].ttl`

```turtle
# labels-es.ttl (Spanish)
@prefix rs: <https://comet.carbon/ontology/responsiblesteel/> .

rs:SteelProduct rdfs:label "Producto de Acero"@es .
rs:steelGrade rdfs:label "grado de acero"@es .
rs:alloyComposition rdfs:label "composición de aleación"@es .
```

**Language support** (prioritized):
1. English (always required)
2. Spanish, German, French, Mandarin (high priority)
3. Portuguese, Japanese, Italian, Dutch, Swedish (nice-to-have)

---

## Step 4: Create Documentation

### 4.1 Extension README

Create `ext/[domain]/README.md`:

```markdown
# ResponsibleSteel Extension

COMET extension for tracking responsible steel production and emissions.

## Overview

This extension specializes COMET's core Product and Process classes for steel supply chains.

## Classes

- `SteelProduct`: A steel product with grade and properties
- `SteelGrade`: A specific steel specification
- `SteelProcess`: Manufacturing process for steel

## Properties

Object properties:
- `steelGrade`: The grade of a steel product

Data properties:
- `alloyComposition`: Chemical composition of steel

## Example

[Include worked example showing a complete instance]

## Standards Alignment

- ResponsibleSteel Standard v2.0
- ISO 14001:2015
- EN 10020 (Classification system for steel)

## See Also

- [COMET Core Ontology](../../)
- [Extension Creation Guide](../../docs/creating-extensions.md)
```

### 4.2 Use Case Documentation

Create `ext/[domain]/use-cases.md` with 2-3 business scenarios:

**Use Case 1: Emissions Calculation**
- **Actor**: Steel manufacturer
- **Goal**: Calculate scope 1 emissions for production
- **Scenario**: [Step-by-step description]

---

## Step 5: Submit Draft PR (1-2 weeks review)

### 5.1 Organize Files

```
ext/responsiblesteel/
  ontology.ttl          # Core ontology
  shapes.ttl            # SHACL validation shapes
  examples.ttl          # Example instance data
  labels-*.ttl          # Translations
  README.md             # Extension documentation
  use-cases.md          # Business scenarios
  alignment.ttl         # Alignment to standards
```

### 5.2 Create Pull Request

Title: `Draft: ResponsibleSteel Extension Module`

**Checklist**:
- [ ] Ontology file validates (OWL 2 DL)
- [ ] Examples validate against SHACL shapes
- [ ] Documentation complete
- [ ] 3+ languages supported
- [ ] Use cases documented
- [ ] No conflicts with core COMET

### 5.3 Address Review Feedback

Domain Expert will review for:
- **Correctness**: Does it accurately represent the domain?
- **Completeness**: Are all key concepts included?
- **Alignment**: Does it align with standards?
- **Quality**: Are examples clear? Are labels accurate?

Make requested changes and update PR.

---

## Step 6: Advance to Stable (1-2 weeks)

### 6.1 Production Validation

- Demonstrate production use (even pilot)
- Confirm no critical issues found
- Update maintenance plan

### 6.2 Stable PR

Title: `Promote: ResponsibleSteel → Stable`

Include:
- Link to production use case
- Updated CHANGELOG entry
- Commitment to maintenance

### 6.3 Release

Owner/Maintainer approves promotion:
- Version bump (e.g., 0.2.0 → 0.3.0)
- Announce in release notes
- Update documentation

---

## Maintenance Checklist

Once stable, maintain your extension:

### Quarterly

- [ ] Check for COMET core updates
- [ ] Review outstanding issues
- [ ] Update examples if needed

### Annually

- [ ] Review standards alignment (things change!)
- [ ] Consider new domain features
- [ ] Update documentation
- [ ] Refresh translations if available

### If Deprecating

- [ ] Post 6-month notice (issue + GitHub Discussions)
- [ ] Document migration path
- [ ] Archive on Zenodo
- [ ] Move to `retired/` directory

---

## Tips for Success

1. **Start small**: One core concept better than many half-baked ones
2. **Use examples**: Make sure they're realistic and runnable
3. **Test early**: Validate examples against shapes as you build
4. **Get feedback**: RFC phase is for gathering stakeholder input
5. **Document thoroughly**: Future maintainers will thank you
6. **Plan for maintenance**: Who will support this extension in 6 months?

---

## Template Extension

Starter template for your extension (copy and modify):

```turtle
@prefix comet: <https://comet.carbon/ontology/> .
@prefix myext: <https://comet.carbon/ontology/my-extension/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# TODO: Replace "myext" with your namespace
# TODO: Define your classes and properties
# TODO: Add RDFS labels in multiple languages
# TODO: Comment everything clearly

myext:MyClass
  rdfs:subClassOf comet:Product ;
  rdfs:label "My Class"@en ;
  rdfs:comment "Description of my class" .
```

---

## Questions?

- **Process**: See [CONTRIBUTING.md](../../CONTRIBUTING.md#creating-extensions)
- **Architecture**: See [ADR-003](../adr/ADR-003-extension-module-pattern.md)
- **Help**: File an issue or ask in discussions
- **Mentorship**: Request a Domain Expert mentor for your first extension

Good luck building your extension!
