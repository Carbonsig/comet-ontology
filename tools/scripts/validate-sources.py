#!/usr/bin/env python3
"""
Validate dcterms:source values in COMET RS TTL files.

Extracts all source declarations and validates them against known patterns
for COMET-related standards and specifications.

Usage:
    python validate-sources.py --files core.ttl,labels/*.ttl [--strict]
"""

import argparse
import sys
import re
from pathlib import Path
from rdflib import Graph, Namespace
from collections import Counter

# Known source patterns
KNOWN_SOURCES = {
    "RS Production Standard V2.1.1": {
        "pattern": r"RS.*Standard.*V?2\.1\.1",
        "description": "Responsible Steel Production Standard v2.1.1",
    },
    "GHG Protocol": {
        "pattern": r"GHG.{0,20}?(Protocol|Standard|Scope)",
        "description": "Greenhouse Gas Protocol Standard",
    },
    "GHG Fundamentals": {
        "pattern": r"GHG.{0,20}?Fundamentals",
        "description": "GHG Protocol Fundamentals",
    },
    "PACT Pathfinder": {
        "pattern": r"PACT.{0,20}?(Pathfinder|v?3)",
        "description": "PACT Pathfinder v3 Specification",
    },
    "EU CBAM": {
        "pattern": r"(CBAM|Carbon.Border)",
        "description": "EU Carbon Border Adjustment Mechanism",
    },
    "CSRD/ESRS": {
        "pattern": r"(CSRD|ESRS|Corporate.Sustainability)",
        "description": "Corporate Sustainability Reporting Directive",
    },
    "ISO 14040": {
        "pattern": r"ISO.{0,5}14040",
        "description": "ISO 14040 LCA Methodology",
    },
    "ISO 14044": {
        "pattern": r"ISO.{0,5}14044",
        "description": "ISO 14044 LCA Requirements",
    },
    "ILCD Handbook": {
        "pattern": r"ILCD",
        "description": "International Reference Life Cycle Data System",
    },
    "World Steel": {
        "pattern": r"World.?Steel",
        "description": "World Steel Association publications",
    },
    "ILO Conventions": {
        "pattern": r"ILO",
        "description": "International Labour Organization Conventions",
    },
    "Transparency International": {
        "pattern": r"Transparency.International",
        "description": "Transparency International",
    },
    "UN Sustainable Development": {
        "pattern": r"(SDG|UN|Sustainable.Development)",
        "description": "UN Sustainable Development Goals",
    },
}


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Validate dcterms:source declarations in COMET RS TTL files."
    )
    parser.add_argument(
        "--files",
        type=str,
        required=True,
        help="Comma-separated TTL file paths (supports glob patterns)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 if any unknown sources found",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed source analysis",
    )
    return parser.parse_args()


def expand_file_paths(files_spec):
    """
    Expand file specification into actual paths.

    Supports comma-separated paths and glob patterns.
    """
    paths = []
    for spec in files_spec.split(","):
        spec = spec.strip()
        if "*" in spec:
            paths.extend(Path(".").glob(spec))
        else:
            paths.append(Path(spec))
    return [p for p in paths if p.exists()]


def load_graph(file_paths):
    """Load multiple TTL files into single graph."""
    graph = Graph()
    DCTERMS = Namespace("http://purl.org/dc/terms/")

    for file_path in file_paths:
        try:
            print(f"Loading: {file_path}")
            graph.parse(str(file_path), format="turtle")
        except Exception as e:
            print(f"Warning: Error loading {file_path}: {e}")

    return graph


def extract_sources(graph):
    """Extract all dcterms:source values from graph."""
    DCTERMS = Namespace("http://purl.org/dc/terms/")
    sources = []

    for s, p, o in graph.triples((None, DCTERMS.source, None)):
        source_value = str(o)
        sources.append({
            "value": source_value,
            "subject": str(s),
        })

    return sources


