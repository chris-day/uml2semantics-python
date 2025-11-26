import argparse
from pathlib import Path
from .tsv_loader import load_model
from .ontology_builder import serialise_ontology


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert UML-style TSV files to an OWL ontology.")
    parser.add_argument("--classes", "-c", type=Path, help="Classes TSV file")
    parser.add_argument("--attributes", "-a", type=Path, help="Attributes TSV file")
    parser.add_argument("--enumerations", "-e", type=Path, help="Enumerations TSV file")
    parser.add_argument("--enum-values", "-n", type=Path, help="Enumeration named values TSV file")
    parser.add_argument("--datatypes", "-d", type=Path, help="Datatypes TSV file")
    parser.add_argument("--output", "-o", type=Path, required=True, help="Output ontology file")
    parser.add_argument("--ontology-iri", "-i", type=str, required=True, help="Ontology IRI")
    parser.add_argument("--prefixes", "-p", type=str, default="", help="Prefix declarations, e.g. iso=http://iso20022.org/iso20022#;xsd=http://www.w3.org/2001/XMLSchema#")
    parser.add_argument("--format", type=str, choices=["xml", "turtle"], default="xml", help="Serialisation format")
    parser.add_argument("--xml-base", type=str, default=None, help="Optional xml:base for RDF/XML")
    args = parser.parse_args()

    model = load_model(
        classes_tsv=args.classes,
        enums_tsv=args.enumerations,
        enum_literals_tsv=args.enum_values,
        datatypes_tsv=args.datatypes,
        attributes_tsv=args.attributes,
    )

    serialise_ontology(
        model=model,
        ontology_iri=args.ontology_iri,
        prefix_str=args.prefixes,
        output_path=args.output,
        format=args.format,
        xml_base=args.xml_base,
    )


if __name__ == "__main__":
    main()
