import subprocess
from pathlib import Path

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
        "-p", "iso:http://iso20022.example/ontology#,rdfs:http://www.w3.org/2000/01/rdf-schema#,skos:http://www.w3.org/2004/02/skos/core#",
        "-i", "http://iso20022.example/ontology",
    ]
    subprocess.check_call(cmd)

    golden = examples / "golden-out.ttl"
    assert golden.read_text(encoding="utf-8").strip() == out.read_text(encoding="utf-8").strip()
