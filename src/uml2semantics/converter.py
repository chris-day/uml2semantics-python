from __future__ import annotations

from pathlib import Path
from typing import Iterable

from rdflib import BNode, Graph, Literal, Namespace, RDF, RDFS, OWL, XSD

from .model import UmlModel, UmlClass, UmlProperty
from .options import ConversionOptions
from .parser import UmlParser


class Uml2OwlConverter:
    """Convert UML models to OWL 2.

    This class centralises the OWL 2‑aware mapping logic. The intention is that
    it can be extended to accommodate the full semantics of the original
    uml2semantics tool, while keeping a clean and testable design.
    """

    def __init__(self, options: ConversionOptions) -> None:
        self.options = options
        self.g = Graph()

        self.EX = Namespace(self.options.base_iri)
        self.g.bind("ex", self.EX)
        self.g.bind("owl", OWL)
        self.g.bind("rdfs", RDFS)
        self.g.bind("xsd", XSD)

    # ------------------------------------------------------------------ public

    def run(self) -> Graph:
        model = self._load_model(self.options.input_path)
        self._initialise_ontology()
        self._map_classes(model)
        return self.g

    def write(self, graph: Graph, path: Path, fmt: str) -> None:
        graph.serialize(destination=str(path), format=fmt)

    # ----------------------------------------------------------------- helpers

    def _load_model(self, path: Path) -> UmlModel:
        parser = UmlParser()
        return parser.parse(path)

    def _initialise_ontology(self) -> None:
        # OWL 2 ontology header
        ontology_iri = self.options.base_iri.rstrip("#")
        self.g.add((self.EX[""], RDF.type, OWL.Ontology))
        for imp in self.options.imports:
            self.g.add((self.EX[""], OWL.imports, Literal(imp)))

    def _map_classes(self, model: UmlModel) -> None:
        for uml_class in model.classes.values():
            if uml_class.is_enumeration:
                self._map_enumeration(uml_class)
            else:
                self._map_class(uml_class)

    def _map_class(self, uml_class: UmlClass) -> None:
        cls = self.EX[uml_class.name]
        self.g.add((cls, RDF.type, OWL.Class))

        for super_name in uml_class.super_types:
            super_cls = self.EX[super_name]
            self.g.add((cls, RDFS.subClassOf, super_cls))

        for prop in uml_class.properties:
            if prop.is_association:
                self._map_object_property(uml_class, prop)
            else:
                self._map_data_property(uml_class, prop)

    # ---------------------------- OWL 2 patterns for properties & restrictions

    def _map_object_property(self, uml_class: UmlClass, prop: UmlProperty) -> None:
        p = self.EX[prop.name]
        domain = self.EX[uml_class.name]
        range_cls = self.EX[prop.type_name]

        self.g.add((p, RDF.type, OWL.ObjectProperty))
        self.g.add((p, RDFS.domain, domain))
        self.g.add((p, RDFS.range, range_cls))

        for restriction in self._multiplicity_restrictions(domain, p, prop):
            self.g.add((domain, RDFS.subClassOf, restriction))

    def _map_data_property(self, uml_class: UmlClass, prop: UmlProperty) -> None:
        p = self.EX[prop.name]
        domain = self.EX[uml_class.name]

        # Datatype is simplified to xsd:string here; in a full implementation
        # this would inspect the UML type and map it to an appropriate XSD
        # datatype plus any necessary OWL 2 facets.
        datatype = XSD.string

        self.g.add((p, RDF.type, OWL.DatatypeProperty))
        self.g.add((p, RDFS.domain, domain))
        self.g.add((p, RDFS.range, datatype))

        for restriction in self._multiplicity_restrictions(domain, p, prop):
            self.g.add((domain, RDFS.subClassOf, restriction))

    def _multiplicity_restrictions(self, domain, prop, uml_prop: UmlProperty) -> Iterable[BNode]:
        """Encode UML multiplicity as OWL 2 cardinality restrictions.

        We use the standard OWL 2 object/datatype cardinality constructs.
        """
        restrictions: list[BNode] = []

        if uml_prop.lower is not None and uml_prop.lower > 0:
            r = BNode()
            self.g.add((r, RDF.type, OWL.Restriction))
            self.g.add((r, OWL.onProperty, prop))
            self.g.add((r, OWL.minCardinality, Literal(uml_prop.lower, datatype=XSD.nonNegativeInteger)))
            restrictions.append(r)

        if uml_prop.upper is not None:
            r = BNode()
            self.g.add((r, RDF.type, OWL.Restriction))
            self.g.add((r, OWL.onProperty, prop))
            self.g.add((r, OWL.maxCardinality, Literal(uml_prop.upper, datatype=XSD.nonNegativeInteger)))
            restrictions.append(r)

        return restrictions

    # ------------------------------------------------------------- enumerations

    def _map_enumeration(self, uml_class: UmlClass) -> None:
        """Map a UML enumeration to OWL 2 using `owl:oneOf`.

        Each literal becomes an individual; the enumeration itself is exposed
        as a class whose extension is exactly the listed individuals.
        """
        enum_cls = self.EX[uml_class.name]
        self.g.add((enum_cls, RDF.type, OWL.Class))

        members: list = []
        for lit in uml_class.enumeration_literals:
            ind = self.EX[lit]
            self.g.add((ind, RDF.type, enum_cls))
            members.append(ind)

        if not members:
            return

        # Build an owl:oneOf list: _:x rdf:type owl:Class; owl:oneOf (a b c)
        one_of_node = BNode()
        self.g.add((enum_cls, OWL.equivalentClass, one_of_node))
        self.g.add((one_of_node, RDF.type, OWL.Class))

        # Build RDF list structure for the enumeration extension
        list_head = self._rdf_list(members)
        self.g.add((one_of_node, OWL.oneOf, list_head))

    # --------------------------------------------------------------- utilities

    def _rdf_list(self, members):
        """Create an RDF list in the graph and return the head node."""
        if not members:
            return RDF.nil

        head = BNode()
        current = head
        for i, m in enumerate(members):
            self.g.add((current, RDF.first, m))
            if i == len(members) - 1:
                self.g.add((current, RDF.rest, RDF.nil))
            else:
                nxt = BNode()
                self.g.add((current, RDF.rest, nxt))
                current = nxt
        return head
