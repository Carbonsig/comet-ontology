#!/usr/bin/env python3
"""
Generate a searchable HTML glossary from COMET RS ontology TTL files.

Loads core TTL and language label files, extracts all classes with their labels,
definitions, and layers, then generates a static HTML glossary with client-side
search and filtering.

Usage:
    python generate-glossary.py --core path/to/core.ttl --labels path/to/labels/ \
                                 --output glossary.html [--langs en,zh,de,ja,ko,fr,es,pt,hi,ar]
"""

import argparse
import sys
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from rdflib import Graph, RDFS, RDF, Namespace
from rdflib.namespace import SKOS, DCTERMS


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate searchable HTML glossary from COMET RS ontology."
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
        "--output",
        type=Path,
        default=Path("glossary.html"),
        help="Output HTML file path (default: glossary.html)",
    )
    parser.add_argument(
        "--langs",
        type=str,
        default="en,zh,de,ja,ko,fr,es,pt,hi,ar",
        help="Comma-separated language codes to include (default: en,zh,de,ja,ko,fr,es,pt,hi,ar)",
    )
    parser.add_argument(
        "--title",
        type=str,
        default="COMET Responsible Steel Glossary",
        help="HTML page title",
    )
    return parser.parse_args()


def load_graph(core_path, labels_dir):
    """Load core TTL and label files into single graph."""
    graph = Graph()

    print(f"Loading core TTL: {core_path}")
    try:
        graph.parse(str(core_path), format="turtle")
    except Exception as e:
        print(f"Error loading core TTL: {e}", file=sys.stderr)
        sys.exit(1)

    labels_path = Path(labels_dir)
    if labels_path.exists():
        label_files = sorted(labels_path.glob("*.ttl"))
        for label_file in label_files:
            try:
                graph.parse(str(label_file), format="turtle")
            except Exception as e:
                print(f"Warning: Error loading {label_file.name}: {e}")

    print(f"Loaded graph with {len(graph)} triples")
    return graph


def extract_classes(graph):
    """Extract all OWL classes from graph."""
    OWL = Namespace("http://www.w3.org/2002/07/owl#")
    classes = set()

    for s in graph.subjects(RDF.type, OWL.Class):
        classes.add(s)

    return classes


def get_class_labels(graph, cls, languages):
    """
    Get labels for a class in specified languages.

    Returns:
        dict: {language_code: label_text}
    """
    labels = {}

    for lang in languages:
        # Try rdfs:label first
        for label in graph.objects(cls, RDFS.label):
            if label.language == lang:
                labels[lang] = str(label)
                break

        # Fall back to skos:prefLabel
        if lang not in labels:
            for label in graph.objects(cls, SKOS.prefLabel):
                if label.language == lang:
                    labels[lang] = str(label)
                    break

    return labels


def get_class_definition(graph, cls, language="en"):
    """Get definition for a class (skos:definition preferred)."""
    # Try skos:definition
    for definition in graph.objects(cls, SKOS.definition):
        if definition.language == language:
            return str(definition)

    # Fall back to rdfs:comment
    for comment in graph.objects(cls, RDFS.comment):
        if comment.language == language:
            return str(comment)

    return None


def get_class_layer(graph, cls):
    """
    Determine which ontology layer a class belongs to.

    Common patterns: core, properties, individuals, etc.
    """
    uri_str = str(cls)

    if "properties" in uri_str:
        return "Properties"
    elif "individuals" in uri_str:
        return "Individuals"
    elif "measurement" in uri_str:
        return "Measurement"
    elif "alignment" in uri_str:
        return "Alignment"
    else:
        return "Core"


def build_glossary_data(graph, classes, languages):
    """
    Build structured glossary data for HTML generation.

    Returns:
        list of dicts with class information
    """
    glossary = []

    for cls in sorted(classes, key=str):
        labels = get_class_labels(graph, cls, languages)

        # Skip if no English label (English is fallback)
        if "en" not in labels:
            continue

        definition = get_class_definition(graph, cls, "en")
        layer = get_class_layer(graph, cls)

        entry = {
            "iri": str(cls),
            "local_name": str(cls).split("/")[-1],
            "layer": layer,
            "labels": labels,
            "definition": definition,
        }

        glossary.append(entry)

    return glossary


