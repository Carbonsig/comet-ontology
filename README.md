# COMET — Carbon Ontology for Markets, Emissions & Trade

A free, open, community-governed meta-ontology that maps product-level carbon
footprint data, supply chain verification, Environmental Attribute Certificates,
and market-pricing signals into a single interoperable knowledge graph. COMET
provides a shared language so carbon data can move between platforms, suppliers,
regulators, and markets without translation loss.

## The Problem

Carbon data exists across platforms, suppliers, and regulators — but none speaks
the same language. Different units, methodologies, scopes, and emission factor
vintages make comparison, verification, and trading impossible. Without a common
schema, every integration is bespoke, every audit is manual, and every market
signal is noisy.

## Architecture

COMET is organised as a seven-layer stack:

| Layer | Name | Covers |
|-------|------|--------|
| L1 | Core Identity | Organisations, Sites, Processes, Materials, UOM |
| L2 | Emission Factors | Ecoinvent, WorldSteel, BAFU, Climatiq |
| L3 | Supply Chain & Activity Data | Bills of materials, transport, energy inputs |
| L4 | Product Carbon Footprint | ISO 14067, PACT v3 aligned PCFs |
| L5 | Environmental Attribute Certificates | I-RECs, DAC credits, GO certificates |
| L6 | Verification & Assurance | Third-party audits, chain-of-custody proofs |
| L7 | Market Signals | Carbon premiums, CBAM tariffs, EAC prices |

## Documentation

- [Microsite](https://nickgogerty.github.io/comet-ontology/) — Project overview and documentation hub
- [Ontology Specification](https://nickgogerty.github.io/comet-ontology/ontology.html) — Complete 20-section specification
- [Master Build Plan](https://nickgogerty.github.io/comet-ontology/build-plan.html) — 200 steps across 10 expert panels
- Stakeholder Deck (PPTX) — in `docs/` folder

## Related Research — Carbon at Risk

COMET builds on the [Carbon at Risk (CaR)](https://www.carbonatrisk.org/) framework,
originated by Nick Gogerty at Carbon Finance Labs. CaR applies Value-at-Risk
methodology to carbon removal, quantifying delivery risk and storage risk across
removal approaches. Where CaR provides the risk measurement language, COMET
provides the ontological infrastructure to make it interoperable.

## Standards Alignment

ISO 14067, PACT v3, EU CBAM, GHG Protocol, EN 15804, IRA 45V,
ResponsibleSteel, ASI.

## License

CC BY 4.0 (content) | Apache 2.0 (code)

## About

A [Carbon Finance Lab](https://carbonfinancelab.com) research initiative.
