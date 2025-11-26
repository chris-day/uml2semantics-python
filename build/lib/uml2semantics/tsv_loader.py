import csv
from pathlib import Path
from typing import Optional
from .model import (
    Model,
    UmlClass,
    UmlEnumeration,
    UmlEnumLiteral,
    UmlDatatype,
    UmlAttribute,
)


def _read_tsv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            yield {(k or "").strip(): (v or "").strip() for k, v in row.items()}


def _to_int(value: str) -> Optional[int]:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def load_model(
    classes_tsv: Optional[Path] = None,
    enums_tsv: Optional[Path] = None,
    enum_literals_tsv: Optional[Path] = None,
    datatypes_tsv: Optional[Path] = None,
    attributes_tsv: Optional[Path] = None,
) -> Model:
    model = Model()

    if classes_tsv:
        for r in _read_tsv(classes_tsv):
            curie = r.get("Curie") or None
            name = r.get("Name") or None
            definition = r.get("Definition") or None
            parents = r.get("ParentNames") or ""
            parent_curie_list = [p.strip() for p in parents.split("|") if p.strip()]
            is_abstract = (r.get("IsAbstract") or "").lower() in ("true", "1", "yes", "y")
            choice_of_raw = r.get("ChoiceOf") or ""
            choice_of = [c.strip() for c in choice_of_raw.split("|") if c.strip()]
            choice_semantics = r.get("ChoiceSemantics") or None
            cls = UmlClass(
                curie=curie,
                name=name,
                definition=definition,
                parent_curie_list=parent_curie_list,
                is_abstract=is_abstract,
                choice_of=choice_of,
                choice_semantics=choice_semantics,
            )
            key = curie or name
            if key:
                model.classes[key] = cls

    if enums_tsv:
        for r in _read_tsv(enums_tsv):
            curie = r.get("Curie") or None
            name = r.get("Name") or None
            definition = r.get("Definition") or None
            en = UmlEnumeration(curie=curie, name=name, definition=definition)
            key = curie or name
            if key:
                model.enumerations[key] = en

    if enum_literals_tsv:
        for r in _read_tsv(enum_literals_tsv):
            enum_ref = r.get("Enumeration") or ""
            curie = r.get("Curie") or None
            name = r.get("Name") or None
            definition = r.get("Definition") or None
            if enum_ref:
                lit = UmlEnumLiteral(
                    enumeration=enum_ref,
                    curie=curie,
                    name=name,
                    definition=definition,
                )
                model.enum_literals.append(lit)

    if datatypes_tsv:
        for r in _read_tsv(datatypes_tsv):
            curie = r.get("Curie") or None
            name = r.get("Name") or None
            base = r.get("BaseDatatype") or ""
            definition = r.get("Definition") or None
            dt = UmlDatatype(
                curie=curie,
                name=name,
                base_datatype=base,
                definition=definition,
                pattern=r.get("Pattern") or None,
                min_length=_to_int(r.get("MinLength") or ""),
                max_length=_to_int(r.get("MaxLength") or ""),
                min_inclusive=r.get("MinInclusive") or None,
                max_inclusive=r.get("MaxInclusive") or None,
                min_exclusive=r.get("MinExclusive") or None,
                max_exclusive=r.get("MaxExclusive") or None,
                total_digits=_to_int(r.get("TotalDigits") or ""),
                fraction_digits=_to_int(r.get("FractionDigits") or ""),
            )
            key = curie or name
            if key:
                model.datatypes[key] = dt

    if attributes_tsv:
        for r in _read_tsv(attributes_tsv):
            class_ref = r.get("Class") or ""
            if not class_ref:
                continue
            curie = r.get("Curie") or None
            name = r.get("Name") or None
            if not name:
                raise ValueError(f"Attribute for class '{class_ref}' with CURIE '{curie}' is missing a Name; TSV Name must be populated.")
            type_ref = r.get("ClassEnumOrPrimitiveType") or ""
            definition = r.get("Definition") or None
            min_mult = r.get("MinMultiplicity") or ""
            max_mult = r.get("MaxMultiplicity") or ""
            min_card = _to_int(min_mult)
            if max_mult == "*":
                max_card = "*"
            else:
                max_card = _to_int(max_mult)
            attr = UmlAttribute(
                class_curie=class_ref,
                curie=curie,
                name=name,
                type_curie_or_primitive=type_ref,
                min_cardinality=min_card,
                max_cardinality=max_card,
                definition=definition,
                pattern=r.get("Pattern") or None,
                min_length=_to_int(r.get("MinLength") or ""),
                max_length=_to_int(r.get("MaxLength") or ""),
                min_inclusive=r.get("MinInclusive") or None,
                max_inclusive=r.get("MaxInclusive") or None,
                min_exclusive=r.get("MinExclusive") or None,
                max_exclusive=r.get("MaxExclusive") or None,
                total_digits=_to_int(r.get("TotalDigits") or ""),
                fraction_digits=_to_int(r.get("FractionDigits") or ""),
            )
            model.attributes.append(attr)

    return model
