# COMET Data Tools

Command-line tools for validating, converting, and exporting carbon data in the COMET JSON-LD format.

## Install

```bash
cd tools/
pip install -r requirements.txt
```

Requires Python 3.9+. The only external dependency is `jsonschema`.

## Quick start

### Validate a COMET file

```bash
python comet_cli.py validate examples/steel-pcf.comet.json
```

Validate all files in a directory:

```bash
python comet_cli.py validate examples/
```

Strict mode (checks optional fields too) and quiet mode (error count only):

```bash
python comet_cli.py validate data.json --strict --quiet
```

Structured JSON output:

```bash
python comet_cli.py validate data.json --json
```

### Generate a template

```bash
python comet_cli.py template pcf                     # Print PCF template to stdout
python comet_cli.py template eac --output my-eac.json  # Write EAC template to file
python comet_cli.py template scope3                   # Scope 3 template (15 categories)
```

### Convert external formats to COMET

```bash
python comet_cli.py convert data.csv --from csv --to comet --pretty
python comet_cli.py convert footprint.json --from pact --to comet
python comet_cli.py convert declaration.xml --from cbam-xml --to comet
python comet_cli.py convert credits.json --from cad-trust --to comet --output out.json
```

### Export COMET to external formats

```bash
python comet_cli.py export steel.comet.json --to pact
python comet_cli.py export steel.comet.json --to cbam-xml --output declaration.xml
python comet_cli.py export steel.comet.json --to csv --output report.csv
```

## Direct validator usage

The validator can also be run standalone:

```bash
python validators/validate.py steel-pcf.comet.json
python validators/validate.py --batch examples/
python validators/validate.py data.json --strict --quiet
```

## Schemas

JSON Schemas for all COMET data types live in `schemas/`:

| File | Description |
|------|-------------|
| `comet-core.schema.json` | Shared entities: Organization, Site, Material, TimePeriod, UnitOfMeasure, EmissionFactor, Verification |
| `comet-pcf.schema.json` | Product Carbon Footprint — ISO 14067, GHG Protocol, PACT v3, CBAM aligned |
| `comet-eac.schema.json` | Environmental Attribute Certificate — Verra, Gold Standard, CAD Trust, Article 6 aligned |

Schemas use JSON Schema draft-07 with `$ref` to shared definitions in `comet-core.schema.json`.

## Supported formats

| Direction | Format | Converter | Status |
|-----------|--------|-----------|--------|
| Ingest | CSV | `csv_to_comet.py` | Planned |
| Ingest | PACT v3 JSON | `pact_to_comet.py` | Planned |
| Ingest | CBAM XML | `cbam_to_comet.py` | Planned |
| Ingest | CAD Trust | `cad_trust_to_comet.py` | Planned |
| Export | PACT v3 JSON | `comet_to_pact.py` | Planned |
| Export | CBAM XML | `comet_to_cbam.py` | Planned |
| Export | CSV | `comet_to_csv.py` | Planned |

## Project structure

```
tools/
  comet_cli.py              # Unified CLI entry point
  requirements.txt          # Python dependencies
  README.md                 # This file
  schemas/
    comet-core.schema.json  # Shared entity definitions
    comet-pcf.schema.json   # PCF schema
    comet-eac.schema.json   # EAC schema
  validators/
    validate.py             # Validation script
  converters/               # Format converters (planned)
  templates/                # CSV templates (planned)
  examples/                 # Example JSON-LD files (planned)
```

## Exit codes

- `0` — valid / success
- `1` — invalid / error
