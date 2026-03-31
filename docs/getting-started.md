# Getting Started with COMET in 5 Minutes

Welcome to COMET! This guide gets you up and running with the ontology in just a few minutes.

## Choose Your Path

### Path 1: Browser (Fastest)

Use the SPARQL playground to query COMET without installing anything.

**Go to**: https://sparql.comet.carbon/

**Try this query**:
```sparql
PREFIX comet: <https://comet.carbon/ontology/>

SELECT ?class ?label WHERE {
  ?class a owl:Class ;
         rdfs:label ?label ;
         rdfs:label "Emissions"@en .
} LIMIT 10
```

Click "Execute" to see results. No installation needed!

### Path 2: Python (Recommended for Development)

Install the COMET Python package to work with the ontology programmatically.

**Step 1: Install**
```bash
pip install comet-ontology
```

**Step 2: Load and query**
```python
from comet import load_ontology, sparql_query

# Load the ontology
onto = load_ontology('https://comet.carbon/ontology/0.2.0/comet.ttl')

# Query for all classes
results = sparql_query(onto, """
    PREFIX comet: <https://comet.carbon/ontology/>
    SELECT ?class WHERE {
        ?class a owl:Class .
    } LIMIT 5
""")

for row in results:
    print(row['class'])
```

**Step 3: Explore the schema**
```python
# Get all classes in a specific layer
emissions_classes = onto.get_classes(layer='calculation')

# Get properties of a class
product_class = onto['https://comet.carbon/ontology/Product']
for prop in product_class.properties():
    print(prop.label())
```

### Path 3: Command Line (CLI)

Query COMET directly from the terminal.

**Step 1: Install**
```bash
pip install comet-cli
```

**Step 2: Query**
```bash
# List all classes
comet schema classes

# Get class details
comet schema describe Product

# Run SPARQL query
comet query --file my-query.sparql
```

---

## Next Steps

### Learn the Basics (10 minutes)

1. **Understand the 7-layer architecture**:
   - Read [Architecture Decision Records - ADR-001](adr/ADR-001-seven-layer-stack.md)
   - Understand how data flows through layers

2. **See example data**:
   - Check out `examples/` directory for RDF instance data
   - Each example shows real-world emissions scenarios

3. **Run example SPARQL queries**:
   ```bash
   # Calculate total emissions for a product
   comet query --file examples/calculate-emissions.sparql
   
   # Find certified suppliers
   comet query --file examples/find-certified-suppliers.sparql
   ```

### Read Key Documentation (20 minutes)

- **[FAQ](faq.md)** - Quick answers to 20 common questions
- **[Architecture Overview](../docs/adr/ADR-001-seven-layer-stack.md)** - Understand the design
- **[Creating Extensions](creating-extensions.md)** - How to add your domain

### Set Up Your First Project (30 minutes)

**Scenario: Track emissions for a steel product**

**Step 1: Get the ResponsibleSteel extension**
```bash
comet extensions install responsiblesteel
```

**Step 2: Create instance data**
```turtle
@prefix comet: <https://comet.carbon/ontology/> .
@prefix rs: <https://comet.carbon/ontology/responsiblesteel/> .
@prefix ex: <https://example.com/supply/> .

ex:SteelCoil
  a rs:SteelProduct ;
  rdfs:label "Cold-rolled steel coil" ;
  comet:weight "1000"^^xsd:decimal ;
  comet:weightUnit comet:Kilogram ;
  comet:emissionsFactor "2.1"^^xsd:decimal ;
  comet:emissionsFactorUnit comet:kgCO2ePerKg ;
  rs:steelGrade "HSLA" ;
  rs:certifications ex:ISO14001 .
```

**Step 3: Validate with SHACL**
```bash
comet validate --data my-data.ttl --shapes comet-shapes.ttl
```

**Step 4: Query the results**
```sparql
PREFIX comet: <https://comet.carbon/ontology/>
PREFIX rs: <https://comet.carbon/ontology/responsiblesteel/>
PREFIX ex: <https://example.com/supply/>

SELECT ?product ?weight ?emissionsFactor ?totalEmissions WHERE {
  ?product a rs:SteelProduct ;
           comet:weight ?weight ;
           comet:emissionsFactor ?emissionsFactor .
  
  BIND(?weight * ?emissionsFactor AS ?totalEmissions)
}
```

---

## Common Tasks

### Load COMET Into Your Application

**JavaScript/Node.js**:
```javascript
import { loadOntology } from 'comet-js';

const comet = await loadOntology('https://comet.carbon/ontology/0.2.0/comet.ttl');
const classes = comet.getClasses();
```

**Python**:
```python
from rdflib import Graph

g = Graph()
g.parse('https://comet.carbon/ontology/0.2.0/comet.ttl', format='turtle')

# Query using rdflib
for s, p, o in g.triples((None, None, None)):
    print(f"{s} -> {p} -> {o}")
```

**SPARQL Endpoint**:
```bash
curl -H "Accept: application/sparql-results+json" \
  "https://sparql.comet.carbon/?query=SELECT%20%3Fclass%20WHERE%20%7B%20%3Fclass%20a%20owl%3AClass%20.%20%7D%20LIMIT%205"
```

### Access Labels in Different Languages

COMET provides labels in 10 languages. Query a specific language:

```sparql
PREFIX comet: <https://comet.carbon/ontology/>

SELECT ?class ?label_en ?label_es ?label_de WHERE {
  ?class a owl:Class ;
         rdfs:label ?label_en ;
         rdfs:label ?label_es ;
         rdfs:label ?label_de .
  
  FILTER (LANG(?label_en) = "en")
  FILTER (LANG(?label_es) = "es")
  FILTER (LANG(?label_de) = "de")
} LIMIT 5
```

### Add Your Own Data to COMET

```turtle
@prefix comet: <https://comet.carbon/ontology/> .
@prefix myco: <https://mycompany.com/ontology/> .
@prefix : <https://mycompany.com/data/> .

:Product001
  a comet:Product ;
  rdfs:label "My Product" ;
  comet:hasSupplier :Supplier001 ;
  myco:internalId "SKU-12345" .

:Supplier001
  a comet:Supplier ;
  rdfs:label "My Supplier" ;
  comet:hasCertification :ISO14001 .
```

### Validate Your Data

```bash
# Validate RDF data against SHACL shapes
comet validate --data my-instance-data.ttl \
               --shapes comet-shapes.ttl \
               --report validation-report.txt
```

---

## API Reference Quick Links

- **Core Classes**: [Product, Supplier, Emission, Certification, ...]
- **Object Properties**: [hasSupplier, hasCertification, usesProcess, ...]
- **Data Properties**: [weight, emissionsFactor, emissionsValue, ...]
- **Full API Docs**: https://comet.carbon/api/

---

## Get Help

- **Questions?** Check the [FAQ](faq.md)
- **Bug?** File an issue: https://github.com/comet-ontology/comet/issues
- **Discussion?** Start a discussion: https://github.com/comet-ontology/comet/discussions
- **Conduct question?** Email conduct@comet.carbon

---

## What's Next?

1. **Learn more**: Read [COMET architecture](../docs/adr/ADR-001-seven-layer-stack.md)
2. **Build an extension**: Follow [Creating Extensions](creating-extensions.md)
3. **Contribute**: See [Contributing Guide](../CONTRIBUTING.md)
4. **Join the community**: GitHub Discussions, email list, conferences

Welcome to COMET! Happy querying.
