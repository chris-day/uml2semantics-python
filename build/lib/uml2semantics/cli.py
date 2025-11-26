from __future__ import annotations

import argparse
from pathlib import Path

from .converter import Uml2OwlConverter, PrefixConfig
from .tsv import read_tsv


def _guess_format(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".ttl":
        return "turtle"
    if ext == ".nt":
        return "nt"
    if ext in (".jsonld", ".json"):
        return "json-ld"
    return "xml"


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="uml2semantics",
        description="Convert UML-style TSV specifications into an OWL 2 ontology.",
    )

    p.add_argument("-c", "--classes", required=True, help="TSV file with Classes")
    p.add_argument("-a", "--attributes", required=True, help="TSV file with Attributes / Associations")
    p.add_argument("-e", "--enumerations", help="TSV file with Enumerations (optional)")
    p.add_argument("-n", "--enum-values", help="TSV file with Enumeration Named Values (optional)")
    p.add_argument("--datatypes", help="TSV with Datatypes (optional)")
    p.add_argument("--annotation-properties", help="TSV with Annotation Properties (optional)")
    p.add_argument("--annotations", help="TSV with Annotations (optional)")
    p.add_argument("-o", "--output", required=True, help="Output ontology file. Format inferred from extension")
    p.add_argument("-p", "--prefix",
                   help="Prefix mapping, e.g. 'iso:http://example.org/ns#' or multiple separated by commas.")
    p.add_argument("-i", "--ontology-iri", required=True, help="Ontology IRI / base IRI.")

    return p


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    prefixes = PrefixConfig.from_string(args.prefix).prefixes
    conv = Uml2OwlConverter(base_iri=args.ontology_iri, prefixes=prefixes)

    class_rows = read_tsv(args.classes)
    attr_rows = read_tsv(args.attributes)
    enum_rows = read_tsv(args.enumerations)
    enum_val_rows = read_tsv(args.enum_values)
    datatype_rows = read_tsv(args.datatypes)
    ann_prop_rows = read_tsv(args.annotation_properties)
    ann_rows = read_tsv(args.annotations)

    if ann_prop_rows:
        conv.add_annotation_properties(ann_prop_rows)

    if datatype_rows:
        conv.add_datatypes(datatype_rows)

    conv.add_classes(class_rows)

    if enum_rows:
        conv.add_enumerations(enum_rows)
    if enum_val_rows:
        conv.add_enum_values(enum_val_rows)

    conv.add_attributes(attr_rows)

    if ann_rows:
        conv.add_annotations(ann_rows)

    out_path = Path(args.output)
    fmt = _guess_format(out_path)

    conv.graph.serialize(destination=str(out_path), format=fmt)
    print(f"uml2semantics: wrote ontology to {out_path} (format={fmt})")
