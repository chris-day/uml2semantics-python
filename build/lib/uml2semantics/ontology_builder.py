from typing import Dict, List, Tuple
from rdflib import Graph, Namespace, URIRef, BNode, Literal
from rdflib.namespace import RDF, RDFS, OWL, XSD
from .model import Model, UmlDatatype, UmlAttribute


def parse_prefixes(prefix_str: str) -> Dict[str, str]:
    prefix_map: Dict[str, str] = {}
    if not prefix_str:
        return prefix_map
    parts = [p.strip() for p in prefix_str.split(";") if p.strip()]
    for part in parts:
        if "=" not in part:
            continue
        pfx, iri = part.split("=", 1)
        prefix_map[pfx.strip()] = iri.strip()
    return prefix_map


def _expand(curie_or_iri: str, prefix_map: Dict[str, str]) -> URIRef:
    if ":" in curie_or_iri:
        pfx, local = curie_or_iri.split(":", 1)
        if pfx in prefix_map:
            return URIRef(prefix_map[pfx] + local)
    return URIRef(curie_or_iri)


def _make_rdf_list(g: Graph, elements: List[URIRef]) -> BNode:
    if not elements:
        return RDF.nil  # type: ignore
    head = BNode()
    current = head
    for i, el in enumerate(elements):
        g.add((current, RDF.first, el))
        if i == len(elements) - 1:
            g.add((current, RDF.rest, RDF.nil))
        else:
            nxt = BNode()
            g.add((current, RDF.rest, nxt))
            current = nxt
    return head


def _facet_nodes_for_datatype(
    g: Graph,
    base_uri: URIRef,
    pattern: str = None,
    min_length: int = None,
    max_length: int = None,
    min_inclusive: str = None,
    max_inclusive: str = None,
    min_exclusive: str = None,
    max_exclusive: str = None,
    total_digits: int = None,
    fraction_digits: int = None,
) -> List[BNode]:
    nodes: List[BNode] = []
    if pattern:
        n = BNode()
        g.add((n, XSD.pattern, Literal(pattern)))
        nodes.append(n)
    if min_length is not None:
        n = BNode()
        g.add((n, XSD.minLength, Literal(min_length, datatype=XSD.integer)))
        nodes.append(n)
    if max_length is not None:
        n = BNode()
        g.add((n, XSD.maxLength, Literal(max_length, datatype=XSD.integer)))
        nodes.append(n)
    if min_inclusive is not None:
        n = BNode()
        g.add((n, XSD.minInclusive, Literal(min_inclusive, datatype=base_uri)))
        nodes.append(n)
    if max_inclusive is not None:
        n = BNode()
        g.add((n, XSD.maxInclusive, Literal(max_inclusive, datatype=base_uri)))
        nodes.append(n)
    if min_exclusive is not None:
        n = BNode()
        g.add((n, XSD.minExclusive, Literal(min_exclusive, datatype=base_uri)))
        nodes.append(n)
    if max_exclusive is not None:
        n = BNode()
        g.add((n, XSD.maxExclusive, Literal(max_exclusive, datatype=base_uri)))
        nodes.append(n)
    if total_digits is not None:
        n = BNode()
        g.add((n, XSD.totalDigits, Literal(total_digits, datatype=XSD.integer)))
        nodes.append(n)
    if fraction_digits is not None:
        n = BNode()
        g.add((n, XSD.fractionDigits, Literal(fraction_digits, datatype=XSD.integer)))
        nodes.append(n)
    return nodes


def _base_datatype_iri(base: str, prefix_map: Dict[str, str]) -> URIRef:
    if ":" in base:
        pfx, local = base.split(":", 1)
        if pfx == "xsd":
            return getattr(XSD, local)
        if pfx in prefix_map:
            return URIRef(prefix_map[pfx] + local)
    return URIRef(base)


