
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class UmlClass:
    name: str
    iri: str
    definition: Optional[str] = None
    is_abstract: bool = False
    super_classes: List[str] = field(default_factory=list)


@dataclass
class UmlAttribute:
    owner: str
    name: str
    type_name: str
    min_cardinality: Optional[int]
    max_cardinality: Optional[int]
    definition: Optional[str] = None


@dataclass
class UmlEnumeration:
    name: str
    iri: str
    definition: Optional[str] = None


@dataclass
class UmlEnumLiteral:
    enumeration: str
    name: str
    iri: str
    definition: Optional[str] = None


@dataclass
class UmlDatatype:
    name: str
    iri: str
    base_iri: Optional[str] = None
    # Facets are kept simple; if present, they are emitted as OWL 2 datatype restrictions.
    min_inclusive: Optional[str] = None
    max_inclusive: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None


@dataclass
class Model:
    classes: Dict[str, UmlClass]
    attributes: List[UmlAttribute]
    enumerations: Dict[str, UmlEnumeration]
    enum_literals: List[UmlEnumLiteral]
    datatypes: Dict[str, UmlDatatype]
