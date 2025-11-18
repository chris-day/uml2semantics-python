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
    p.add_argument("-o", "--output", required=True, help="Output ontology file. Format inferred from extension")
    p.add_argument("-p", "--prefix",
                   help="Prefix mapping, e.g. 'iso:http://example.org/ns#' or multiple separated by commas.")
    p.add_argument("-i", "--ontology-iri", required=True, help="Ontology IRI / base IRI.")
    # Choice (Option B) optional sheets
    p.add_argument("--choices", help="TSV with Choices (ChoiceClass, Semantics, Definition)")
    p.add_argument("--choice-members", help="TSV with ChoiceMembers (ChoiceClass, Kind, Ref | Datatype, Property)")

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

    conv.add_classes(class_rows)

    # Optional enumerations
    if enum_rows:
        conv.add_enumerations(enum_rows)
    if enum_val_rows:
        conv.add_enum_values(enum_val_rows)

    # Attributes next
    conv.add_attributes(attr_rows)

    # Choice support
    conv.add_choices_from_classes(class_rows)
    # Optional external choice sheets
    if args.choices or args.choice_members:
        choices_rows = read_tsv(args.choices)
        choice_member_rows = read_tsv(args.choice_members)
        conv.add_choices(choices_rows, choice_member_rows)

    out_path = Path(args.output)
    fmt = _guess_format(out_path)

    conv.graph.serialize(destination=str(out_path), format=fmt)
    print(f"uml2semantics: wrote ontology to {out_path} (format={fmt})")
