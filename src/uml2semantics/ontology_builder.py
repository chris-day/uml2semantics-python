from typing import Dict, List, Tuple, Union, Optional
import logging
from urllib.parse import urlparse
from rdflib import Graph, Namespace, URIRef, BNode, Literal
from rdflib.namespace import RDF, RDFS, OWL, XSD, XMLNS, DCTERMS, DCAT
from .model import Model, UmlDatatype, UmlAttribute, UmlClass, AnnotationAssertion, AnnotationProperty, PropertyChain

log = logging.getLogger(__name__)


def _preferred_ident(curie: str, name: str, kind: str) -> Union[str, None]:
    """
    Return a CURIE/identifier preferring the provided CURIE. If no CURIE is
    available, fall back to name and warn so consumers know a lossy identifier
    was used.
    """
    if curie:
        return curie
    if name:
        log.warning("%s '%s' is missing a CURIE; falling back to Name for identifier", kind, name)
        return name
    log.warning("%s is missing both CURIE and Name; skipping", kind)
    return None


def parse_prefixes(prefix_str: str) -> Dict[str, str]:
    prefix_map: Dict[str, str] = {
        "rdf": str(RDF),
        "rdfs": str(RDFS),
        "owl": str(OWL),
        "xsd": str(XSD),
        "xml": str(XMLNS),
        "dct": str(DCTERMS),
        "dcat": str(DCAT),
    }
    if not prefix_str:
        return prefix_map
    # Allow either ';' or ',' as separators
    cleaned = prefix_str.replace(",", ";")
    parts = [p.strip() for p in cleaned.split(";") if p.strip()]
    for part in parts:
        pfx = None
        iri = None
        if "=" in part:
            pfx, iri = part.split("=", 1)
        elif ":" in part:
            pfx, iri = part.split(":", 1)
        if pfx and iri:
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


def _is_iri(value: str) -> bool:
    if not value or " " in value:
        return False
    parsed = urlparse(value)
    return bool(parsed.scheme)


def _emit_named_datatype(g: Graph, dt: UmlDatatype, prefix_map: Dict[str, str]) -> None:
    dt_ident = _preferred_ident(dt.curie, dt.name, "Datatype")
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

    base_uri = _base_datatype_iri(dt.base_datatype, prefix_map) if dt.base_datatype else None

    if not has_facets:
        if base_uri is not None:
            g.add((dt_uri, OWL.equivalentClass, base_uri))
        return

    if base_uri is None:
        raise ValueError(
            f"Datatype '{dt.name or dt.curie}' has facet constraints but no BaseDatatype; "
            "populate BaseDatatype in Datatypes.tsv to avoid defaulting to xsd:string."
        )

    restr_dt = BNode()
    g.add((restr_dt, RDF.type, RDFS.Datatype))
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


def _annotation_value_node(value: str, lang: Optional[str], dtype: Optional[str], prefix_map: Dict[str, str]):
    if dtype:
        dt_uri = _base_datatype_iri(dtype, prefix_map) if dtype.startswith("xsd:") or ":" in dtype else URIRef(dtype)
        return Literal(value, datatype=dt_uri)
    if lang:
        return Literal(value, lang=lang)
    if ":" in value:
        pfx, local = value.split(":", 1)
        if pfx in prefix_map:
            return URIRef(prefix_map[pfx] + local)
    return Literal(value)


def _emit_inline_datatype_range(g: Graph, attr: UmlAttribute, prefix_map: Dict[str, str]) -> BNode:
    t = attr.type_curie_or_primitive
    if ":" in t:
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


def _build_token_index(model: Model, prefix_map: Dict[str, str]):
    class_token_to_uri: Dict[str, URIRef] = {}
    enum_token_to_uri: Dict[str, URIRef] = {}
    dt_token_to_uri: Dict[str, URIRef] = {}

    for cls in model.classes.values():
        base_ident = _preferred_ident(cls.curie, cls.name, "Class") or ""
        if not base_ident:
            continue
        uri = _expand(base_ident, prefix_map)
        if cls.curie:
            class_token_to_uri[cls.curie] = uri
        if cls.name:
            class_token_to_uri[cls.name] = uri

    for en in model.enumerations.values():
        base_ident = _preferred_ident(en.curie, en.name, "Enumeration") or ""
        if not base_ident:
            continue
        uri = _expand(base_ident, prefix_map)
        if en.curie:
            enum_token_to_uri[en.curie] = uri
        if en.name:
            enum_token_to_uri[en.name] = uri

    for dt in model.datatypes.values():
        base_ident = _preferred_ident(dt.curie, dt.name, "Datatype") or ""
        if not base_ident:
            continue
        uri = _expand(base_ident, prefix_map)
        if dt.curie:
            dt_token_to_uri[dt.curie] = uri
        if dt.name:
            dt_token_to_uri[dt.name] = uri

    return class_token_to_uri, enum_token_to_uri, dt_token_to_uri


