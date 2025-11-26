from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Iterable

from rdflib import Graph, Namespace, Literal, RDF, RDFS, OWL, XSD

from .rdf_utils import (
    DatatypeDef,
    DatatypeFacet,
    ISO20022,
    ISO20022DT,
    ISO20022CD,
    add_namespaces,
    make_datatype_restriction,
    normalise_base_datatype,
    add_label_and_definition,
)


@dataclass
class ClassDef:
    curie: str
    name: str
    definition: Optional[str] = None


@dataclass
class AttributeDef:
    curie: str
    owner_class_curie: str
    name: str
    type_curie: str
    min_multiplicity: str
    max_multiplicity: str
    definition: Optional[str] = None


@dataclass
class EnumLiteralDef:
    curie: str
    name: str
    definition: Optional[str] = None
    enumeration_curie: Optional[str] = None


class UML2OWLGenerator:
    """Generate an OWL 2 ontology from UML-derived TSV exports.

    This is intentionally **minimal** and focussed on getting OWL 2 semantics
    right for datatypes and the separation of classes vs. enumeration
    individuals.
    """

    def __init__(
        self,
        class_tsv: Optional[Path] = None,
        attribute_tsv: Optional[Path] = None,
        datatypes_tsv: Optional[Path] = None,
        enumerations_tsv: Optional[Path] = None,
    ) -> None:
        self.class_tsv = Path(class_tsv) if class_tsv else None
        self.attribute_tsv = Path(attribute_tsv) if attribute_tsv else None
        self.datatypes_tsv = Path(datatypes_tsv) if datatypes_tsv else None
        self.enumerations_tsv = Path(enumerations_tsv) if enumerations_tsv else None

        self.classes: Dict[str, ClassDef] = {}
        self.attributes: Dict[str, AttributeDef] = {}
        self.datatypes: Dict[str, DatatypeDef] = {}
        self.enum_literals: Dict[str, EnumLiteralDef] = {}

    # ------------------------------------------------------------------
    # Loading helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _iter_tsv(path: Path):
        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                yield row

    def load_classes(self) -> None:
        if not self.class_tsv:
            return
        for row in self._iter_tsv(self.class_tsv):
            curie = row.get("Curie") or row.get("Class") or ""
            name = row.get("Name") or ""
            definition = row.get("Definition") or None
            if not curie:
                continue
            self.classes[curie] = ClassDef(curie=curie, name=name, definition=definition)

    def load_attributes(self) -> None:
        if not self.attribute_tsv:
            return
        for row in self._iter_tsv(self.attribute_tsv):
            curie = row.get("Curie") or ""
            owner = row.get("Class") or ""
            name = row.get("Name") or ""
            type_curie = row.get("ClassEnumOrPrimitiveType") or ""
            min_mult = row.get("MinMultiplicity") or "0"
            max_mult = row.get("MaxMultiplicity") or "1"
            definition = row.get("Definition") or None
            if not curie or not owner or not name or not type_curie:
                continue
            self.attributes[curie] = AttributeDef(
                curie=curie,
                owner_class_curie=owner,
                name=name,
                type_curie=type_curie,
                min_multiplicity=min_mult,
                max_multiplicity=max_mult,
                definition=definition,
            )

    def load_datatypes(self) -> None:
        if not self.datatypes_tsv:
            return
        for row in self._iter_tsv(self.datatypes_tsv):
            curie = row.get("Curie") or ""
            name = row.get("Name") or ""
            base = row.get("BaseDatatype") or "xsd:string"
            definition = row.get("Definition") or None
            if not curie:
                continue

            facets: Dict[str, DatatypeFacet] = {}
            for key in (
                "MinLength",
                "MaxLength",
                "Pattern",
                "MinInclusive",
                "MaxInclusive",
                "MinExclusive",
                "MaxExclusive",
                "TotalDigits",
                "FractionDigits",
            ):
                val = row.get(key) or ""
                if val != "":
                    facets[key] = DatatypeFacet(key=key, value=val)

            self.datatypes[curie] = DatatypeDef(
                curie=curie,
                name=name,
                base_datatype=normalise_base_datatype(base),
                definition=definition,
                facets=facets,
            )

    def load_enumerations(self) -> None:
        if not self.enumerations_tsv:
            return
        for row in self._iter_tsv(self.enumerations_tsv):
            curie = row.get("Curie") or ""
            name = row.get("Name") or ""
            definition = row.get("Definition") or None
            enumeration_curie = row.get("Enumeration") or None
            if not curie:
                continue
            self.enum_literals[curie] = EnumLiteralDef(
                curie=curie,
                name=name,
                definition=definition,
                enumeration_curie=enumeration_curie,
            )

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def build_graph(self) -> Graph:
        g = Graph()
        add_namespaces(g)

        # Classes
        for cls in self.classes.values():
            iri = self._curie_to_iri(cls.curie, default_ns=ISO20022)
            g.add((iri, RDF.type, OWL.Class))
            add_label_and_definition(g, iri, cls.name, cls.definition)

        # Datatypes (OWL 2 datatype restrictions where facets exist)
        for dt in self.datatypes.values():
            dt_iri = self._curie_to_iri(dt.curie, default_ns=ISO20022DT)
            base_iri = dt.base_datatype

            if dt.facets:
                restriction_bnode = make_datatype_restriction(
                    g,
                    base_iri=base_iri,
                    facets=dt.facets.values(),
                )
                # We mint a named datatype and assert equivalence to the restriction
                g.add((dt_iri, RDF.type, RDFS.Datatype))
                g.add((dt_iri, OWL.equivalentClass, restriction_bnode))
            else:
                g.add((dt_iri, RDF.type, RDFS.Datatype))
                g.add((dt_iri, OWL.onDatatype, base_iri))

            add_label_and_definition(g, dt_iri, dt.name, dt.definition)

        # Enumerations / code lists as individuals under iso20022cd:
        for lit in self.enum_literals.values():
            # Force the iso20022cd: prefix semantics even if the TSV Curie does not
            # already start with it – this reflects the convention you described.
            iri = self._curie_to_iri(lit.curie, default_ns=ISO20022CD)
            g.add((iri, RDF.type, OWL.NamedIndividual))
            add_label_and_definition(g, iri, lit.name, lit.definition)
            # Optional: link literal to its enumeration "class" if provided
            if lit.enumeration_curie:
                enum_iri = self._curie_to_iri(lit.enumeration_curie, default_ns=ISO20022CD)
                g.add((iri, RDF.type, enum_iri))

        # Attributes as OWL object or datatype properties
        for attr in self.attributes.values():
            owner_iri = self._curie_to_iri(attr.owner_class_curie, default_ns=ISO20022)
            prop_iri = self._curie_to_iri(attr.curie, default_ns=ISO20022)
            range_iri = self._curie_to_iri(attr.type_curie, default_ns=ISO20022DT)

            # Decide object vs datatype property very simply: iso20022dt: means datatype,
            # iso20022: means class. This can be refined later.
            if attr.type_curie.startswith("iso20022dt:"):
                prop_type = OWL.DatatypeProperty
            else:
                prop_type = OWL.ObjectProperty

            g.add((prop_iri, RDF.type, prop_type))
            g.add((prop_iri, RDFS.domain, owner_iri))
            g.add((prop_iri, RDFS.range, range_iri))
            add_label_and_definition(g, prop_iri, attr.name, attr.definition)

            # Multiplicity can be turned into cardinality restrictions later if desired.

        return g

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_all(self) -> None:
        self.load_classes()
        self.load_attributes()
        self.load_datatypes()
        self.load_enumerations()

    def generate(self, output_path: Path, fmt: str = "xml") -> None:
        self.load_all()
        g = self.build_graph()
        g.serialize(destination=str(output_path), format=fmt)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _curie_to_iri(curie: str, default_ns: Namespace):
        # Very small helper: if it looks like a CURIE with known prefix, pass
        # it through, otherwise put it under the given default namespace.
        if ":" in curie:
            prefix, local = curie.split(":", 1)
            if prefix == "iso20022":
                return ISO20022[local]
            if prefix == "iso20022dt":
                return ISO20022DT[local]
            if prefix == "iso20022cd":
                return ISO20022CD[local]
        return default_ns[curie]