def generate_html(glossary, languages, title, output_path):
    """
    Generate static HTML glossary with client-side search.

    Args:
        glossary: list of class info dicts
        languages: list of language codes
        title: page title
        output_path: Path to write HTML
    """
    # Language display names
    lang_names = {
        "en": "English",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "de": "German",
        "fr": "French",
        "es": "Spanish",
        "pt": "Portuguese",
        "hi": "Hindi",
        "ar": "Arabic",
    }

    # Build language columns HTML
    lang_columns = ""
    for lang in languages:
        lang_columns += f'<th>{lang_names.get(lang, lang.upper())}</th>'

    # Build table rows
    rows_html = ""
    glossary_json = json.dumps(glossary)

    for entry in glossary:
        row = f"""
        <tr class="glossary-row" data-searchable="{entry['local_name']} {entry['iri']} {' '.join(entry['labels'].values())}">
            <td class="iri-cell">{entry['local_name']}</td>
            <td class="layer-cell">{entry['layer']}</td>
"""
        for lang in languages:
            label = entry["labels"].get(lang, "—")
            row += f'            <td class="label-cell">{label}</td>\n'

        row += """        </tr>
"""
        rows_html += row

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f5f5;
            color: #2c2c2c;
            line-height: 1.5;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px 20px;
        }}

        header {{
            margin-bottom: 40px;
            text-align: center;
        }}

        h1 {{
            font-size: 2.5rem;
            margin-bottom: 12px;
            font-weight: 600;
            color: #1a1a1a;
        }}

        .subtitle {{
            font-size: 1.1rem;
            color: #666;
            margin-bottom: 20px;
        }}

        .metadata {{
            font-size: 0.9rem;
            color: #999;
        }}

        .controls {{
            background: white;
            padding: 20px;
            border-radius: 4px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }}

        .search-box {{
            width: 100%;
            padding: 12px 16px;
            font-size: 1rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-family: inherit;
        }}

        .search-box:focus {{
            outline: none;
            border-color: #0066cc;
            box-shadow: 0 0 0 2px rgba(0, 102, 204, 0.1);
        }}

        .table-wrapper {{
            background: white;
            border-radius: 4px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        thead {{
            background: #f0f0f0;
            border-bottom: 2px solid #ddd;
            position: sticky;
            top: 0;
        }}

        th {{
            padding: 16px;
            text-align: left;
            font-weight: 600;
            font-size: 0.95rem;
            color: #333;
        }}

        td {{
            padding: 12px 16px;
            border-bottom: 1px solid #eee;
        }}

        tbody tr {{
            transition: background-color 0.15s ease;
        }}

        tbody tr:hover {{
            background: #f9f9f9;
        }}

        .iri-cell {{
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9rem;
            color: #0066cc;
            font-weight: 500;
        }}

        .layer-cell {{
            font-size: 0.85rem;
            background: #f5f5f5;
            color: #666;
            border-radius: 2px;
            padding: 4px 8px;
            display: inline-block;
        }}

        .label-cell {{
            font-size: 0.95rem;
        }}

        .hidden {{
            display: none;
        }}

        .result-count {{
            padding: 10px 16px;
            font-size: 0.9rem;
            color: #666;
            border-top: 1px solid #eee;
        }}

        .no-results {{
            padding: 40px;
            text-align: center;
            color: #999;
        }}

        footer {{
            margin-top: 40px;
            padding: 20px;
            text-align: center;
            color: #999;
            font-size: 0.9rem;
        }}

        @media (max-width: 1200px) {{
            h1 {{ font-size: 1.8rem; }}
            .container {{ padding: 20px 10px; }}
            th, td {{ padding: 10px; font-size: 0.9rem; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <div class="subtitle">Comprehensive reference of COMET Responsible Steel concepts</div>
            <div class="metadata">
                Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
                | Total entries: {len(glossary)}
            </div>
        </header>

        <div class="controls">
            <input
                type="text"
                id="searchInput"
                class="search-box"
                placeholder="Search by term, IRI, or definition... (press / to focus)"
                autocomplete="off"
            >
        </div>

        <div class="table-wrapper">
            <table id="glossaryTable">
                <thead>
                    <tr>
                        <th>Term IRI</th>
                        <th>Layer</th>
                        {lang_columns}
                    </tr>
                </thead>
                <tbody id="tableBody">
                    {rows_html}
                </tbody>
            </table>
            <div id="resultCount" class="result-count"></div>
        </div>

        <footer>
            <p>COMET Responsible Steel Ontology</p>
            <p>Material Intelligence | Responsible Steel Standard</p>
        </footer>
    </div>

    <script>
        const glossaryData = {glossary_json};
        const searchInput = document.getElementById('searchInput');
        const tableBody = document.getElementById('tableBody');
        const resultCount = document.getElementById('resultCount');
        const rows = tableBody.querySelectorAll('tr');

        // Focus search box on '/' key
        document.addEventListener('keydown', (e) => {{
            if (e.key === '/' && document.activeElement !== searchInput) {{
                e.preventDefault();
                searchInput.focus();
            }}
        }});

        // Search functionality
        searchInput.addEventListener('input', (e) => {{
            const query = e.target.value.toLowerCase().trim();
            let visibleCount = 0;

            rows.forEach((row) => {{
                const searchable = row.dataset.searchable.toLowerCase();
                const matches = query === '' || searchable.includes(query);

                row.classList.toggle('hidden', !matches);
                if (matches) visibleCount++;
            }});

            // Update result count
            if (query === '') {{
                resultCount.textContent = '';
            }} else {{
                resultCount.textContent = `Showing {{visibleCount}} of {{rows.length}} entries`;
            }}

            // Show no results message if needed
            const noResults = visibleCount === 0 && query !== '';
            if (noResults) {{
                resultCount.textContent = `No matches found for "{{query}}"`;
            }}
        }});

        // Initial focus
        searchInput.focus();
    </script>
</body>
</html>
"""

    # Write HTML file
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        print(f"\nGlossary generated successfully: {output_path}")
        print(f"Total entries: {len(glossary)}")
    except Exception as e:
        print(f"Error writing HTML file: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main entry point."""
    args = parse_arguments()

    # Validate paths
    if not args.core.exists():
        print(f"Error: Core TTL file not found: {args.core}", file=sys.stderr)
        sys.exit(1)

    languages = [l.strip() for l in args.langs.split(",")]

    # Load graph
    graph = load_graph(args.core, args.labels)

    # Extract classes
    classes = extract_classes(graph)
    print(f"Found {len(classes)} classes")

    if not classes:
        print("Warning: No classes found in graph")
        sys.exit(1)

    # Build glossary data
    glossary = build_glossary_data(graph, classes, languages)
    print(f"Built glossary with {len(glossary)} entries")

    # Generate HTML
    generate_html(glossary, languages, args.title, args.output)


if __name__ == "__main__":
    main()
