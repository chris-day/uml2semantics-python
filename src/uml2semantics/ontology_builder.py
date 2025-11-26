
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from rdflib import BNode, Graph, Literal, Namespace, RDF, RDFS, OWL, URIRef
from rdflib.namespace import XSD

from .model import Model, UmlDatatype


def parse_prefixes(prefix_str: str) -> Dict[str, str]:
    """
    Parse a prefix string of the form:

        'iso20022:http://iso20022.org/iso20022/,xsd:http://www.w3.org/2001/XMLSchema#'

    into a mapping {"iso20022": "http://iso20022.org/iso20022/", ...}.
    """
    result: Dict[str, str] = {}
    if not prefix_str:
        return result
    for part in prefix_str.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            continue
        pref, iri = part.split(":", 1)
        pref = pref.strip()
        iri = iri.strip()
        if pref and iri:
            result[pref] = iri
    return result


def curie_to_iri(curie: str, prefixes: Dict[str, str]) -> Optional[URIRef]:
    if ":" not in curie:
        return None
    pref, local = curie.split(":", 1)
    base = prefixes.get(pref)
    if not base:
        return None
    return URIRef(base + local)


def _datatype_from_name(type_name: str, model: Model, prefixes: Dict[str, str]) -> Optional[URIRef]:
    # 1) Explicit datatypes.tsv mapping
    dt: Optional[UmlDatatype] = model.datatypes.get(type_name)
    if dt is not None:
        return URIRef(dt.iri)

    # 2) CURIE directly resolvable via prefixes
    iri = curie_to_iri(type_name, prefixes)
    if iri is not None:
        return iri

    # 3) Fallback: try xsd:*
    if not type_name.startswith("xsd:"):
        return None
    local = type_name.split(":", 1)[1]
    if hasattr(XSD, local):
        return getattr(XSD, local)
    return None


