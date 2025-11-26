
from __future__ import annotations

import argparse
from pathlib import Path

from .ontology_builder import serialise_ontology
from .tsv_loader import load_model


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="uml2semantics",
        description="Convert UML model TSV exports into an OWL 2 ontology.",
    )

    p.add_argument(
        "-c",
        "--classes",
        required=True,
        type=Path,
        help="TSV file containing UML classes.",
    )
    p.add_argument(
        "-a",
        "--attributes",
        type=Path,
        help="TSV file containing UML attributes (associations + data-valued attributes).",
    )
    p.add_argument(
        "-e",
        "--enumerations",
        type=Path,
        help="TSV file containing UML enumerations.",
    )
    p.add_argument(
        "-n",
        "--enumeration-individuals",
        type=Path,
        help="TSV file containing enumeration individuals.",
    )
    p.add_argument(
        "--datatypes",
        type=Path,
        help="TSV file containing UML datatypes and optional OWL 2 facet information.",
    )
    p.add_argument(
        "--output",
        "-o",
        required=True,
        type=Path,
        help="Output ontology file (RDF/XML, .owl).",
    )
    p.add_argument(
        "--prefix",
        required=True,
        type=str,
        help='Comma-separated prefix mappings, e.g. "iso20022:http://iso20022.org/iso20022/,xsd:http://www.w3.org/2001/XMLSchema#".',
    )
    p.add_argument(
        "--ontology-iri",
        "-i",
        required=True,
        type=str,
        help="Ontology IRI to use as the base for generated entities.",
    )
    p.add_argument(
        "--format",
        default="xml",
        choices=["xml", "turtle", "nt", "n3"],
        help="Serialisation format for the output ontology (default: xml).",
    )

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    model = load_model(
        class_tsv=args.classes,
        attribute_tsv=args.attributes,
        enumeration_tsv=args.enumerations,
        enum_individuals_tsv=args.enumeration_individuals,
        datatypes_tsv=args.datatypes,
    )

    serialise_ontology(
        model=model,
        ontology_iri=args.ontology_iri,
        prefix_str=args.prefix,
        output=args.output,
        format=args.format,
    )


if __name__ == "__main__":
    main()
