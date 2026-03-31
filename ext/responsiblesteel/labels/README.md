# COMET ResponsibleSteel Multilingual Labels

Turtle RDF files providing translated labels for the COMET ResponsibleSteel ontology extension across 9 languages.

## Files

| File | Language | Code | Terms |
|------|----------|------|-------|
| `labels-zh.ttl` | Chinese (Simplified) | zh-Hans | 44 |
| `labels-de.ttl` | German | de | 44 |
| `labels-ja.ttl` | Japanese | ja | 44 |
| `labels-ko.ttl` | Korean | ko | 44 |
| `labels-fr.ttl` | French | fr | 44 |
| `labels-es.ttl` | Spanish | es | 44 |
| `labels-pt.ttl` | Portuguese | pt | 44 |
| `labels-hi.ttl` | Hindi | hi | 44 |
| `labels-ar.ttl` | Arabic | ar | 44 |

## Coverage

Each file provides translations for:
- **31 Classes** organized in 7 layers (L1–L7):
  - L1 Core: 7 classes (production routes)
  - L3 Supply Chain: 9 classes
  - L4 PCF: 6 classes
  - L5 EAC: 7 classes
  - L6 Verification: 6 classes
  - L7 Market: 2 classes

- **13 RS Principles** (P01–P13):
  - Corporate Leadership, ESG Systems, Stakeholder Engagement
  - Environmental Management, GHG Reduction, Climate Adaptation
  - Water Security, Air Quality, Waste Stewardship
  - Human Rights, Labor Practices, Occupational Safety, Community Impact

## Format

Each file follows standard Turtle RDF format with:
- `rdfs:label` for complete descriptive labels
- `skos:prefLabel` for preferred short labels
- `skos:altLabel` for technical abbreviations (BF-BOF, EAF, DRI-EAF, SR-BOF, DPL, SPL)
- Language tags (e.g., `@zh-Hans`, `@de`, `@ja`)

## Technical Terminology

All translations use industry-standard steel terminology:
- BF-BOF: Blast Furnace - Basic Oxygen Furnace
- EAF: Electric Arc Furnace
- DRI-EAF: Direct Reduced Iron - Electric Arc Furnace
- SR-BOF: Scrap - Basic Oxygen Furnace
- DPL: Decarbonization Progress Level
- SPL: Sourcing Progress Level
- CoC: Chain of Custody
- CCUS: Carbon Capture, Utilization & Storage

## Unicode Support

Files include full Unicode support for:
- Chinese characters (Hanzi)
- Japanese characters (Hiragana, Katakana, Kanji)
- Korean Hangul
- Hindi Devanagari script
- Arabic script (RTL)
- European diacritics