def _emit_named_datatype(g: Graph, dt: UmlDatatype, prefix_map: Dict[str, str]) -> None:
    dt_ident = dt.curie or dt.name
    if not dt_ident:
        return
    dt_uri = _expand(dt_ident, prefix_map)
    g.add((dt_uri, RDF.type, RDFS.Datatype))
    if dt.name:
        g.add((dt_uri, RDFS.label, Literal(dt.name)))
    if dt.definition:
        g.add((dt_uri, RDFS.comment, Literal(dt.definition)))
    has_facets = any([
        dt.pattern,
        dt.min_length is not None,
        dt.max_length is not None,
        dt.min_inclusive is not None,
        dt.max_inclusive is not None,
        dt.min_exclusive is not None,
        dt.max_exclusive is not None,
        dt.total_digits is not None,
        dt.fraction_digits is not None,
    ])
    if not has_facets:
        return
    restr_dt = BNode()
    g.add((restr_dt, RDF.type, RDFS.Datatype))
    base_uri = _base_datatype_iri(dt.base_datatype, prefix_map)
    g.add((restr_dt, OWL.onDatatype, base_uri))
    facet_nodes = _facet_nodes_for_datatype(
        g,
        base_uri=base_uri,
        pattern=dt.pattern,
        min_length=dt.min_length,
        max_length=dt.max_length,
        min_inclusive=dt.min_inclusive,
        max_inclusive=dt.max_inclusive,
        min_exclusive=dt.min_exclusive,
        max_exclusive=dt.max_exclusive,
        total_digits=dt.total_digits,
        fraction_digits=dt.fraction_digits,
    )
    if facet_nodes:
        lst = _make_rdf_list(g, facet_nodes)
        g.add((restr_dt, OWL.withRestrictions, lst))
    g.add((dt_uri, OWL.equivalentClass, restr_dt))


def _emit_inline_datatype_range(g: Graph, attr: UmlAttribute, prefix_map: Dict[str, str]) -> URIRef:
    t = attr.type_curie_or_primitive
    if t in prefix_map or ":" in t:
        base_uri = _base_datatype_iri(t, prefix_map)
    else:
        base_uri = XSD.string
    restr_dt = BNode()
    g.add((restr_dt, RDF.type, RDFS.Datatype))
    g.add((restr_dt, OWL.onDatatype, base_uri))
    facet_nodes = _facet_nodes_for_datatype(
        g,
        base_uri=base_uri,
        pattern=attr.pattern,
        min_length=attr.min_length,
        max_length=attr.max_length,
        min_inclusive=attr.min_inclusive,
        max_inclusive=attr.max_inclusive,
        min_exclusive=attr.min_exclusive,
        max_exclusive=attr.max_exclusive,
        total_digits=attr.total_digits,
        fraction_digits=attr.fraction_digits,
    )
    if facet_nodes:
        lst = _make_rdf_list(g, facet_nodes)
        g.add((restr_dt, OWL.withRestrictions, lst))
    return restr_dt


