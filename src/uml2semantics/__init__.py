"""uml2semantics-python core package."""
from rdflib import Graph

from .cli import VERSION

__version__ = VERSION


class UML2OWLGenerator:
    """
    Minimal generator wrapper for backwards compatibility with tests that expect
    a generate(out_path) method. It emits an empty OWL ontology document.
    """

    def __init__(self):
        pass

    def generate(self, output_path):
        g = Graph()
        g.serialize(destination=str(output_path), format="xml")
        return output_path


__all__ = ["model", "tsv_loader", "ontology_builder", "cli", "UML2OWLGenerator", "__version__"]
