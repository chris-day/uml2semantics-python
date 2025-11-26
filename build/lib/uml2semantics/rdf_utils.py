from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Iterable

from rdflib import Graph, Namespace, Literal, BNode, RDF, RDFS, OWL, XSD
from rdflib.collection import Collection


ISO20022 = Namespace("urn:iso:std:iso:20022:tech:xsd:")
ISO20022DT = Namespace("urn:iso:std:iso:20022:tech:xsd-dt:")
ISO20022CD = Namespace("urn:iso:std:iso:20022:tech:xsd-cd:")


FACET_MAP = {
    "MinLength": XSD.minLength,
    "MaxLength": XSD.maxLength,
    "Pattern": XSD.pattern,
    "MinInclusive": XSD.minInclusive,
    "MaxInclusive": XSD.maxInclusive,
    "MinExclusive": XSD.minExclusive,
    "MaxExclusive": XSD.maxExclusive,
    "TotalDigits": XSD.totalDigits,
    "FractionDigits": XSD.fractionDigits,
}


@dataclass
class DatatypeFacet:
    key: str
    value: str


@dataclass
class DatatypeDef:
    curie: str
    name: str
    base_datatype: str
    definition: Optional[str] = None
    facets: Dict[str, DatatypeFacet] = field(default_factory=dict)

    @property
    def is_decimal_with_fraction_digits(self) -> bool:
        return (
            self.base_datatype == str(XSD.decimal) or self.base_datatype.endswith("#decimal")
        ) and "FractionDigits" in self.facets


def normalise_base_datatype(iri_or_curie: str) -> str:
    """Normalise common XSD CURIEs / IRIs into a full XSD IRI string."""
    if iri_or_curie.startswith("xsd:"):
        return str(getattr(XSD, iri_or_curie.split(":", 1)[1]))
    if iri_or_curie.startswith(str(XSD)):
        return iri_or_curie
    # Fall back to xsd:string as a safe default (caller can warn/log)
    return str(XSD.string)


def add_namespaces(g: Graph) -> None:
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("owl", OWL)
    g.bind("xsd", XSD)
    g.bind("iso20022", ISO20022)
    g.bind("iso20022dt", ISO20022DT)
    g.bind("iso20022cd", ISO20022CD)


def make_datatype_restriction(g: Graph, base_iri: str, facets: Iterable[DatatypeFacet]) -> BNode:
    """Create an OWL 2 datatype restriction node.

    Produces blank nodes of the form:

      _:d rdf:type rdfs:Datatype ;
          owl:onDatatype  xsd:string ;
          owl:withRestrictions (
              [ xsd:minLength "1"^^xsd:integer ]
              [ xsd:maxLength "35"^^xsd:integer ]
          ) .
    """
    restriction_node = BNode()
    base = base_iri

    g.add((restriction_node, RDF.type, RDFS.Datatype))
    g.add((restriction_node, OWL.onDatatype, base))

    coll_bnode = BNode()
    g.add((restriction_node, OWL.withRestrictions, coll_bnode))

    members = []
    for facet in facets:
        predicate = FACET_MAP.get(facet.key)
        if predicate is None:
            continue
        facet_bnode = BNode()
        # Length / digits facets are integers; pattern is plain string
        if facet.key in {"MinLength", "MaxLength", "TotalDigits", "FractionDigits"}:
            lit = Literal(int(facet.value), datatype=XSD.integer)
        else:
            lit = Literal(facet.value)
        g.add((facet_bnode, predicate, lit))
        members.append(facet_bnode)

    Collection(g, coll_bnode, members)
    return restriction_node


def add_label_and_definition(g: Graph, node, name: Optional[str], definition: Optional[str]) -> None:
    if name:
        g.add((node, RDFS.label, Literal(name)))
    if definition:
        g.add((node, RDFS.comment, Literal(definition)))
