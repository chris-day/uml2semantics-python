
from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from .model import (
    Model,
    UmlAttribute,
    UmlClass,
    UmlDatatype,
    UmlEnumLiteral,
    UmlEnumeration,
)


def _read_tsv(path: Optional[Path]) -> Iterable[Dict[str, str]]:
    if path is None:
        return []
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            # Normalise keys (strip BOM / whitespace)
            cleaned = {k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            yield cleaned


def _b(s: Optional[str]) -> Optional[bool]:
    if s is None:
        return None
    v = s.strip().lower()
    if v in {"true", "t", "yes", "y", "1"}:
        return True
    if v in {"false", "f", "no", "n", "0"}:
        return False
    return None


def _i(s: Optional[str]) -> Optional[int]:
    if s is None:
        return None
    s = s.strip()
    if not s or s == "*":
        return None
    try:
        return int(s)
    except ValueError:
        return None


def load_model(
    class_tsv: Path,
    attribute_tsv: Optional[Path] = None,
    enumeration_tsv: Optional[Path] = None,
    enum_individuals_tsv: Optional[Path] = None,
    datatypes_tsv: Optional[Path] = None,
) -> Model:
    classes: Dict[str, UmlClass] = {}
    attributes: List[UmlAttribute] = []
    enumerations: Dict[str, UmlEnumeration] = {}
    enum_literals: List[UmlEnumLiteral] = []
    datatypes: Dict[str, UmlDatatype] = {}

    # --- Classes ---
    for row in _read_tsv(class_tsv):
        name = row.get("name") or row.get("Name")
        iri = row.get("iri") or row.get("IRI") or row.get("Iri")
        if not name or not iri:
            continue
        is_abstract = _b(row.get("isAbstract") or row.get("Abstract") or row.get("is_abstract")) or False
        super_classes_str = row.get("superClass") or row.get("SuperClass") or row.get("SuperClasses") or ""
        super_classes = [s.strip() for s in super_classes_str.split(",") if s.strip()]
        definition = row.get("definition") or row.get("Definition")
        classes[name] = UmlClass(
            name=name,
            iri=iri,
            definition=definition,
            is_abstract=is_abstract,
            super_classes=super_classes,
        )

    # --- Attributes ---
    if attribute_tsv:
        for row in _read_tsv(attribute_tsv):
            owner = row.get("class") or row.get("Class") or row.get("Owner")
            name = row.get("name") or row.get("Name")
            type_name = row.get("type") or row.get("Type") or row.get("ClassEnumOrPrimitiveType")
            if not owner or not name or not type_name:
                continue
            min_card = _i(row.get("minCardinality") or row.get("MinMultiplicity") or row.get("min"))
            max_card = _i(row.get("maxCardinality") or row.get("MaxMultiplicity") or row.get("max"))
            definition = row.get("definition") or row.get("Definition")
            attributes.append(
                UmlAttribute(
                    owner=owner,
                    name=name,
                    type_name=type_name,
                    min_cardinality=min_card,
                    max_cardinality=max_card,
                    definition=definition,
                )
            )

    # --- Enumerations ---
    if enumeration_tsv:
        for row in _read_tsv(enumeration_tsv):
            name = row.get("name") or row.get("Name")
            iri = row.get("iri") or row.get("IRI") or row.get("Iri")
            if not name or not iri:
                continue
            definition = row.get("definition") or row.get("Definition")
            enumerations[name] = UmlEnumeration(name=name, iri=iri, definition=definition)

    # --- Enum literals ---
    if enum_individuals_tsv:
        for row in _read_tsv(enum_individuals_tsv):
            enumeration = row.get("enumeration") or row.get("Enumeration")
            name = row.get("name") or row.get("Name")
            iri = row.get("iri") or row.get("IRI") or row.get("Iri")
            if not enumeration or not name or not iri:
                continue
            definition = row.get("definition") or row.get("Definition")
            enum_literals.append(
                UmlEnumLiteral(
                    enumeration=enumeration,
                    name=name,
                    iri=iri,
                    definition=definition,
                )
            )

    # --- Datatypes ---
    if datatypes_tsv:
        for row in _read_tsv(datatypes_tsv):
            name = row.get("name") or row.get("Name")
            iri = row.get("iri") or row.get("IRI") or row.get("Iri")
            base_iri = row.get("baseIri") or row.get("BaseIRI") or row.get("Base")
            if not name or not iri:
                continue
            dt = UmlDatatype(
                name=name,
                iri=iri,
                base_iri=base_iri,
            )
            # Optional facet columns (keep naming tolerant)
            dt.min_inclusive = row.get("minInclusive") or row.get("MinInclusive")
            dt.max_inclusive = row.get("maxInclusive") or row.get("MaxInclusive")
            dt.min_length = _i(row.get("minLength") or row.get("MinLength"))
            dt.max_length = _i(row.get("maxLength") or row.get("MaxLength"))
            datatypes[name] = dt

    return Model(
        classes=classes,
        attributes=attributes,
        enumerations=enumerations,
        enum_literals=enum_literals,
        datatypes=datatypes,
    )