def build_ontology(
    model: Model,
    ontology_iri: str,
    prefix_str: str,
) -> Graph:
    g = Graph()

    prefixes = parse_prefixes(prefix_str)
    for pfx, iri in prefixes.items():
        g.bind(pfx, Namespace(iri))
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("owl", OWL)
    g.bind("xsd", XSD)

    ont_iri_ref = URIRef(ontology_iri)
    g.add((ont_iri_ref, RDF.type, OWL.Ontology))

    # Helper for class IRI lookup by name
    class_iris: Dict[str, URIRef] = {name: URIRef(uc.iri) for name, uc in model.classes.items()}
    enum_iris: Dict[str, URIRef] = {name: URIRef(e.iri) for name, e in model.enumerations.items()}

    # --- Classes ---
    for c in model.classes.values():
        c_iri = URIRef(c.iri)
        g.add((c_iri, RDF.type, OWL.Class))
        g.add((c_iri, RDFS.label, Literal(c.name)))
        if c.definition:
            g.add((c_iri, RDFS.comment, Literal(c.definition)))
        if c.is_abstract:
            # Use an OWL 2 annotation for abstractness.
            g.add((c_iri, OWL.deprecated, Literal(True)))
        for sc_name in c.super_classes:
            sc_iri = class_iris.get(sc_name)
            if sc_iri:
                g.add((c_iri, RDFS.subClassOf, sc_iri))

    # --- Enumerations as classes ---
    for e in model.enumerations.values():
        e_iri = URIRef(e.iri)
        g.add((e_iri, RDF.type, OWL.Class))
        g.add((e_iri, RDFS.label, Literal(e.name)))
        if e.definition:
            g.add((e_iri, RDFS.comment, Literal(e.definition)))

    # --- Enum literals as individuals ---
    for lit in model.enum_literals:
        enum_iri = enum_iris.get(lit.enumeration)
        if not enum_iri:
            continue
        lit_iri = URIRef(lit.iri)
        g.add((lit_iri, RDF.type, enum_iri))
        g.add((lit_iri, RDFS.label, Literal(lit.name)))
        if lit.definition:
            g.add((lit_iri, RDFS.comment, Literal(lit.definition)))

    # --- Attributes → OWL 2 object / datatype properties + restrictions ---
    for attr in model.attributes:
        owner_iri = class_iris.get(attr.owner) or enum_iris.get(attr.owner)
        if owner_iri is None:
            continue

        # Decide property kind: object vs datatype
        range_class_iri = class_iris.get(attr.type_name) or enum_iris.get(attr.type_name)
        range_dt_iri = _datatype_from_name(attr.type_name, model, prefixes)

        if range_class_iri is not None:
            prop_type = OWL.ObjectProperty
            range_iri = range_class_iri
        else:
            prop_type = OWL.DatatypeProperty
            range_iri = range_dt_iri or XSD.string  # robust fallback

        # Property IRI: reuse CURIE if possible, otherwise mint from owner + name.
        prop_iri = curie_to_iri(attr.name, prefixes)
        if prop_iri is None:
            # Mint a local IRI under the ontology IRI
            prop_iri = URIRef(f"{ontology_iri}#{attr.owner}.{attr.name}")

        g.add((prop_iri, RDF.type, prop_type))
        g.add((prop_iri, RDFS.label, Literal(attr.name)))
        if attr.definition:
            g.add((prop_iri, RDFS.comment, Literal(attr.definition)))

        # Domain & range
        g.add((prop_iri, RDFS.domain, owner_iri))
        if range_iri is not None:
            g.add((prop_iri, RDFS.range, range_iri))

        # OWL 2 cardinality restrictions: subclass axioms on the owner
        min_card = attr.min_cardinality
        max_card = attr.max_cardinality

        def restriction_node(cardinality_kind: str, value: int):
            r = BNode()
            g.add((r, RDF.type, OWL.Restriction))
            g.add((r, OWL.onProperty, prop_iri))
            lit = Literal(value, datatype=XSD.nonNegativeInteger)
            if prop_type is OWL.ObjectProperty:
                if cardinality_kind == "exact":
                    g.add((r, OWL.qualifiedCardinality, lit))
                elif cardinality_kind == "min":
                    g.add((r, OWL.minQualifiedCardinality, lit))
                elif cardinality_kind == "max":
                    g.add((r, OWL.maxQualifiedCardinality, lit))
                g.add((r, OWL.onClass, range_iri or OWL.Thing))
            else:
                if cardinality_kind == "exact":
                    g.add((r, OWL.qualifiedCardinality, lit))
                elif cardinality_kind == "min":
                    g.add((r, OWL.minQualifiedCardinality, lit))
                elif cardinality_kind == "max":
                    g.add((r, OWL.maxQualifiedCardinality, lit))
                g.add((r, OWL.onDataRange, range_iri or RDFS.Literal))
            return r

        if min_card is not None and max_card is not None and min_card == max_card:
            r = restriction_node("exact", min_card)
            g.add((owner_iri, RDFS.subClassOf, r))
        else:
            if min_card is not None:
                r = restriction_node("min", min_card)
                g.add((owner_iri, RDFS.subClassOf, r))
            if max_card is not None:
                r = restriction_node("max", max_card)
                g.add((owner_iri, RDFS.subClassOf, r))

    # --- Datatype declarations and optional OWL 2 datatype restrictions ---
    for dt in model.datatypes.values():
        dt_iri = URIRef(dt.iri)
        g.add((dt_iri, RDF.type, RDFS.Datatype))
        if dt.base_iri:
            # Base datatype with optional facets using OWL 2 syntax
            base = URIRef(dt.base_iri)
            base_restr = BNode()
            g.add((dt_iri, OWL.equivalentClass, base_restr))
            g.add((base_restr, RDF.type, RDFS.Datatype))
            g.add((base_restr, OWL.onDatatype, base))

            from rdflib.collection import Collection

            facet_list = BNode()
            g.add((base_restr, OWL.withRestrictions, facet_list))

            members = []
            if dt.min_inclusive is not None:
                f = BNode()
                g.add((f, XSD.minInclusive, Literal(dt.min_inclusive)))
                members.append(f)
            if dt.max_inclusive is not None:
                f = BNode()
                g.add((f, XSD.maxInclusive, Literal(dt.max_inclusive)))
                members.append(f)
            if dt.min_length is not None:
                f = BNode()
                g.add((f, XSD.minLength, Literal(dt.min_length, datatype=XSD.nonNegativeInteger)))
                members.append(f)
            if dt.max_length is not None:
                f = BNode()
                g.add((f, XSD.maxLength, Literal(dt.max_length, datatype=XSD.nonNegativeInteger)))
                members.append(f)

            Collection(g, facet_list, members)

    return g


def serialise_ontology(
    model: Model,
    ontology_iri: str,
    prefix_str: str,
    output: Path,
    format: str = "xml",
) -> None:
    g = build_ontology(model=model, ontology_iri=ontology_iri, prefix_str=prefix_str)
    output.parent.mkdir(parents=True, exist_ok=True)
    g.serialize(destination=str(output), format=format)
