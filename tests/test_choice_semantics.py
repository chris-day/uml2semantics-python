from rdflib import RDF, RDFS, OWL, URIRef

from uml2semantics.model import Model, UmlClass
from uml2semantics.ontology_builder import build_ontology


def test_choice_inclusive_union_only():
    model = Model(
        classes={
            "ex:Choice": UmlClass(curie="ex:Choice", name="Choice", choice_of=["ex:A", "B"]),
            "ex:A": UmlClass(curie="ex:A", name="A"),
            "B": UmlClass(curie=None, name="B"),
        }
    )
    g = build_ontology(model, "http://example.com/ont#", "ex=http://example.com/")

    choice_uri = URIRef("http://example.com/Choice")
    member_a = URIRef("http://example.com/A")
    member_b = URIRef("http://example.com/B")

    union = None
    for _, _, candidate in g.triples((choice_uri, RDFS.subClassOf, None)):
        if (candidate, OWL.unionOf, None) in g:
            union = candidate
            break
    assert union is not None, "Choice union was not emitted"

    members = list(g.items(g.value(union, OWL.unionOf)))
    assert member_a in members and member_b in members
    assert (choice_uri, OWL.disjointWith, member_a) not in g
    assert (choice_uri, OWL.disjointWith, member_b) not in g


def test_choice_exclusive_disjoint_with_members():
    model = Model(
        classes={
            "ex:Choice": UmlClass(
                curie="ex:Choice",
                name="Choice",
                choice_of=["ex:A", "ex:B"],
                choice_semantics="exclusive",
            ),
            "ex:A": UmlClass(curie="ex:A", name="A"),
            "ex:B": UmlClass(curie="ex:B", name="B"),
        }
    )
    g = build_ontology(model, "http://example.com/ont#", "ex=http://example.com/")

    choice_uri = URIRef("http://example.com/Choice")
    member_a = URIRef("http://example.com/A")
    member_b = URIRef("http://example.com/B")

    assert (choice_uri, OWL.disjointWith, member_a) in g
    assert (choice_uri, OWL.disjointWith, member_b) in g
    # Not pairwise disjoint unless explicitly modelled elsewhere
    assert (member_a, OWL.disjointWith, member_b) not in g
