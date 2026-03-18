#!/usr/bin/env python3
"""
COMET JSON-LD Validator

Validates COMET ProductCarbonFootprint (PCF) and Environmental Attribute
Certificate (EAC) documents against their JSON Schemas.

Usage:
    python validate.py <file.json>
    python validate.py --batch <directory>
    python validate.py <file.json> --strict --quiet

Exit codes:
    0 = valid
    1 = invalid or error
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    import jsonschema
    from jsonschema import Draft7Validator, RefResolver
except ImportError:
    print(
        "Error: jsonschema library is required. Install with:\n"
        "  pip install jsonschema>=4.0",
        file=sys.stderr,
    )
    sys.exit(1)


# ── Schema paths ────────────────────────────────────────────────────────
SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schemas"

SCHEMA_FILES = {
    "pcf": SCHEMA_DIR / "comet-pcf.schema.json",
    "eac": SCHEMA_DIR / "comet-eac.schema.json",
    "core": SCHEMA_DIR / "comet-core.schema.json",
}

# Map @type values to schema keys
TYPE_MAP = {
    "comet-pcf:ProductCarbonFootprint": "pcf",
    "comet-eac:EAC": "eac",
    "comet-eac:EnergyAttributeCertificate": "eac",
    "comet-eac:CarbonRemovalCertificate": "eac",
    "comet-eac:MaterialStewardshipCertificate": "eac",
    "comet-eac:CarbonAvoidanceCredit": "eac",
    "comet-eac:CarbonRemovalCert": "eac",
}


# ── Terminal colors ─────────────────────────────────────────────────────
class Colors:
    """ANSI color codes for terminal output."""

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    @classmethod
    def disable(cls):
        cls.RED = ""
        cls.GREEN = ""
        cls.YELLOW = ""
        cls.CYAN = ""
        cls.BOLD = ""
        cls.RESET = ""


if not sys.stdout.isatty():
    Colors.disable()


# ── Schema loading ──────────────────────────────────────────────────────
_schema_cache: dict[str, dict] = {}


def load_schema(key: str) -> dict:
    """Load and cache a JSON Schema file."""
    if key not in _schema_cache:
        path = SCHEMA_FILES[key]
        if not path.exists():
            raise FileNotFoundError(f"Schema not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            _schema_cache[key] = json.load(f)
    return _schema_cache[key]


def build_resolver() -> RefResolver:
    """Build a JSON Schema RefResolver that can resolve $ref to local schema files."""
    core_schema = load_schema("core")
    store = {}
    for key in SCHEMA_FILES:
        schema = load_schema(key)
        schema_id = schema.get("$id", f"file://{SCHEMA_FILES[key]}")
        store[schema_id] = schema
        # Also store by filename for relative $ref resolution
        store[SCHEMA_FILES[key].name] = schema

    base_uri = f"file://{SCHEMA_DIR}/"
    return RefResolver(base_uri, core_schema, store=store)


# ── Type detection ──────────────────────────────────────────────────────
def detect_type(data: dict) -> str | None:
    """Detect the COMET document type from the @type field."""
    doc_type = data.get("@type")
    if doc_type is None:
        return None
    return TYPE_MAP.get(doc_type)


# ── Error formatting ────────────────────────────────────────────────────
def format_error(error: jsonschema.ValidationError) -> dict:
    """Convert a jsonschema ValidationError into a structured error dict."""
    field = ".".join(str(p) for p in error.absolute_path) or "(root)"
    expected = ""
    got = ""
    suggestion = ""

    if error.validator == "required":
        # Extract field name from message
        missing = error.message
        suggestion = f"Add the missing required field."
        expected = "field to be present"
    elif error.validator == "type":
        expected = error.validator_value
        got = type(error.instance).__name__
        if isinstance(error.validator_value, list):
            expected = " or ".join(error.validator_value)
        suggestion = f"Change the value to type '{expected}'."
    elif error.validator == "enum":
        expected = ", ".join(str(v) for v in error.validator_value)
        got = str(error.instance)
        suggestion = f"Use one of: {expected}"
    elif error.validator == "format":
        expected = f"format: {error.validator_value}"
        got = str(error.instance)
        suggestion = f"Provide a valid {error.validator_value} string."
    elif error.validator == "minimum":
        expected = f">= {error.validator_value}"
        got = str(error.instance)
        suggestion = f"Value must be at least {error.validator_value}."
    elif error.validator == "maximum":
        expected = f"<= {error.validator_value}"
        got = str(error.instance)
        suggestion = f"Value must be at most {error.validator_value}."
    elif error.validator == "exclusiveMinimum":
        expected = f"> {error.validator_value}"
        got = str(error.instance)
        suggestion = f"Value must be strictly greater than {error.validator_value}."
    elif error.validator == "minLength":
        expected = f"string with length >= {error.validator_value}"
        got = f"string of length {len(error.instance)}" if isinstance(error.instance, str) else str(error.instance)
        suggestion = "Provide a non-empty string."
    elif error.validator == "minItems":
        expected = f"array with >= {error.validator_value} items"
        got = f"array with {len(error.instance)} items" if isinstance(error.instance, list) else str(error.instance)
        suggestion = f"Provide at least {error.validator_value} item(s)."
    elif error.validator == "pattern":
        expected = f"pattern: {error.validator_value}"
        got = str(error.instance)
        suggestion = f"Value must match the pattern {error.validator_value}."
    elif error.validator == "const":
        expected = str(error.validator_value)
        got = str(error.instance)
        suggestion = f"Value must be exactly '{error.validator_value}'."
    elif error.validator == "additionalProperties":
        suggestion = "Remove the unexpected property or check for typos."
        expected = "no additional properties"
        got = error.message
    else:
        expected = str(error.validator_value) if error.validator_value else ""
        got = str(error.instance)[:100] if error.instance is not None else ""
        suggestion = error.message

    return {
        "field": field,
        "error": error.message,
        "expected": expected,
        "got": got,
        "suggestion": suggestion,
    }


# ── Validation ──────────────────────────────────────────────────────────
def validate_document(
    data: dict,
    strict: bool = False,
) -> list[dict]:
    """
    Validate a COMET JSON-LD document against its schema.

    Returns a list of structured error dicts. Empty list means valid.
    """
    schema_key = detect_type(data)
    if schema_key is None:
        return [
            {
                "field": "@type",
                "error": "Cannot detect document type. Missing or unrecognized @type field.",
                "expected": ", ".join(TYPE_MAP.keys()),
                "got": str(data.get("@type", "(missing)")),
                "suggestion": "Add an @type field with a valid COMET type.",
            }
        ]

    schema = load_schema(schema_key)
    resolver = build_resolver()

    validator_cls = Draft7Validator
    validator = validator_cls(schema, resolver=resolver)

    errors = []
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
        errors.append(format_error(error))

    return errors


def validate_file(
    file_path: Path,
    strict: bool = False,
    quiet: bool = False,
) -> bool:
    """
    Validate a single COMET JSON-LD file.

    Returns True if valid, False if invalid.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        if not quiet:
            print(f"{Colors.RED}ERROR{Colors.RESET} {file_path}: Invalid JSON — {e}")
        return False
    except FileNotFoundError:
        if not quiet:
            print(f"{Colors.RED}ERROR{Colors.RESET} {file_path}: File not found")
        return False

    errors = validate_document(data, strict=strict)

    if not errors:
        if not quiet:
            print(f"{Colors.GREEN}VALID{Colors.RESET} {file_path}")
        return True

    if quiet:
        print(f"{Colors.RED}INVALID{Colors.RESET} {file_path}: {len(errors)} error(s)")
    else:
        print(f"{Colors.RED}INVALID{Colors.RESET} {file_path}: {len(errors)} error(s)\n")
        for err in errors:
            print(f"  {Colors.CYAN}{err['field']}{Colors.RESET}: {err['error']}")
            if err["expected"]:
                print(f"    Expected: {Colors.YELLOW}{err['expected']}{Colors.RESET}")
            if err["got"]:
                print(f"    Got:      {err['got']}")
            if err["suggestion"]:
                print(f"    Fix:      {err['suggestion']}")
            print()

    return False


