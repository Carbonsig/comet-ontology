#!/usr/bin/env python3
"""
Detect breaking changes between two versions of a TTL ontology file.

Compares old vs new TTL files and identifies:
- Removed classes
- Removed properties
- Changed property ranges/domains
- Removed individuals
- Removed object properties

Usage:
    python detect-breaking-changes.py old.ttl new.ttl [--report-file report.txt]
"""

import argparse
import sys
from pathlib import Path
from rdflib import Graph, RDF, RDFS, OWL, Namespace
from collections import defaultdict


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Detect breaking changes between TTL ontology versions."
    )
    parser.add_argument(
        "old_file",
        type=Path,
        help="Old/baseline TTL file",
    )
    parser.add_argument(
        "new_file",
        type=Path,
        help="New TTL file to check",
    )
    parser.add_argument(
        "--report-file",
        type=Path,
        help="Optional file to write report (otherwise stdout)",
    )
    parser.add_argument(
        "--exit-on-breaking",
        action="store_true",
        default=True,
        help="Exit with code 1 if breaking changes found (default: True)",
    )
    return parser.parse_args()


def load_graph(file_path):
    """Load TTL file into graph."""
    graph = Graph()
    try:
        graph.parse(str(file_path), format="turtle")
        return graph
    except Exception as e:
        print(f"Error loading {file_path}: {e}", file=sys.stderr)
        sys.exit(1)


def extract_classes(graph):
    """Extract all OWL classes."""
    classes = {}
    for s in graph.subjects(RDF.type, OWL.Class):
        classes[s] = {
            "label": None,
            "comment": None,
        }
        # Try to get label
        for label in graph.objects(s, RDFS.label):
            classes[s]["label"] = str(label)
            break
        # Try to get comment
        for comment in graph.objects(s, RDFS.comment):
            classes[s]["comment"] = str(comment)
            break

    return classes


def extract_properties(graph):
    """Extract all RDF/OWL properties."""
    properties = {}

    # Object properties
    for s in graph.subjects(RDF.type, OWL.ObjectProperty):
        properties[s] = {
            "type": "ObjectProperty",
            "label": None,
            "domain": None,
            "range": None,
        }
        for label in graph.objects(s, RDFS.label):
            properties[s]["label"] = str(label)
            break
        for domain in graph.objects(s, RDFS.domain):
            properties[s]["domain"] = str(domain)
            break
        for range_ in graph.objects(s, RDFS.range):
            properties[s]["range"] = str(range_)
            break

    # Data properties
    for s in graph.subjects(RDF.type, OWL.DatatypeProperty):
        properties[s] = {
            "type": "DatatypeProperty",
            "label": None,
            "domain": None,
            "range": None,
        }
        for label in graph.objects(s, RDFS.label):
            properties[s]["label"] = str(label)
            break
        for domain in graph.objects(s, RDFS.domain):
            properties[s]["domain"] = str(domain)
            break
        for range_ in graph.objects(s, RDFS.range):
            properties[s]["range"] = str(range_)
            break

    # RDF properties (catch-all)
    for s in graph.subjects(RDF.type, RDF.Property):
        if s not in properties:
            properties[s] = {
                "type": "Property",
                "label": None,
                "domain": None,
                "range": None,
            }

    return properties


def extract_individuals(graph):
    """Extract named individuals."""
    individuals = {}

    for s in graph.subjects(RDF.type, OWL.NamedIndividual):
        individuals[s] = {
            "label": None,
            "comment": None,
        }
        for label in graph.objects(s, RDFS.label):
            individuals[s]["label"] = str(label)
            break
        for comment in graph.objects(s, RDFS.comment):
            individuals[s]["comment"] = str(comment)
            break

    return individuals


def detect_removed_classes(old_classes, new_classes):
    """Detect removed classes."""
    removed = []
    for uri in old_classes:
        if uri not in new_classes:
            removed.append((uri, old_classes[uri]))
    return removed


def detect_removed_properties(old_props, new_props):
    """Detect removed properties."""
    removed = []
    for uri in old_props:
        if uri not in new_props:
            removed.append((uri, old_props[uri]))
    return removed


def detect_changed_ranges(old_props, new_props):
    """Detect properties with changed ranges or domains."""
    changes = []
    for uri in old_props:
        if uri in new_props:
            old_domain = old_props[uri]["domain"]
            new_domain = new_props[uri]["domain"]
            old_range = old_props[uri]["range"]
            new_range = new_props[uri]["range"]

            if old_domain != new_domain:
                changes.append({
                    "uri": uri,
                    "property": "domain",
                    "old": old_domain,
                    "new": new_domain,
                })

            if old_range != new_range:
                changes.append({
                    "uri": uri,
                    "property": "range",
                    "old": old_range,
                    "new": new_range,
                })

    return changes


def detect_removed_individuals(old_individuals, new_individuals):
    """Detect removed named individuals."""
    removed = []
    for uri in old_individuals:
        if uri not in new_individuals:
            removed.append((uri, old_individuals[uri]))
    return removed


