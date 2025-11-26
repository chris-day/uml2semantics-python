from pathlib import Path

from uml2semantics import UML2OWLGenerator, __version__


def test_import_and_basic_instantiation(tmp_path: Path):
    gen = UML2OWLGenerator()
    out = tmp_path / "out.owl"
    gen.generate(out)
    assert out.exists()
    assert isinstance(__version__, str)
