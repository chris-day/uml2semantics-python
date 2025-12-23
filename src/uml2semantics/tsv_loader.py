import csv
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from .model import (
    Model,
    UmlClass,
    UmlEnumeration,
    UmlEnumLiteral,
    UmlDatatype,
    UmlAttribute,
    AnnotationProperty,
    AnnotationAssertion,
    PropertyChain,
)


def _read_tsv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            yield {(k or "").strip(): (v or "").strip() for k, v in row.items()}


def _read_tsv_with_row(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for idx, row in enumerate(reader, start=2):
            yield idx, {(k or "").strip(): (v or "").strip() for k, v in row.items()}


def _to_int(value: str) -> Optional[int]:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _to_bool(value: str, default: bool = True) -> bool:
    if value is None or value == "":
        return default
    return value.strip().lower() not in ("false", "0", "no", "n")


def _is_iri(value: str) -> bool:
    if not value or " " in value:
        return False
    parsed = urlparse(value)
    return bool(parsed.scheme)


def _property_chain_error(row: int, column: str, message: str) -> None:
    raise ValueError(f"property_chains.tsv row {row} column '{column}': {message}")


def load_model(
    classes_tsv: Optional[Path] = None,
    enums_tsv: Optional[Path] = None,
    enum_literals_tsv: Optional[Path] = None,
    datatypes_tsv: Optional[Path] = None,
    attributes_tsv: Optional[Path] = None,
    annotation_properties_tsv: Optional[Path] = None,
    annotations_tsv: Optional[Path] = None,
    property_chains_tsv: Optional[Path] = None,
) -> Model:
    model = Model()

    # Classes (Name required)
    if classes_tsv:
        for r in _read_tsv(classes_tsv):
            curie = r.get("Curie") or None
            name = r.get("Name") or None
            if not name:
                raise ValueError(
                    f"Class with CURIE '{curie}' is missing a Name; TSV Name must be populated for all classes."
                )
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

    # Enumerations (Name required)
    if enums_tsv:
        for r in _read_tsv(enums_tsv):
            curie = r.get("Curie") or None
            name = r.get("Name") or None
            if not name:
                raise ValueError(
                    f"Enumeration with CURIE '{curie}' is missing a Name; TSV Name must be populated for all enumerations."
                )
            definition = r.get("Definition") or None
            en = UmlEnumeration(curie=curie, name=name, definition=definition)
            key = curie or name
            if key:
                model.enumerations[key] = en

    # Enumeration named values (Name optional)
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

    # Datatypes (Name optional but recommended)
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

    # Attributes (Name required)
    if attributes_tsv:
        for r in _read_tsv(attributes_tsv):
            class_ref = r.get("Class") or ""
            if not class_ref:
                continue
            curie = r.get("Curie") or None
            name = r.get("Name") or None
            if not name:
                raise ValueError(
                    f"Attribute for class '{class_ref}' with CURIE '{curie}' is missing a Name; TSV Name must be populated for all attributes."
                )
            # Support both spellings: Primitive / Primative
            type_ref = (
                r.get("ClassEnumOrPrimitiveType")
                or r.get("ClassEnumOrPrimativeType")
                or ""
            )
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

    # Annotation properties
    if annotation_properties_tsv:
        for r in _read_tsv(annotation_properties_tsv):
            curie = r.get("Curie") or None
            name = r.get("Name") or None
            definition = r.get("Definition") or None
            ap = AnnotationProperty(curie=curie, name=name, definition=definition)
            key = curie or name
            if key:
                model.annotation_properties[key] = ap

    # Annotation assertions
    if annotations_tsv:
        for r in _read_tsv(annotations_tsv):
            target = r.get("TargetCurie") or ""
            prop = r.get("AnnotationProperty") or ""
            value = r.get("Value") or ""
            lang = r.get("Language") or None
            dtype = r.get("Datatype") or None
            if not target or not prop or value == "":
                continue
            ann = AnnotationAssertion(
                target_curie=target,
                property_curie=prop,
                value=value,
                language=lang,
                datatype=dtype,
            )
            model.annotations.append(ann)

    # Property chains
    if property_chains_tsv:
        for row_num, r in _read_tsv_with_row(property_chains_tsv):
            enabled = _to_bool(r.get("enabled") or r.get("Enabled") or "", default=True)
            if not enabled:
                continue
            superprop = r.get("superproperty_iri") or r.get("SuperpropertyIri") or ""
            if not superprop:
                _property_chain_error(row_num, "superproperty_iri", "missing required IRI")
            if not _is_iri(superprop):
                _property_chain_error(row_num, "superproperty_iri", f"invalid IRI '{superprop}'")
            chain_raw = r.get("chain_property_iris") or r.get("ChainPropertyIris") or ""
            if not chain_raw:
                _property_chain_error(row_num, "chain_property_iris", "missing required chain list")
            chain_list = [c.strip() for c in chain_raw.split("|") if c.strip()]
            if len(chain_list) < 2:
                _property_chain_error(
                    row_num,
                    "chain_property_iris",
                    "property chain must have length >= 2",
                )
            for iri in chain_list:
                if not _is_iri(iri):
                    _property_chain_error(row_num, "chain_property_iris", f"invalid IRI '{iri}'")
            pc = PropertyChain(
                superproperty_iri=superprop,
                chain_property_iris=chain_list,
                label=r.get("label") or r.get("Label") or None,
                comment=r.get("comment") or r.get("Comment") or None,
                source=r.get("source") or r.get("Source") or None,
                enabled=True,
            )
            model.property_chains.append(pc)

    return model