def _ensure_object_property(g: Graph, prop_uri: URIRef) -> None:
    g.add((prop_uri, RDF.type, OWL.ObjectProperty))


def _add_literal_if_absent(g: Graph, subject: URIRef, predicate: URIRef, value: str) -> None:
    if (subject, predicate, None) not in g:
        g.add((subject, predicate, Literal(value)))


def _classify_target(
    attr: UmlAttribute,
    prefix_map: Dict[str, str],
    class_token_to_uri: Dict[str, URIRef],
    enum_token_to_uri: Dict[str, URIRef],
    dt_token_to_uri: Dict[str, URIRef],
) -> Tuple[str, URIRef]:
    target = attr.type_curie_or_primitive
    if not target:
        raise ValueError(
            f"Attribute '{attr.name}' on '{attr.class_curie}' is missing ClassEnumOrPrimitiveType"
        )

    if target in class_token_to_uri:
        return "object", class_token_to_uri[target]
    if target in enum_token_to_uri:
        return "object", enum_token_to_uri[target]
    if target in dt_token_to_uri:
        return "datatype", dt_token_to_uri[target]

    if target.startswith("xsd:"):
        base_uri = _base_datatype_iri(target, prefix_map)
        return "datatype", base_uri

    expanded = _expand(target, prefix_map)
    if expanded in class_token_to_uri.values():
        return "object", expanded
    if expanded in enum_token_to_uri.values():
        return "object", expanded
    if expanded in dt_token_to_uri.values():
        return "datatype", expanded

    raise ValueError(
        f"Unknown ClassEnumOrPrimitiveType '{target}' for attribute '{attr.name}' on class '{attr.class_curie}'. "
        f"It does not resolve to a class, enumeration, named datatype, or xsd: primitive."
    )


