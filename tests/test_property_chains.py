from pathlib import Path

import pytest
from rdflib import RDF, OWL, URIRef, Literal
from rdflib.namespace import DCTERMS

from uml2semantics.tsv_loader import load_model
from uml2semantics.ontology_builder import build_ontology


def test_property_chains_invalid_row():
    root = Path(__file__).resolve().parents[1]
    chains_tsv = root / "testdata" / "property_chains.tsv"
    with pytest.raises(ValueError) as excinfo:
        load_model(property_chains_tsv=chains_tsv)
    msg = str(excinfo.value)
    assert "row 4" in msg
    assert "superproperty_iri" in msg


def test_property_chain_emission_and_disabled_row():
    root = Path(__file__).resolve().parents[1]
    chains_tsv = root / "testdata" / "property_chains_valid.tsv"
    model = load_model(property_chains_tsv=chains_tsv)
    g = build_ontology(model, "http://example.com/ont#", "")

    super_prop = URIRef("http://example.com/rel/trace")
    p1 = URIRef("http://example.com/rel/ME")
    p2 = URIRef("http://example.com/rel/BE")
    p3 = URIRef("http://example.com/rel/BA")

    assert (super_prop, RDF.type, OWL.ObjectProperty) in g
    chain_head = g.value(super_prop, OWL.propertyChainAxiom)
    assert chain_head is not None
    assert list(g.items(chain_head)) == [p1, p2, p3]
    assert (super_prop, DCTERMS.source, Literal("spec-v1")) in g

    disabled_prop = URIRef("http://example.com/rel/disabled")
    assert (disabled_prop, OWL.propertyChainAxiom, None) not in g
