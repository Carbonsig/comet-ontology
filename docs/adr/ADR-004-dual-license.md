# ADR-004: Dual License (CC BY 4.0 + Apache 2.0)

**Status**: Accepted

**Date**: 2026-03-15

---

## Context

Licensing COMET required balancing multiple stakeholder needs:

1. **Data users** (companies using COMET for carbon accounting): Want flexible use, minimal restrictions
2. **Tool developers** (building software on top of COMET): Want clear IP terms, no contamination
3. **Academic researchers**: Want attribution and citation
4. **Standards bodies** (ResponsibleSteel, PACT, etc.): Want to incorporate COMET into standards
5. **Community contributors**: Want to know their contributions are fairly licensed

COMET has two distinct components with different licensing needs:

- **The ontology itself** (RDF/OWL data): Semantic knowledge asset
- **Supporting software** (validation tools, converters): Functional code

A single license couldn't address both effectively.

---

## Decision

**COMET adopts a dual license model:**

- **Ontology data**: Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Supporting software**: Apache License 2.0

### The Ontology: CC BY 4.0

The ontology files (`comet.ttl`, extension files, SHACL shapes, example data) are licensed under **CC BY 4.0**:

```
Copyright (c) 2026 Nick Gogerty and COMET Contributors

This work is licensed under the Creative Commons Attribution 4.0 International License.
To view a copy of this license, visit http://creativecommons.org/licenses/by/4.0/
```

**CC BY 4.0 means**:
- ✓ Use for any purpose (commercial, educational, research)
- ✓ Modify and create derivative works
- ✓ Share and redistribute
- ✓ No restrictions on field of use
- → **Requirement**: Attribution (cite COMET)

### Supporting Software: Apache 2.0

Tools, validators, and utilities (Python SDK, CLI tools, test suites) are licensed under **Apache License 2.0**:

```
Copyright (c) 2026 Nick Gogerty and COMET Contributors

Licensed under the Apache License, Version 2.0 (the "License")...
```

**Apache 2.0 means**:
- ✓ Commercial use
- ✓ Modification and private use
- ✓ Distribution (with license and notice)
- ✓ Patent indemnification
- → **Requirement**: Include license copy; state changes

### Why This Combination?

| Aspect | CC BY 4.0 | Apache 2.0 |
|--------|-----------|-----------|
| **Best for** | Data/knowledge assets | Software/code |
| **Attribution** | Required | Required |
| **Derivative works** | Allowed | Allowed |
| **Patent clause** | No | Yes (important for software) |
| **Commercial use** | Allowed | Allowed |
| **Compatibility** | With data licenses | With open source |

---

## Specific Files

### CC BY 4.0 (Ontology Data)

```
comet-core.ttl
comet-shapes.ttl
comet.ttl

ext/responsiblesteel/ontology.ttl
ext/responsiblesteel/shapes.ttl
ext/responsiblesteel/examples.ttl

labels/labels-*.ttl
examples/*.ttl
```

### Apache 2.0 (Software)

```
src/comet_ontology/__init__.py
src/comet_cli/main.py
tools/validate.py
tools/convert.py

tests/*.py

Makefile
setup.py
```

### Shared/Dual (Documentation & Config)

```
README.md          (CC BY 4.0)
CONTRIBUTING.md    (CC BY 4.0)
docs/              (CC BY 4.0)
LICENSE-CC-BY-4.0  (CC BY 4.0)
LICENSE-APACHE-2.0 (Apache 2.0)
```

---

## Attribution Requirements

### For Using the Ontology Data

When using COMET ontology, you must:

1. **In documentation**: "Uses COMET (Carbon Ontology for Materials and Emissions Tracking)"
2. **In code/systems**: Comment or metadata with attribution
3. **In publications**: Citation (see CITATION.cff)

### Citation Format

**BibTeX**:
```
@software{gogerty2026comet,
  author = {Gogerty, Nick},
  title = {COMET: Carbon Ontology for Materials and Emissions Tracking},
  year = {2026},
  url = {https://comet.carbon},
  version = {0.2.0}
}
```

**In text**:
"We use COMET (Carbon Ontology for Materials and Emissions Tracking, v0.2.0; Gogerty, 2026)"

---

## Consequences

### Positive

1. **Permissive for Data**: CC BY 4.0 is maximally permissive for data use
   - Companies can use COMET freely
   - Standards bodies can incorporate COMET
   - No "viral" effects (unlike GPL)
   - Encourages widespread adoption

2. **Patent Protection for Software**: Apache 2.0 includes patent grant
   - Developers won't be sued for using COMET tools
   - Clear IP indemnification
   - Important for enterprise adoption

3. **Academic Compatibility**: CC BY 4.0 is respected in academia
   - Researchers can cite COMET
   - Can be adapted for research
   - Appropriate for knowledge assets

4. **Contributor Clarity**: Contributors understand license status
   - Data contributions under CC BY 4.0
   - Code contributions under Apache 2.0
   - No confusion about what applies