def _validate_model(model: Model, prefix_map: Dict[str, str], strict: bool = False):
    errors: List[str] = []
    missing_prefixes: set[str] = set()
    warnings: Dict[str, List[str]] = {"choice": [], "semantic": [], "annotation": []}

    # Duplicate / missing identifiers
    def _check_identities(items, kind: str):
        seen: Dict[str, str] = {}
        for obj in items:
            curie = getattr(obj, "curie", None)
            name = getattr(obj, "name", None)
            ident = curie or name
            if not ident:
                errors.append(f"{kind} is missing both CURIE and Name")
                continue
            if ident in seen:
                errors.append(f"Duplicate {kind} identifier '{ident}'")
            else:
                seen[ident] = kind

    _check_identities(model.classes.values(), "Class")
    _check_identities(model.enumerations.values(), "Enumeration")
    _check_identities(model.datatypes.values(), "Datatype")
    _check_identities(model.attributes, "Attribute")
    _check_identities(model.annotation_properties.values(), "AnnotationProperty")

    class_token_to_uri, enum_token_to_uri, dt_token_to_uri = _build_token_index(model, prefix_map)

    # Prefix coverage
    def _check_prefix(token: str, context: str):
        if ":" in token:
            pfx = token.split(":", 1)[0]
            if pfx != "xsd" and pfx not in prefix_map:
                missing_prefixes.add(pfx)

    for t in list(class_token_to_uri.keys()) + list(enum_token_to_uri.keys()) + list(dt_token_to_uri.keys()):
        _check_prefix(t, "identifiers")
    for attr in model.attributes:
        _check_prefix(attr.type_curie_or_primitive, f"attribute '{attr.name}' type")

    # Multiplicities
    for attr in model.attributes:
        if attr.min_cardinality is not None and attr.min_cardinality < 0:
            errors.append(f"Attribute '{attr.name}' has min_cardinality < 0")
        if (
            attr.min_cardinality is not None
            and isinstance(attr.max_cardinality, int)
            and attr.max_cardinality is not None
            and attr.min_cardinality > attr.max_cardinality
        ):
            errors.append(f"Attribute '{attr.name}' has min_cardinality > max_cardinality")

    # Attribute target resolution
    for attr in model.attributes:
        try:
            _classify_target(attr, prefix_map, class_token_to_uri, enum_token_to_uri, dt_token_to_uri)
        except ValueError as e:
            errors.append(str(e))

    # Choice members resolution
    attrs_by_class: Dict[str, List[UmlAttribute]] = {}
    for attr in model.attributes:
        attrs_by_class.setdefault(attr.class_curie, []).append(attr)
    for cls in model.classes.values():
        if not cls.choice_of:
            continue
        tokens = cls.choice_of
        for tok in tokens:
            if tok in class_token_to_uri:
                continue
            found_attr = False
            for candidate in attrs_by_class.get(cls.curie, []) + attrs_by_class.get(cls.name or "", []):
                if tok in (candidate.name, candidate.curie):
                    found_attr = True
                    break
            if not found_attr:
                warnings["choice"].append(
                    f"Choice member '{tok}' on class '{cls.curie or cls.name}' not found as class or attribute"
                )

        if cls.choice_semantics and cls.choice_semantics.lower() not in ("exclusive", "inclusive"):
            warnings["semantic"].append(
                f"ChoiceSemantics '{cls.choice_semantics}' on class '{cls.curie or cls.name}' is not recognized"
            )

    # Annotations: basic field presence
    for ann in model.annotations:
        if not ann.target_curie or not ann.property_curie or ann.value == "":
            errors.append("Annotation row is missing TargetCurie, AnnotationProperty, or Value")

    # Property chains
    for pc in model.property_chains:
        if not pc.enabled:
            continue
        if not pc.superproperty_iri:
            errors.append("Property chain is missing superproperty_iri")
            continue
        if not _is_iri(pc.superproperty_iri):
            errors.append(f"Property chain superproperty_iri is not a valid IRI: {pc.superproperty_iri}")
        if len(pc.chain_property_iris) < 2:
            errors.append(
                f"Property chain for {pc.superproperty_iri} must have length >= 2"
            )
        for iri in pc.chain_property_iris:
            if not _is_iri(iri):
                errors.append(
                    f"Property chain for {pc.superproperty_iri} has invalid IRI: {iri}"
                )

    flat_warnings = []
    if missing_prefixes:
        flat_warnings.append("Prefixes not declared: " + ", ".join(sorted(missing_prefixes)))
    for category, msgs in warnings.items():
        if msgs:
            flat_warnings.extend(msgs)

    if errors or (strict and flat_warnings):
        raise ValueError("Validation failed: " + "; ".join(errors + ([] if not strict else flat_warnings)))

    if missing_prefixes:
        log.warning("Validation warnings (prefix): %s", ", ".join(sorted(missing_prefixes)))
    for cat, msgs in warnings.items():
        if msgs:
            log.warning("Validation warnings (%s): %s", cat, "; ".join(msgs))


