
import importlib


def test_import_package():
    m = importlib.import_module("uml2semantics")
    assert hasattr(m, "__version__")