5. **Standards Body Integration**: CC BY 4.0 allows incorporation
   - ResponsibleSteel can build on COMET
   - PACT can align with COMET
   - No licensing barriers

### Negative

1. **Complexity**: Two licenses is harder to explain than one
   - New users must understand both
   - More legal text to review
   - Potential confusion ("Which applies to what?")

2. **Attribution Burden**: CC BY 4.0 requires attribution in all uses
   - Every derived product must credit COMET
   - Difficult to enforce at scale
   - Could be considered burdensome for some users

3. **Compatibility Questions**: Dual licensing can raise questions
   - What if someone combines CC BY code with Apache code?
   - Are they compatible? (They are, but users may not know)
   - Potential friction in some licensing regimes

### Neutral

1. **License Text Size**: Both licenses have substantial text
   - Must include full license copies in distribution
   - Adds ~5KB to repository
   - Required by both licenses

---

## Alternatives Considered

### Alternative 1: CC0 (Public Domain)

**Approach**: Place everything in public domain

**Pros**:
- Simplest (no attribution required)
- Maximum freedom for users
- True "open"

**Cons**:
- No attribution (COMET loses credit)
- Academic work deserves citation
- Community credit lost
- Difficult for researchers to cite

### Alternative 2: GPL v3 (for everything)

**Approach**: Copyleft license for ontology and software

**Pros**:
- Ensures derivative works are open
- Strong copyleft protection

**Cons**:
- Viral effect (any use requires GPL)
- Standards bodies won't use it
- Companies uncomfortable with GPL
- Defeats goal of adoption

### Alternative 3: Single CC BY 4.0 License

**Approach**: Use CC BY 4.0 for ontology and software

**Pros**:
- Single license is simpler
- CC BY is permissive

**Cons**:
- CC BY not designed for software
- No patent protection for code
- Unclear for executable programs
- Apache 2.0 better practice for software

### Alternative 4: ELRA (European Language Resources Association)

**Approach**: Data license designed for linguistic resources

**Pros**:
- Specifically for structured data
- Recognized in research community

**Cons**:
- Not well-known outside linguistics
- Overly specialized for carbon ontology
- Less permissive than CC BY
- Patent terms weak for software

---

## Implementation

### Repository Structure

```
LICENSE
├── LICENSE-CC-BY-4.0          # Full CC BY 4.0 text
├── LICENSE-APACHE-2.0         # Full Apache 2.0 text

comet/
├── comet.ttl
│   File header comment:
│   # This work is licensed under CC BY 4.0
│   # See LICENSE-CC-BY-4.0 for full license text

src/
├── comet_ontology/__init__.py
│   File header comment:
│   # Licensed under Apache License 2.0
│   # See LICENSE-APACHE-2.0 for full license text
```

### Copyright Notices

**In CC BY 4.0 files**:
```
@prefix dc: <http://purl.org/dc/elements/1.1/> .

<https://comet.carbon/ontology/>
  dc:rights "Copyright (c) 2026 Nick Gogerty and COMET Contributors" ;
  dc:license <http://creativecommons.org/licenses/by/4.0/> .
```

**In Apache 2.0 files**:
```
# Copyright 2026 Nick Gogerty and COMET Contributors
# Licensed under the Apache License, Version 2.0 (the "License")
```

### Package Distribution

```
comet-0.2.0.tar.gz
├── LICENSE           (instructions)
├── LICENSE-CC-BY-4.0 (full CC BY text)
├── LICENSE-APACHE-2.0 (full Apache text)
├── comet/            (CC BY 4.0 data)
├── src/              (Apache 2.0 software)
└── README.md         (explains both licenses)
```

---

## FAQ

**Q: Can I use COMET commercially?**
A: Yes. CC BY 4.0 permits commercial use with attribution.

**Q: Can I modify the ontology?**
A: Yes. Create a derivative work (fork) and attribute the original.

**Q: Can I include COMET in my proprietary product?**
A: Yes, but you must attribute COMET and provide the license text.

**Q: Can I build proprietary software on top of COMET?**
A: Yes. The ontology (CC BY) is permissive. Your software (Apache 2.0) can be proprietary if you use our tools.

**Q: What if I incorporate COMET into a standard?**
A: Include attribution and license text. CC BY 4.0 explicitly permits this.

**Q: Do I need to open-source my data if I use COMET?**
A: No. COMET uses only the ontology schema, not your instance data.

**Q: How do I attribute COMET?**
A: Include "Uses COMET (Carbon Ontology for Materials and Emissions Tracking)" in your documentation. See CITATION.cff for full citation.

---

## Related Decisions

- All COMET decisions are made under these licensing terms
- Contributions are automatically licensed under dual license (see CONTRIBUTING.md)

---

## References

- **CC BY 4.0**: https://creativecommons.org/licenses/by/4.0/
- **Apache 2.0**: https://www.apache.org/licenses/LICENSE-2.0
- **Dual Licensing Guide**: https://opensource.org/guide/dual-licensing/
- **W3C Semantic Web Licensing**: https://www.w3.org/Consortium/Legal/2015/copyright-software-and-document.html