def build_ontology(model: Model, ontology_iri: str, prefix_str: str) -> Graph:
    g = Graph()
    prefix_map = parse_prefixes(prefix_str)
    for pfx, iri in prefix_map.items():
        g.bind(pfx, Namespace(iri))
    ont_uri = URIRef(ontology_iri)
    g.add((ont_uri, RDF.type, OWL.Ontology))

    # Classes
    for cls in model.classes.values():
        ident = cls.curie or cls.name
        if not ident:
            continue
        uri = _expand(ident, prefix_map)
        g.add((uri, RDF.type, OWL.Class))
        if cls.name:
            g.add((uri, RDFS.label, Literal(cls.name)))
        if cls.definition:
            g.add((uri, RDFS.comment, Literal(cls.definition)))
        for parent in cls.parent_curie_list:
            g.add((uri, RDFS.subClassOf, _expand(parent, prefix_map)))
        if cls.choice_of:
            members = [_expand(c, prefix_map) for c in cls.choice_of]
            union_class = BNode()
            g.add((union_class, RDF.type, OWL.Class))
            lst = _make_rdf_list(g, members)
            g.add((union_class, OWL.unionOf, lst))
            g.add((uri, RDFS.subClassOf, union_class))
            if cls.choice_semantics and cls.choice_semantics.lower().startswith("exclusive"):
                for m in members:
                    g.add((uri, OWL.disjointWith, m))

    # Enumerations
    for en in model.enumerations.values():
        ident = en.curie or en.name
        if not ident:
            continue
        uri = _expand(ident, prefix_map)
        g.add((uri, RDF.type, OWL.Class))
        if en.name:
            g.add((uri, RDFS.label, Literal(en.name)))
        if en.definition:
            g.add((uri, RDFS.comment, Literal(en.definition)))

    # Enumeration literals
    for lit in model.enum_literals:
        enum_uri = _expand(lit.enumeration, prefix_map)
        inst_ident = lit.curie or lit.name
        if not inst_ident:
            continue
        inst_uri = _expand(inst_ident, prefix_map)
        g.add((inst_uri, RDF.type, enum_uri))
        if lit.name:
            g.add((inst_uri, RDFS.label, Literal(lit.name)))
        if lit.definition:
            g.add((inst_uri, RDFS.comment, Literal(lit.definition)))

    # Datatypes
    for dt in model.datatypes.values():
        _emit_named_datatype(g, dt, prefix_map)

    # Attributes → properties
    from .model import UmlAttribute  # avoid circular

    restrictions_by_domain: Dict[URIRef, List[URIRef]] = {}

    for attr in model.attributes:
        domain_uri = _expand(attr.class_curie, prefix_map)
        prop_ident = attr.curie or attr.name
        if not prop_ident:
            continue
        prop_uri = _expand(prop_ident, prefix_map)
        target = attr.type_curie_or_primitive
        is_object = target in model.classes or target in model.enumerations
        if is_object:
            g.add((prop_uri, RDF.type, OWL.ObjectProperty))
            g.add((prop_uri, RDFS.domain, domain_uri))
            g.add((prop_uri, RDFS.range, _expand(target, prefix_map)))
        else:
            g.add((prop_uri, RDF.type, OWL.DatatypeProperty))
            g.add((prop_uri, RDFS.domain, domain_uri))
            has_inline = any([
                attr.pattern,
                attr.min_length is not None,
                attr.max_length is not None,
                attr.min_inclusive is not None,
                attr.max_inclusive is not None,
                attr.min_exclusive is not None,
                attr.max_exclusive is not None,
                attr.total_digits is not None,
                attr.fraction_digits is not None,
            ])
            if has_inline:
                range_dt = _emit_inline_datatype_range(g, attr, prefix_map)
                g.add((prop_uri, RDFS.range, range_dt))
            else:
                if target in model.datatypes:
                    g.add((prop_uri, RDFS.range, _expand(target, prefix_map)))
                else:
                    g.add((prop_uri, RDFS.range, _base_datatype_iri(target, prefix_map)))

        # rdfs:label from TSV Name (always populated; loader enforces)
        if attr.name:
            g.add((prop_uri, RDFS.label, Literal(attr.name)))

        if attr.definition:
            g.add((prop_uri, RDFS.comment, Literal(attr.definition)))

        if attr.min_cardinality is not None or attr.max_cardinality is not None:
            restr = BNode()
            g.add((restr, RDF.type, OWL.Restriction))
            g.add((restr, OWL.onProperty, prop_uri))
            if (
                attr.min_cardinality is not None
                and attr.max_cardinality is not None
                and attr.max_cardinality != "*"
                and attr.min_cardinality == attr.max_cardinality
            ):
                g.add((restr, OWL.cardinality, Literal(attr.min_cardinality, datatype=XSD.nonNegativeInteger)))
            else:
                if attr.min_cardinality is not None:
                    g.add((restr, OWL.minCardinality, Literal(attr.min_cardinality, datatype=XSD.nonNegativeInteger)))
                if attr.max_cardinality not in (None, "*"):
                    g.add((restr, OWL.maxCardinality, Literal(attr.max_cardinality, datatype=XSD.nonNegativeInteger)))
            restrictions_by_domain.setdefault(domain_uri, []).append(restr)

    for domain_uri, restrs in restrictions_by_domain.items():
        for r in restrs:
            g.add((domain_uri, RDFS.subClassOf, r))

    return g


def serialise_ontology(model: Model, ontology_iri: str, prefix_str: str, output_path, format: str = "xml", xml_base: str = None) -> None:
    g = build_ontology(model, ontology_iri, prefix_str)
    if xml_base and format == "xml":
        g.serialize(destination=str(output_path), format=format, xml_base=xml_base)
    else:
        g.serialize(destination=str(output_path), format=format)
