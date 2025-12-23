from pathlib import Path

from rdflib import Graph, RDF, OWL, URIRef

from uml2semantics.tsv_loader import load_model
from uml2semantics.ontology_builder import build_ontology


def test_property_chain_turtle_output(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    chains_tsv = root / "testdata" / "property_chains_valid.tsv"
    model = load_model(property_chains_tsv=chains_tsv)
    g = build_ontology(model, "http://example.com/ont#", "")

    out = tmp_path / "chains.ttl"
    g.serialize(destination=str(out), format="turtle")

    g_parsed = Graph().parse(out, format="turtle")
    super_prop = URIRef("http://example.com/rel/trace")
    p1 = URIRef("http://example.com/rel/ME")
    p2 = URIRef("http://example.com/rel/BE")
    p3 = URIRef("http://example.com/rel/BA")

    assert (super_prop, RDF.type, OWL.ObjectProperty) in g_parsed
    chain_head = g_parsed.value(super_prop, OWL.propertyChainAxiom)
    assert chain_head is not None
    assert list(g_parsed.items(chain_head)) == [p1, p2, p3]
