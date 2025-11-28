import logging
from typing import List

from rdflib import RDF, RDFS, OWL, URIRef, BNode, Literal
from rdflib.namespace import XSD

from uml2semantics.model import Model, UmlClass, UmlAttribute
from uml2semantics.ontology_builder import build_ontology


def _rdf_list_members(g, head) -> List:
    members = []
    if head == RDF.nil:
        return members
    cursor = head
    while cursor and cursor != RDF.nil:
        first = g.value(cursor, RDF.first)
        if first is not None:
            members.append(first)
        cursor = g.value(cursor, RDF.rest)
        if cursor is None:
            break
    return members


def test_choice_prefers_curie_for_property_and_class():
    model = Model(
        classes={
            "ex:Foo": UmlClass(curie="ex:Foo", name="Foo", choice_of=["bar"]),
        },
        attributes=[
            UmlAttribute(
                class_curie="ex:Foo",
                curie="ex:bar",
                name="bar",
                type_curie_or_primitive="xsd:string",
                min_cardinality=1,
                max_cardinality=1,
            )
        ],
    )

    g = build_ontology(model, "http://example.com/ont#", "ex=http://example.com/")

    class_uri = URIRef("http://example.com/Foo")
    prop_uri = URIRef("http://example.com/bar")

    assert (class_uri, RDF.type, OWL.Class) in g
    assert (prop_uri, RDF.type, OWL.DatatypeProperty) in g

    # Find the choice union and ensure the restriction uses the CURIE-based property IRI.
    union = None
    for _, _, candidate in g.triples((class_uri, RDFS.subClassOf, None)):
        if (candidate, OWL.unionOf, None) in g:
            union = candidate
            break
    assert union is not None, "Choice union was not emitted"

    members = _rdf_list_members(g, g.value(union, OWL.unionOf))
    assert members, "Choice union has no members"

    for restr in members:
        assert isinstance(restr, BNode)
        assert (restr, OWL.onProperty, prop_uri) in g


def test_choice_min_zero_promoted_to_one():
    model = Model(
        classes={
            "ex:Foo": UmlClass(curie="ex:Foo", name="Foo", choice_of=["bar"]),
        },
        attributes=[
            UmlAttribute(
                class_curie="ex:Foo",
                curie="ex:bar",
                name="bar",
                type_curie_or_primitive="xsd:string",
                min_cardinality=0,
                max_cardinality=1,
            )
        ],
    )

    g = build_ontology(model, "http://example.com/ont#", "ex=http://example.com/")

    prop_uri = URIRef("http://example.com/bar")
    restrictions = list(g.subjects(OWL.onProperty, prop_uri))
    assert restrictions, "Restriction for choice attribute not emitted"

    has_cardinality_one = any(
        (r, OWL.cardinality, Literal(1, datatype=XSD.nonNegativeInteger)) in g for r in restrictions
    )
    assert has_cardinality_one, "Choice attribute cardinality was not promoted to 1"


def test_warns_when_falling_back_to_name(caplog):
    caplog.set_level(logging.WARNING)
    model = Model(
        classes={
            "NameOnly": UmlClass(curie=None, name="NameOnly", choice_of=[]),
        },
        attributes=[
            UmlAttribute(
                class_curie="NameOnly",
                curie=None,
                name="prop",
                type_curie_or_primitive="xsd:string",
                min_cardinality=0,
                max_cardinality=1,
            )
        ],
    )

    build_ontology(model, "http://example.com/ont#", "")

    warnings = [rec for rec in caplog.records if "missing a CURIE" in rec.message]
    assert warnings, "Expected a warning when falling back to Name without CURIE"