def validate_batch(
    directory: Path,
    strict: bool = False,
    quiet: bool = False,
) -> bool:
    """
    Validate all .json files in a directory.

    Returns True if all files are valid, False otherwise.
    """
    json_files = sorted(directory.glob("*.json"))
    if not json_files:
        print(f"{Colors.YELLOW}WARNING{Colors.RESET} No .json files found in {directory}")
        return True

    all_valid = True
    valid_count = 0
    invalid_count = 0

    for fp in json_files:
        if validate_file(fp, strict=strict, quiet=quiet):
            valid_count += 1
        else:
            invalid_count += 1
            all_valid = False

    if not quiet:
        print(f"\n{Colors.BOLD}Summary:{Colors.RESET} {valid_count} valid, {invalid_count} invalid, {len(json_files)} total")

    return all_valid


def validate_to_json(file_path: Path, strict: bool = False) -> str:
    """
    Validate a file and return results as a JSON string.

    Used by the CLI for structured output.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return json.dumps(
            {
                "file": str(file_path),
                "valid": False,
                "errors": [
                    {
                        "field": "(root)",
                        "error": f"Invalid JSON: {e}",
                        "expected": "valid JSON",
                        "got": "",
                        "suggestion": "Fix the JSON syntax error.",
                    }
                ],
            },
            indent=2,
        )
    except FileNotFoundError:
        return json.dumps(
            {
                "file": str(file_path),
                "valid": False,
                "errors": [
                    {
                        "field": "(root)",
                        "error": "File not found",
                        "expected": "",
                        "got": "",
                        "suggestion": "Check the file path.",
                    }
                ],
            },
            indent=2,
        )

    errors = validate_document(data, strict=strict)
    return json.dumps(
        {
            "file": str(file_path),
            "valid": len(errors) == 0,
            "errors": errors,
        },
        indent=2,
    )


# ── CLI ─────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Validate COMET JSON-LD files against schemas.",
        epilog=(
            "Examples:\n"
            "  python validate.py steel-pcf.comet.json\n"
            "  python validate.py --batch examples/\n"
            "  python validate.py steel-pcf.comet.json --strict --quiet\n"
            "  python validate.py steel-pcf.comet.json --json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Path to a COMET JSON-LD file to validate.",
    )
    parser.add_argument(
        "--batch",
        metavar="DIR",
        help="Validate all .json files in the given directory.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: also validate optional fields for type correctness.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Quiet mode: only output error count per file.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output validation results as structured JSON.",
    )

    args = parser.parse_args()

    if args.batch:
        batch_dir = Path(args.batch)
        if not batch_dir.is_dir():
            print(f"{Colors.RED}ERROR{Colors.RESET} Not a directory: {args.batch}", file=sys.stderr)
            sys.exit(1)
        success = validate_batch(batch_dir, strict=args.strict, quiet=args.quiet)
        sys.exit(0 if success else 1)

    if not args.file:
        parser.print_help()
        sys.exit(1)

    file_path = Path(args.file)

    if args.json_output:
        print(validate_to_json(file_path, strict=args.strict))
        # Parse result to set exit code
        result = json.loads(validate_to_json(file_path, strict=args.strict))
        sys.exit(0 if result["valid"] else 1)
    else:
        success = validate_file(file_path, strict=args.strict, quiet=args.quiet)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
