# comet-carbonsig

The **single source of truth** for how CarbonSig projects extend and reference
the [COMET ontology](https://nickgogerty.github.io/comet-ontology/). Two repos
consume it so their COMET mappings cannot silently drift apart:

- [`verifier-export`](https://github.com/CarbonSigProductHub/verifier-export) — maps the Verifier Hub export contract (v4) onto COMET.
- [`pcrbase`](https://github.com/CarbonSigProductHub/pcrbase) — harvests Product Category Rules and maps them onto COMET.

## What's here

| Path | Purpose |
| --- | --- |
| `extensions/comet-pcr.ttl` | The **`comet-pcr`** extension namespace — new COMET terms for Product Category Rules (PCRDocument, CutOffRule, DeclaredModule, ReferenceServiceLife, ContentDeclaration, the keystone `governedByPCR`, and PEF terms). Follows COMET's `comet-rs`/`comet-cn` extension pattern. |
| `registry/namespaces.json` | Canonical prefix → IRI map. Edit here, never in consumers. |
| `registry/comet-curies.json` | **Generated** allow-list of every COMET CURIE a CarbonSig repo may reference (COMET published terms + pending `comet-pcr` terms). |
| `tools/build_registry.py` | Regenerates the registry from COMET's `ontology-data.json` + `comet-pcr.ttl`. |
| `tools/validate_curies.py` / `validate-curies.ts` | Reference validators (Python for pcrbase, TS for verifier-export). Identical semantics. |

## Why this exists

Before this repo, each consumer hard-coded COMET CURIE strings with no check
they existed. That let real bugs through — pcrbase referenced `comet-core:`
(not a COMET prefix; core is `comet:`), `comet-pcf:biogenicCarbon` (wrong case;
the term is `comet-pcf:BiogenicCarbon`), and `comet:FunctionalUnit` (wrong layer;
it's `comet-pcf:FunctionalUnit`). And pcrbase's *proposed* new terms lived only
as dict strings, so verifier-export couldn't reference them even where they
overlap (a footprint's PCR provenance).

Now there is one TTL defining the new terms and one registry both repos validate
against in CI. A typo or a reference to a non-existent COMET term fails the build.

## The `comet-pcr` extension

`comet-pcr` (`https://comet.carbon/ext/pcr#`) adds Product Category Rules method
vocabulary to COMET L4 (PCF). The keystone is **`comet-pcr:governedByPCR`**,
linking a `comet-pcf:ProductCarbonFootprint` to the `comet-pcr:PCRDocument` whose
method requirements govern it. It reifies COMET's single `comet-pcf:PCRReference`
stub into a structured, versioned entity with a programme operator, validity
dates, CPC scope, and supersession chain.

This extension is **pending upstream** into `Carbonsig/comet-ontology` as
evidence-gated PRs (≥3 occurrences + human sign-off), per COMET governance.

## Usage

```bash
# Regenerate the registry (point at a comet-ontology checkout, or rely on a sibling clone)
python tools/build_registry.py --comet-data ../comet-ontology/docs/ontology-data.json

# Validate CURIEs
python tools/validate_curies.py comet-pcf:FunctionalUnit comet-pcr:PCRDocument
bun tools/validate-curies.ts comet:Process comet-pcr:governedByPCR

# Test
python test/test_registry.py
bun test
```

Consumers **vendor** `registry/comet-curies.json` (committed copy) and re-sync it
with a `comet:sync` script, so CI works offline without cross-repo auth. See each
consumer's `comet:sync` / `comet:validate` scripts.

## License

CC BY 4.0 (ontology content) · Apache 2.0 (code) — matching COMET, so the
`comet-pcr` extension can upstream cleanly.
