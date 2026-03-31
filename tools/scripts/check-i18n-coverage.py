#!/usr/bin/env python3
"""
Check i18n coverage across COMET RS ontology TTL files.

Loads core TTL files and all language label files, then generates a coverage report
showing percentage of classes with labels in each target language.

Usage:
    python check-i18n-coverage.py --core path/to/core.ttl --labels path/to/labels/ [--target-langs en,zh,ja]

Target languages: en (English), zh (Chinese), ja (Japanese), ko (Korean),
                   de (German), fr (French), es (Spanish), pt (Portuguese),
                   hi (Hindi), ar (Arabic)
"""

import argparse
import sys
from pathlib import Path
from collections import defaultdict
from rdflib import Graph, RDFS, RDF, Namespace
from rdflib.namespace import SKOS


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Check internationalization coverage in COMET RS ontology."
    )
    parser.add_argument(
        "--core",
        type=Path,
        required=True,
        help="Path to core COMET TTL file",
    )
    parser.add_argument(
        "--labels",
        type=Path,
        required=True,
        help="Path to directory containing language label TTL files",
    )
    parser.add_argument(
        "--target-langs",
        type=str,
        default="en,zh,ja,ko,de,fr,es,pt,hi,ar",
        help="Comma-separated target language codes (default: en,zh,ja,ko,de,fr,es,pt,hi,ar)",
    )
    parser.add_argument(
        "--min-coverage",
        type=float,
        default=25.0,
        help="Minimum coverage percentage for target languages (exit 1 if below, default: 25)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed coverage per class",
    )
    return parser.parse_args()


def load_graph(core_path, labels_dir):
    """
    Load core TTL file and all label TTL files into a single graph.

    Args:
        core_path: Path to core TTL file
        labels_dir: Path to directory with language label TTL files

    Returns:
        rdflib.Graph: Merged graph with all data
    """
    graph = Graph()

    # Load core
    print(f"Loading core TTL: {core_path}")
    try:
        graph.parse(str(core_path), format="turtle")
    except Exception as e:
        print(f"Error loading core TTL: {e}", file=sys.stderr)
        sys.exit(1)

    # Load all label files
    labels_path = Path(labels_dir)
    if not labels_path.exists():
        print(f"Warning: Labels directory does not exist: {labels_dir}")
        return graph

    label_files = sorted(labels_path.glob("*.ttl"))
    if not label_files:
        print(f"Warning: No TTL files found in {labels_dir}")
        return graph

    print(f"Found {len(label_files)} label files in {labels_dir}")
    for label_file in label_files:
        try:
            print(f"  Loading: {label_file.name}")
            graph.parse(str(label_file), format="turtle")
        except Exception as e:
            print(f"  Warning: Error loading {label_file.name}: {e}")

    return graph


def extract_classes(graph):
    """
    Extract all OWL classes from graph.

    Args:
        graph: rdflib.Graph instance

    Returns:
        set: URIs of all classes
    """
    OWL = Namespace("http://www.w3.org/2002/07/owl#")
    classes = set()

    # Find all subjects that are owl:Class
    for s in graph.subjects(RDF.type, OWL.Class):
        classes.add(s)

    # Also find classes defined with rdf:type
    for s in graph.subjects(RDF.type, RDF.Type):
        classes.add(s)

    return classes


def count_labels_by_language(graph, classes):
    """
    Count labels per language for each class.

    Args:
        graph: rdflib.Graph instance
        classes: set of class URIs

    Returns:
        dict: {language_code: count} for each class URI
    """
    language_coverage = defaultdict(lambda: defaultdict(int))

    for cls in classes:
        # Count rdfs:label by language
        for label in graph.objects(cls, RDFS.label):
            lang = label.language
            if lang:
                language_coverage[cls][lang] += 1
            else:
                language_coverage[cls]['_unlang'] += 1

        # Count skos:prefLabel by language
        for label in graph.objects(cls, SKOS.prefLabel):
            lang = label.language
            if lang:
                language_coverage[cls][lang] += 1

    return language_coverage