def build_ontology(model: Model, ontology_iri: str, prefix_str: str, strict: bool = False) -> Graph:
    g = Graph()
    prefix_map = parse_prefixes(prefix_str)
    log.info("Prefixes in use: %s", ", ".join(f"{pfx}={iri}" for pfx, iri in prefix_map.items()))

    _validate_model(model, prefix_map, strict=strict)

    g.bind("rdf", RDF, replace=True)
    g.bind("rdfs", RDFS, replace=True)
    g.bind("owl", OWL, replace=True)
    g.bind("xsd", XSD, replace=True)
    g.bind("xml", XMLNS, replace=True)
    g.bind("dct", DCTERMS, replace=True)
    g.bind("dcat", DCAT, replace=True)

    for pfx, iri in prefix_map.items():
        g.bind(pfx, Namespace(iri), replace=True)

    ont_uri = URIRef(ontology_iri)
    g.add((ont_uri, RDF.type, OWL.Ontology))
    # Default/base prefix for ontology (for Prefix: : ...)
    if ontology_iri:
        base_ns = ontology_iri
        if not base_ns.endswith(("#", "/")):
            base_ns = base_ns + "#"
        g.bind("", Namespace(base_ns), replace=True)

    # Index classes by token (curie and name) for Choice lookup and defaults
    class_by_token: Dict[str, UmlClass] = {}
    for cls in model.classes.values():
        if cls.curie:
            class_by_token[cls.curie] = cls
        if cls.name:
            class_by_token[cls.name] = cls

    # Emit classes
    for cls in model.classes.values():
        ident = _preferred_ident(cls.curie, cls.name, "Class")
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

    # Enumerations
    for en in model.enumerations.values():
        ident = _preferred_ident(en.curie, en.name, "Enumeration")
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

    # Annotation properties
    for ap in model.annotation_properties.values():
        ap_ident = _preferred_ident(ap.curie, ap.name, "AnnotationProperty")
        if not ap_ident:
            continue
        ap_uri = _expand(ap_ident, prefix_map)
        g.add((ap_uri, RDF.type, OWL.AnnotationProperty))
        if ap.name:
            g.add((ap_uri, RDFS.label, Literal(ap.name)))
        if ap.definition:
            g.add((ap_uri, RDFS.comment, Literal(ap.definition)))

    class_token_to_uri, enum_token_to_uri, dt_token_to_uri = _build_token_index(model, prefix_map)

    restrictions_by_domain: Dict[URIRef, List[URIRef]] = {}
    restrictions_by_attr: Dict[Tuple[str, str], URIRef] = {}

    # Build attributes: properties + qualified restrictions
    for attr in model.attributes:
        prop_ident = _preferred_ident(attr.curie, attr.name, "Attribute property")
        if not prop_ident:
            continue

        domain_uri = class_token_to_uri.get(attr.class_curie)
        if domain_uri is None:
            log.warning(
                "Attribute '%s' references class '%s' that was not in the model; expanding directly",
                attr.name,
                attr.class_curie,
            )
            domain_uri = _expand(attr.class_curie, prefix_map)

        prop_uri = _expand(prop_ident, prefix_map)

        kind, target_uri = _classify_target(attr, prefix_map, class_token_to_uri, enum_token_to_uri, dt_token_to_uri)

        # Determine the actual range node used on the property
        if kind == "object":
            range_node: Union[URIRef, BNode] = target_uri
            g.add((prop_uri, RDF.type, OWL.ObjectProperty))
            g.add((prop_uri, RDFS.domain, domain_uri))
            g.add((prop_uri, RDFS.range, range_node))
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
            if has_inline and str(target_uri).startswith(str(XSD)):
                range_node = _emit_inline_datatype_range(g, attr, prefix_map)
                g.add((prop_uri, RDFS.range, range_node))
            else:
                range_node = target_uri
                g.add((prop_uri, RDFS.range, range_node))

        if attr.name:
            g.add((prop_uri, RDFS.label, Literal(attr.name)))
        if attr.definition:
            g.add((prop_uri, RDFS.comment, Literal(attr.definition)))

        # Qualified cardinality restrictions
        if attr.min_cardinality is not None or attr.max_cardinality is not None:
            restr = BNode()
            g.add((restr, RDF.type, OWL.Restriction))
            g.add((restr, OWL.onProperty, prop_uri))

            if kind == "object":
                g.add((restr, OWL.onClass, range_node))
            else:
                g.add((restr, OWL.onDataRange, range_node))

            if (
                attr.min_cardinality is not None
                and attr.max_cardinality is not None
                and attr.max_cardinality != "*"
                and attr.min_cardinality == attr.max_cardinality
            ):
                g.add((
                    restr,
                    OWL.cardinality,
                    Literal(attr.min_cardinality, datatype=XSD.nonNegativeInteger),
                ))
            else:
                if attr.min_cardinality is not None:
                    g.add((
                        restr,
                        OWL.minCardinality,
                        Literal(attr.min_cardinality, datatype=XSD.nonNegativeInteger),
                    ))
                if attr.max_cardinality not in (None, "*"):
                    g.add((
                        restr,
                        OWL.maxCardinality,
                        Literal(attr.max_cardinality, datatype=XSD.nonNegativeInteger),
                    ))
            cls_for_attr = class_by_token.get(attr.class_curie)
            choice_tokens = set(cls_for_attr.choice_of) if cls_for_attr else set()
            is_choice_member = bool(
                cls_for_attr
                and choice_tokens
                and (
                    (attr.name and attr.name in choice_tokens)
                    or (attr.curie and attr.curie in choice_tokens)
                )
            )
            # Avoid duplicating choice members as direct subclass restrictions on the choice class.
            if not is_choice_member:
                restrictions_by_domain.setdefault(domain_uri, []).append(restr)

            # Index restriction by domain class tokens and attribute tokens (name/curie)
            if attr.name or attr.curie:
                class_keys = {attr.class_curie}
                cls_for_attr = class_by_token.get(attr.class_curie)
                if cls_for_attr:
                    if cls_for_attr.curie:
                        class_keys.add(cls_for_attr.curie)
                    if cls_for_attr.name:
                        class_keys.add(cls_for_attr.name)
                for key in class_keys:
                    if attr.name:
                        restrictions_by_attr[(key, attr.name)] = restr
                    if attr.curie:
                        restrictions_by_attr[(key, attr.curie)] = restr

    # Attach restrictions to domains
    for domain_uri, restrs in restrictions_by_domain.items():
        for r in restrs:
            g.add((domain_uri, RDFS.subClassOf, r))

    # Property chain axioms
    for pc in model.property_chains:
        if not pc.enabled:
            continue
        super_uri = URIRef(pc.superproperty_iri)
        _ensure_object_property(g, super_uri)
        for iri in pc.chain_property_iris:
            _ensure_object_property(g, URIRef(iri))
        chain_nodes = [URIRef(iri) for iri in pc.chain_property_iris]
        head = _make_rdf_list(g, chain_nodes)
        g.add((super_uri, OWL.propertyChainAxiom, head))
        if pc.label:
            _add_literal_if_absent(g, super_uri, RDFS.label, pc.label)
        if pc.comment:
            _add_literal_if_absent(g, super_uri, RDFS.comment, pc.comment)
        if pc.source:
            _add_literal_if_absent(g, super_uri, DCTERMS.source, pc.source)

    # Choice semantics: ChoiceOf interpreted as alternative classes (preferred) or attributes (fallback)
    for cls in model.classes.values():
        if not cls.choice_of:
            continue
        class_ident = _preferred_ident(cls.curie, cls.name, "Class")
        if not class_ident:
            continue
        class_uri = _expand(class_ident, prefix_map)

        choice_members: List[URIRef] = []
        for choice_token in cls.choice_of:
            target = class_token_to_uri.get(choice_token)
            if target is not None:
                choice_members.append(target)
                continue
            # Fallback: attribute restriction by token on this class
            restr = None
            if cls.curie:
                restr = restrictions_by_attr.get((cls.curie, choice_token))
            if restr is None and cls.name:
                restr = restrictions_by_attr.get((cls.name, choice_token))
            if restr is not None:
                choice_members.append(restr)
                continue
            log.warning(
                "Choice member '%s' on class '%s' was not found among classes or attributes; ensure ChoiceOf lists class CURIEs/Names or attribute tokens.",
                choice_token,
                class_ident,
            )

        if not choice_members:
            continue

        union_class = BNode()
        g.add((union_class, RDF.type, OWL.Class))
        lst = _make_rdf_list(g, choice_members)
        g.add((union_class, OWL.unionOf, lst))
        g.add((class_uri, RDFS.subClassOf, union_class))

        if cls.choice_semantics and cls.choice_semantics.lower().startswith("exclusive"):
            disj = BNode()
            g.add((disj, RDF.type, OWL.AllDisjointClasses))
            disjoint_set = [class_uri] + choice_members
            g.add((disj, OWL.members, _make_rdf_list(g, disjoint_set)))

    # Apply annotations
    for ann in model.annotations:
        target_uri = _expand(ann.target_curie, prefix_map)
        prop_uri = _expand(ann.property_curie, prefix_map)
        val_node = _annotation_value_node(ann.value, ann.language, ann.datatype, prefix_map)
        g.add((target_uri, prop_uri, val_node))

    return g


def serialise_ontology(model: Model, ontology_iri: str, prefix_str: str, output_path, format: str = "xml", xml_base: str = None) -> None:
    g = build_ontology(model, ontology_iri, prefix_str)
    if xml_base and format == "xml":
        g.serialize(destination=str(output_path), format=format, xml_base=xml_base)
    else:
        g.serialize(destination=str(output_path), format=format)
