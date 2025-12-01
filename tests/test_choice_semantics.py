from rdflib import RDF, RDFS, OWL, URIRef
from rdflib import Literal
from rdflib.namespace import XSD

from uml2semantics.model import Model, UmlClass, UmlAttribute
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
    member_b = URIRef("B")

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

    # AllDisjointClasses node containing choice + members
    disj_nodes = list(g.subjects(RDF.type, OWL.AllDisjointClasses))
    assert disj_nodes, "Expected AllDisjointClasses for exclusive choice"
    found = False
    for dn in disj_nodes:
        members = list(g.items(g.value(dn, OWL.members)))
        if choice_uri in members and member_a in members and member_b in members:
            found = True
            break
    assert found, "AllDisjointClasses does not contain choice and all members"


def test_choice_class_does_not_get_attribute_restrictions():
    model = Model(
        classes={
            "ex:Choice": UmlClass(curie="ex:Choice", name="Choice", choice_of=["ex:A"]),
            "ex:A": UmlClass(curie="ex:A", name="A"),
        },
        attributes=[
            # Attribute on the choice class itself; should not become subclass restriction
            UmlAttribute(
                class_curie="ex:Choice",
                curie="ex:prop",
                name="prop",
                type_curie_or_primitive="ex:A",
                min_cardinality=1,
                max_cardinality=1,
            )
        ],
    )

    g = build_ontology(model, "http://example.com/ont#", "ex=http://example.com/")

    choice_uri = URIRef("http://example.com/Choice")
    prop_uri = URIRef("http://example.com/prop")

    # Property exists
    assert (prop_uri, RDF.type, OWL.ObjectProperty) in g
    # Subclass restriction is attached directly for non-choice members
    has_direct = any(
        (subclass_obj, OWL.onProperty, prop_uri) in g
        for _, _, subclass_obj in g.triples((choice_uri, RDFS.subClassOf, None))
    )
    assert has_direct, "Attribute restriction should be present on choice class"


def test_choice_attribute_token_in_choiceof_resolves():
    model = Model(
        classes={
            "ex:Choice": UmlClass(curie="ex:Choice", name="Choice", choice_of=["prop"]),
        },
        attributes=[
            UmlAttribute(
                class_curie="ex:Choice",
                curie=None,
                name="prop",
                type_curie_or_primitive="xsd:string",
                min_cardinality=1,
                max_cardinality=1,
            )
        ],
    )
    g = build_ontology(model, "http://example.com/ont#", "ex=http://example.com/")
    choice_uri = URIRef("http://example.com/Choice")
    prop_uri = URIRef("prop")

    # Choice union should include the attribute restriction
    union = next(
        (candidate for _, _, candidate in g.triples((choice_uri, RDFS.subClassOf, None)) if (candidate, OWL.unionOf, None) in g),
        None,
    )
    assert union is not None
    members = list(g.items(g.value(union, OWL.unionOf)))
    has_prop_restr = any((member, OWL.onProperty, prop_uri) in g for member in members)
    assert has_prop_restr

    # And the restriction should have the promoted cardinality
    for member in members:
        if (member, OWL.onProperty, prop_uri) in g:
            assert (member, OWL.cardinality, Literal(1, datatype=XSD.nonNegativeInteger)) in g