def calculate_coverage(language_coverage, target_langs):
    """
    Calculate coverage percentages for target languages.

    Args:
        language_coverage: dict from count_labels_by_language
        target_langs: list of target language codes

    Returns:
        dict: {language: percentage_of_classes_with_label}
    """
    total_classes = len(language_coverage)
    if total_classes == 0:
        return {}

    coverage = {}
    for lang in target_langs:
        classes_with_label = sum(
            1 for labels in language_coverage.values()
            if lang in labels
        )
        percentage = (classes_with_label / total_classes) * 100
        coverage[lang] = {
            'count': classes_with_label,
            'percentage': percentage,
            'total': total_classes,
        }

    return coverage


def print_coverage_table(coverage):
    """
    Print coverage report as formatted table.

    Args:
        coverage: dict from calculate_coverage
    """
    print("\n" + "=" * 70)
    print("LANGUAGE COVERAGE REPORT")
    print("=" * 70)

    # Header
    print(f"{'Language':<15} {'Count':<10} {'Coverage %':<15} {'Status':<10}")
    print("-" * 70)

    # Rows
    for lang in sorted(coverage.keys()):
        data = coverage[lang]
        count = data['count']
        percentage = data['percentage']
        total = data['total']

        # Status indicator
        if percentage >= 100:
            status = "COMPLETE"
        elif percentage >= 75:
            status = "GOOD"
        elif percentage >= 50:
            status = "PARTIAL"
        elif percentage >= 25:
            status = "MINIMAL"
        else:
            status = "MISSING"

        print(
            f"{lang:<15} {count}/{total:<7} {percentage:>6.1f}%         {status:<10}"
        )

    print("=" * 70)


def check_minimum_coverage(coverage, min_coverage):
    """
    Check if all target languages meet minimum coverage.

    Args:
        coverage: dict from calculate_coverage
        min_coverage: minimum percentage threshold

    Returns:
        bool: True if all languages meet threshold, False otherwise
    """
    below_threshold = []
    for lang, data in sorted(coverage.items()):
        if data['percentage'] < min_coverage:
            below_threshold.append((lang, data['percentage']))

    if below_threshold:
        print(f"\nWARNING: The following languages are below {min_coverage}% coverage:")
        for lang, pct in below_threshold:
            print(f"  {lang}: {pct:.1f}%")
        return False
    return True


def print_detailed_coverage(language_coverage, target_langs, verbose):
    """
    Print detailed per-class coverage if verbose mode enabled.

    Args:
        language_coverage: dict from count_labels_by_language
        target_langs: list of target language codes
        verbose: bool, whether to print details
    """
    if not verbose:
        return

    print("\nDETAILED COVERAGE BY CLASS:")
    print("-" * 100)

    # Create header with target languages
    header = "Class URI"
    for lang in target_langs:
        header += f" | {lang}"
    print(header)
    print("-" * 100)

    # Print coverage for each class
    for cls in sorted(language_coverage.keys(), key=str):
        labels = language_coverage[cls]
        row = str(cls)[-50:]  # Show last 50 chars of URI

        for lang in target_langs:
            if lang in labels:
                row += f" | YES"
            else:
                row += f" | -"

        print(row)


def main():
    """Main entry point."""
    args = parse_arguments()

    # Validate paths
    if not args.core.exists():
        print(f"Error: Core TTL file not found: {args.core}", file=sys.stderr)
        sys.exit(1)

    target_langs = [l.strip() for l in args.target_langs.split(",")]

    # Load graph
    graph = load_graph(args.core, args.labels)
    print(f"Loaded graph with {len(graph)} triples")

    # Extract classes
    classes = extract_classes(graph)
    print(f"Found {len(classes)} classes")

    if not classes:
        print("Warning: No classes found in graph")
        sys.exit(1)

    # Count labels by language
    language_coverage = count_labels_by_language(graph, classes)

    # Calculate coverage
    coverage = calculate_coverage(language_coverage, target_langs)

    # Print report
    print_coverage_table(coverage)
    print_detailed_coverage(language_coverage, target_langs, args.verbose)

    # Check minimum coverage
    all_meet_threshold = check_minimum_coverage(coverage, args.min_coverage)

    # Exit code
    if not all_meet_threshold:
        sys.exit(1)
    else:
        print(f"\nAll target languages meet {args.min_coverage}% coverage threshold.")
        sys.exit(0)


if __name__ == "__main__":
    main()