def format_uri(uri):
    """Format URI for display."""
    uri_str = str(uri)
    # Show local name + last part of namespace
    local = uri_str.split("/")[-1]
    namespace = "/".join(uri_str.split("/")[:-1])
    return f"{local} ({namespace})"


def write_report(output_file, old_file, new_file, results):
    """Write formatted report."""
    lines = []

    lines.append("=" * 80)
    lines.append("BREAKING CHANGES DETECTION REPORT")
    lines.append("=" * 80)
    lines.append(f"\nBaseline (Old): {old_file}")
    lines.append(f"New Version:    {new_file}")
    lines.append("")

    removed_classes = results["removed_classes"]
    removed_properties = results["removed_properties"]
    changed_ranges = results["changed_ranges"]
    removed_individuals = results["removed_individuals"]

    has_breaking = bool(
        removed_classes or removed_properties or changed_ranges or removed_individuals
    )

    if has_breaking:
        lines.append("STATUS: BREAKING CHANGES DETECTED")
    else:
        lines.append("STATUS: No breaking changes detected")

    lines.append("\n" + "=" * 80)
    lines.append("SUMMARY")
    lines.append("=" * 80)
    lines.append(f"Removed Classes:           {len(removed_classes)}")
    lines.append(f"Removed Properties:        {len(removed_properties)}")
    lines.append(f"Changed Ranges/Domains:    {len(changed_ranges)}")
    lines.append(f"Removed Individuals:       {len(removed_individuals)}")

    if removed_classes:
        lines.append("\n" + "-" * 80)
        lines.append("REMOVED CLASSES")
        lines.append("-" * 80)
        for uri, info in sorted(removed_classes, key=lambda x: str(x[0])):
            lines.append(f"\n  {format_uri(uri)}")
            if info.get("label"):
                lines.append(f"    Label: {info['label']}")
            if info.get("comment"):
                lines.append(f"    Comment: {info['comment'][:80]}...")

    if removed_properties:
        lines.append("\n" + "-" * 80)
        lines.append("REMOVED PROPERTIES")
        lines.append("-" * 80)
        for uri, info in sorted(removed_properties, key=lambda x: str(x[0])):
            lines.append(f"\n  {format_uri(uri)}")
            lines.append(f"    Type: {info['type']}")
            if info.get("label"):
                lines.append(f"    Label: {info['label']}")

    if changed_ranges:
        lines.append("\n" + "-" * 80)
        lines.append("CHANGED PROPERTY RANGES/DOMAINS")
        lines.append("-" * 80)
        for change in sorted(changed_ranges, key=lambda x: str(x["uri"])):
            lines.append(f"\n  {format_uri(change['uri'])}")
            lines.append(f"    Changed: {change['property']}")
            lines.append(f"    Old: {format_uri(change['old']) if change['old'] else 'None'}")
            lines.append(f"    New: {format_uri(change['new']) if change['new'] else 'None'}")

    if removed_individuals:
        lines.append("\n" + "-" * 80)
        lines.append("REMOVED INDIVIDUALS")
        lines.append("-" * 80)
        for uri, info in sorted(removed_individuals, key=lambda x: str(x[0])):
            lines.append(f"\n  {format_uri(uri)}")
            if info.get("label"):
                lines.append(f"    Label: {info['label']}")

    lines.append("\n" + "=" * 80)

    report_text = "\n".join(lines)

    if output_file:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report_text)
            print(f"Report written to: {output_file}")
        except Exception as e:
            print(f"Error writing report: {e}", file=sys.stderr)
    else:
        print(report_text)

    return has_breaking


def main():
    """Main entry point."""
    args = parse_arguments()

    # Validate inputs
    if not args.old_file.exists():
        print(f"Error: Old file not found: {args.old_file}", file=sys.stderr)
        sys.exit(1)

    if not args.new_file.exists():
        print(f"Error: New file not found: {args.new_file}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading baseline:  {args.old_file}")
    old_graph = load_graph(args.old_file)

    print(f"Loading new version: {args.new_file}")
    new_graph = load_graph(args.new_file)

    # Extract entities
    print("Analyzing classes...")
    old_classes = extract_classes(old_graph)
    new_classes = extract_classes(new_graph)

    print("Analyzing properties...")
    old_properties = extract_properties(old_graph)
    new_properties = extract_properties(new_graph)

    print("Analyzing individuals...")
    old_individuals = extract_individuals(old_graph)
    new_individuals = extract_individuals(new_graph)

    # Detect changes
    results = {
        "removed_classes": detect_removed_classes(old_classes, new_classes),
        "removed_properties": detect_removed_properties(old_properties, new_properties),
        "changed_ranges": detect_changed_ranges(old_properties, new_properties),
        "removed_individuals": detect_removed_individuals(old_individuals, new_individuals),
    }

    # Write report
    has_breaking = write_report(args.report_file, args.old_file, args.new_file, results)

    # Exit code
    if has_breaking and args.exit_on_breaking:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
