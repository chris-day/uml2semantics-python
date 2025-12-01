import argparse
import logging
from pathlib import Path

from rdflib.namespace import OWL
from rdflib import URIRef

from .tsv_loader import load_model
from .ontology_builder import build_ontology

VERSION = "0.9.29"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert UML-style TSV files to an OWL ontology."
    )

    parser.add_argument("--classes", "-c", type=Path, help="Classes TSV file")
    parser.add_argument("--attributes", "-a", type=Path, help="Attributes TSV file")
    parser.add_argument("--enumerations", "-e", type=Path, help="Enumerations TSV file")
    parser.add_argument("--enum-values", "-n", type=Path, help="Enumeration named values TSV file")
    parser.add_argument("--datatypes", "-d", type=Path, help="Datatypes TSV file")
    parser.add_argument("--annotation-properties", type=Path, help="Annotation properties TSV file")
    parser.add_argument("--annotations", type=Path, help="Annotations TSV file")

    parser.add_argument("--output", "-o", type=Path, help="Output ontology file")
    parser.add_argument("--ontology-iri", "-i", type=str, help="Ontology IRI")
    parser.add_argument(
        "--prefixes",
        type=str,
        default="",
        help=(
            "Prefix declarations, e.g. "
            "iso20022=http://iso20022.org/iso20022#;"
            "iso20022dt=http://purl.org/iso20022/dt/;"
            "xsd=http://www.w3.org/2001/XMLSchema#"
        ),
    )
    parser.add_argument(
        "--prefix",
        dest="prefixes",
        type=str,
        help="Alias for --prefixes (comma/semicolon separated pfx=IRI entries)",
    )

    parser.add_argument(
        "--format",
        type=str,
        choices=["rdfxml", "turtle", "owlxml"],
        default="rdfxml",
        help="Serialisation format for the ontology",
    )

    parser.add_argument(
        "--xml-base",
        type=str,
        default=None,
        help="Optional xml:base for RDF/XML output",
    )

    parser.add_argument(
        "--profile",
        "-p",
        type=str,
        choices=["generic", "iso20022"],
        default="generic",
        help="Mapping profile to apply",
    )

    parser.add_argument(
        "--imports",
        action="append",
        metavar="IRI",
        help="Ontology IRI to import (repeatable)",
    )

    parser.add_argument(
        "--no-imports",
        action="store_true",
        help="Disable automatic imports",
    )

    parser.add_argument(
        "--validate",
        dest="validate",
        action="store_true",
        default=True,
        help="Enable structural validation",
    )
    parser.add_argument("--no-validate", dest="validate", action="store_false")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote validation warnings to errors",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        choices=["ERROR", "WARNING", "INFO", "DEBUG"],
        default="INFO",
        help="Logging verbosity",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and build ontology in memory without writing a file",
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information and exit",
    )

    args = parser.parse_args()

    if args.version:
        print(f"uml2semantics version {VERSION}")
        return

    logging.basicConfig(level=getattr(logging, args.log_level.upper()))

    if not args.ontology_iri:
        raise ValueError("You must provide --ontology-iri")

    logging.info("Loading model from TSV bundle...")
    model = load_model(
        classes_tsv=args.classes,
        enums_tsv=args.enumerations,
        enum_literals_tsv=args.enum_values,
        datatypes_tsv=args.datatypes,
        attributes_tsv=args.attributes,
        annotation_properties_tsv=args.annotation_properties,
        annotations_tsv=args.annotations,
    )

    logging.info("Building ontology graph...")
    if args.validate:
        logging.info("Validation enabled.")
        g = build_ontology(model, args.ontology_iri, args.prefixes, strict=args.strict)
    else:
        logging.info("Validation disabled.")
        g = build_ontology(model, args.ontology_iri, args.prefixes)

    if args.profile and args.profile != "generic":
        logging.info("Profile '%s' requested; profile-specific behavior is not implemented yet (no-op).", args.profile)

    if args.imports and not args.no_imports:
        for iri in args.imports:
            g.add((URIRef(args.ontology_iri), OWL.imports, URIRef(iri)))

    if args.dry_run:
        logging.info("Dry run complete; ontology not written to disk.")
        return

    if not args.output:
        raise ValueError("Output file is required unless running with --dry-run")

    fmt = args.format.lower()
    rdflib_fmt = fmt
    if fmt == "rdfxml":
        rdflib_fmt = "xml"
    elif fmt == "turtle":
        rdflib_fmt = "turtle"
    elif fmt == "owlxml":
        rdflib_fmt = "owlxml"

    logging.info("Serialising ontology as %s to %s", rdflib_fmt, args.output)
    if rdflib_fmt == "xml":
        g.serialize(destination=str(args.output), format=rdflib_fmt, xml_base=args.xml_base)
    else:
        g.serialize(destination=str(args.output), format=rdflib_fmt)

    logging.info("Ontology successfully written.")


if __name__ == "__main__":
    main()