def classify_source(source_value):
    """
    Classify a source value against known patterns.

    Returns:
        tuple: (matched_category, confidence)
    """
    # Normalize for matching
    normalized = source_value.lower().replace("_", " ").replace("-", " ")

    best_match = None
    best_score = 0

    for category, config in KNOWN_SOURCES.items():
        pattern = config["pattern"]
        try:
            if re.search(pattern, normalized, re.IGNORECASE):
                # Higher score if exact match vs. partial
                if source_value.lower() == category.lower():
                    return (category, 1.0)
                else:
                    score = 0.8
                    if best_score < score:
                        best_match = category
                        best_score = score
        except Exception as e:
            print(f"Warning: Regex error for {category}: {e}")

    if best_match:
        return (best_match, best_score)

    return (None, 0.0)


def generate_report(sources, file_paths):
    """Generate validation report."""
    lines = []

    lines.append("=" * 80)
    lines.append("SOURCE VALIDATION REPORT")
    lines.append("=" * 80)
    lines.append(f"\nFiles analyzed: {len(file_paths)}")
    lines.append(f"Total sources found: {len(sources)}\n")

    # Classify sources
    classified = {}
    unrecognized = []

    for source in sources:
        category, confidence = classify_source(source["value"])

        if category:
            if category not in classified:
                classified[category] = []
            classified[category].append(source)
        else:
            unrecognized.append(source)

    # Summary
    lines.append("=" * 80)
    lines.append("SUMMARY")
    lines.append("=" * 80)
    lines.append(f"Recognized sources:   {sum(len(v) for v in classified.values())}")
    lines.append(f"Unrecognized sources: {len(unrecognized)}")
    lines.append("")

    # Recognized sources
    if classified:
        lines.append("-" * 80)
        lines.append("RECOGNIZED SOURCES")
        lines.append("-" * 80)

        for category in sorted(classified.keys()):
            entries = classified[category]
            lines.append(f"\n{category} ({len(entries)} occurrences)")

            # Show unique values
            unique_values = set(e["value"] for e in entries)
            for value in sorted(unique_values):
                lines.append(f"  • {value}")

    # Unrecognized sources
    if unrecognized:
        lines.append("\n" + "-" * 80)
        lines.append("UNRECOGNIZED SOURCES")
        lines.append("-" * 80)
        lines.append(f"\nFound {len(unrecognized)} unrecognized source reference(s):\n")

        unique_unrecognized = set(s["value"] for s in unrecognized)
        for value in sorted(unique_unrecognized):
            count = sum(1 for s in unrecognized if s["value"] == value)
            lines.append(f"  • {value} ({count}x)")

        lines.append("\nNOTE: These sources do not match known COMET/standards patterns.")
        lines.append("Please verify these are valid references or update validation patterns.")

    # Known sources reference
    lines.append("\n" + "=" * 80)
    lines.append("REFERENCE: KNOWN SOURCE PATTERNS")
    lines.append("=" * 80)

    for category in sorted(KNOWN_SOURCES.keys()):
        config = KNOWN_SOURCES[category]
        lines.append(f"\n{category}")
        lines.append(f"  Description: {config['description']}")
        lines.append(f"  Pattern: {config['pattern']}")

    lines.append("\n" + "=" * 80)

    return "\n".join(lines), len(unrecognized)


def main():
    """Main entry point."""
    args = parse_arguments()

    # Expand file paths
    file_paths = expand_file_paths(args.files)

    if not file_paths:
        print("Error: No TTL files found matching specification", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(file_paths)} file(s) to analyze\n")

    # Load graph
    graph = load_graph(file_paths)
    print(f"Loaded graph with {len(graph)} triples\n")

    # Extract sources
    sources = extract_sources(graph)

    if not sources:
        print("Warning: No dcterms:source declarations found in ontology")
        sys.exit(0)

    # Generate report
    report, unrecognized_count = generate_report(sources, file_paths)
    print(report)

    # Exit code
    if args.strict and unrecognized_count > 0:
        print(f"\nERROR: {unrecognized_count} unrecognized source(s) found (--strict mode)")
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
