import subprocess
from pathlib import Path
from rdflib import Graph, Namespace, RDF, RDFS, OWL, URIRef, Literal

def test_golden_example(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    examples = root / "examples"
    out = tmp_path / "out.ttl"

    cmd = [
        "python", "-m", "uml2semantics",
        "-c", str(examples / "Classes.tsv"),
        "-a", str(examples / "Attributes.tsv"),
        "--datatypes", str(examples / "Datatypes.tsv"),
        "-e", str(examples / "Enumerations.tsv"),
        "-n", str(examples / "EnumerationNamedValues.tsv"),
        "--annotation-properties", str(examples / "AnnotationProperties.tsv"),
        "--annotations", str(examples / "Annotations.tsv"),
        "-o", str(out),
        "--prefixes", "iso:http://iso20022.example/ontology#,rdfs:http://www.w3.org/2000/01/rdf-schema#,skos:http://www.w3.org/2004/02/skos/core#",
        "-i", "http://iso20022.example/ontology",
        "--format", "turtle",
    ]
    subprocess.check_call(cmd)

    g_actual = Graph().parse(out, format="turtle")
    iso = Namespace("http://iso20022.example/ontology#")

    # Ontology exists and graph is non-empty
    assert len(g_actual) > 0
    assert (URIRef("http://iso20022.example/ontology"), RDF.type, OWL.Ontology) in g_actual

    # At least one class and one annotation property are present
    any_class = next(g_actual.subjects(RDF.type, OWL.Class), None)
    assert any_class is not None
    any_ann_prop = next(g_actual.subjects(RDF.type, OWL.AnnotationProperty), None)
    assert any_ann_prop is not None
