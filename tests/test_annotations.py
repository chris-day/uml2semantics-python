from rdflib import RDF, RDFS, OWL, URIRef, Literal
from rdflib.namespace import XSD

from uml2semantics.model import (
    Model,
    UmlClass,
    AnnotationProperty,
    AnnotationAssertion,
)
from uml2semantics.ontology_builder import build_ontology


def test_annotation_properties_and_assertions():
    model = Model(
        classes={
            "ex:Foo": UmlClass(curie="ex:Foo", name="Foo"),
        },
        annotation_properties={
            "dct:creator": AnnotationProperty(curie="dct:creator", name="Creator"),
            "ex:status": AnnotationProperty(curie="ex:status", name="Status"),
        },
        annotations=[
            AnnotationAssertion(
                target_curie="ex:Foo",
                property_curie="dct:creator",
                value="Chris",
                language=None,
                datatype=None,
            ),
            AnnotationAssertion(
                target_curie="ex:Foo",
                property_curie="ex:status",
                value="approved",
                datatype=None,
                language=None,
            ),
            AnnotationAssertion(
                target_curie="ex:Foo",
                property_curie="rdfs:comment",
                value="A test class",
                language="en",
                datatype=None,
            ),
            AnnotationAssertion(
                target_curie="ex:Foo",
                property_curie="ex:modified",
                value="2024-10-02",
                datatype="xsd:date",
                language=None,
            ),
        ],
    )

    g = build_ontology(
        model,
        "http://example.com/ont#",
        "ex=http://example.com/;dct=http://purl.org/dc/terms/;rdfs=http://www.w3.org/2000/01/rdf-schema#",
    )

    creator = URIRef("http://purl.org/dc/terms/creator")
    status = URIRef("http://example.com/status")
    foo = URIRef("http://example.com/Foo")

    # Annotation properties emitted
    assert (creator, RDF.type, OWL.AnnotationProperty) in g
    assert (creator, RDFS.label, Literal("Creator")) in g

    # Assertions emitted
    assert (foo, creator, Literal("Chris")) in g
    assert (foo, status, Literal("approved")) in g
    assert (foo, RDFS.comment, Literal("A test class", lang="en")) in g
    assert (foo, URIRef("http://example.com/modified"), Literal("2024-10-02", datatype=XSD.date)) in g
