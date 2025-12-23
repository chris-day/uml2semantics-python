from dataclasses import dataclass, field
from typing import Optional, List, Dict, Union


@dataclass
class UmlClass:
    curie: Optional[str]
    name: Optional[str]
    definition: Optional[str] = None
    parent_curie_list: List[str] = field(default_factory=list)
    is_abstract: bool = False
    choice_of: List[str] = field(default_factory=list)
    choice_semantics: Optional[str] = None


@dataclass
class UmlEnumeration:
    curie: Optional[str]
    name: Optional[str]
    definition: Optional[str] = None


@dataclass
class UmlEnumLiteral:
    enumeration: str
    curie: Optional[str]
    name: Optional[str]
    definition: Optional[str] = None


@dataclass
class UmlDatatype:
    curie: Optional[str]
    name: Optional[str]
    base_datatype: str
    definition: Optional[str] = None
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_inclusive: Optional[str] = None
    max_inclusive: Optional[str] = None
    min_exclusive: Optional[str] = None
    max_exclusive: Optional[str] = None
    total_digits: Optional[int] = None
    fraction_digits: Optional[int] = None


@dataclass
class UmlAttribute:
    class_curie: str
    curie: Optional[str]
    name: Optional[str]
    type_curie_or_primitive: str
    min_cardinality: Optional[int] = None
    max_cardinality: Optional[Union[int, str]] = None
    definition: Optional[str] = None
    pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_inclusive: Optional[str] = None
    max_inclusive: Optional[str] = None
    min_exclusive: Optional[str] = None
    max_exclusive: Optional[str] = None
    total_digits: Optional[int] = None
    fraction_digits: Optional[int] = None


@dataclass
class AnnotationProperty:
    curie: Optional[str]
    name: Optional[str]
    definition: Optional[str] = None


@dataclass
class AnnotationAssertion:
    target_curie: str
    property_curie: str
    value: str
    language: Optional[str] = None
    datatype: Optional[str] = None


@dataclass
class PropertyChain:
    superproperty_iri: str
    chain_property_iris: List[str]
    label: Optional[str] = None
    comment: Optional[str] = None
    source: Optional[str] = None
    enabled: bool = True


@dataclass
class Model:
    classes: Dict[str, UmlClass] = field(default_factory=dict)
    enumerations: Dict[str, UmlEnumeration] = field(default_factory=dict)
    enum_literals: List[UmlEnumLiteral] = field(default_factory=list)
    datatypes: Dict[str, UmlDatatype] = field(default_factory=dict)
    attributes: List[UmlAttribute] = field(default_factory=list)
    annotation_properties: Dict[str, AnnotationProperty] = field(default_factory=dict)
    annotations: List[AnnotationAssertion] = field(default_factory=list)
    property_chains: List[PropertyChain] = field(default_factory=list)
