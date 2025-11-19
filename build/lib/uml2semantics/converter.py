from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD
from rdflib.collection import Collection

# Open namespaces for terms not exposed on rdflib's ClosedNamespace
OWL_NS = Namespace(str(OWL))
XSD_FACET = Namespace(str(XSD))


@dataclass
class PrefixConfig:
    prefixes: Dict[str, Namespace] = field(default_factory=dict)

    @classmethod
    def from_string(cls, prefix_str: str | None) -> "PrefixConfig":
        if not prefix_str:
            return cls()

        ns_map: Dict[str, Namespace] = {}
        parts = [p.strip() for p in prefix_str.split(",") if p.strip()]
        for part in parts:
            if ":" not in part:
                raise ValueError(f"Invalid prefix '{part}', expected 'prefix:IRI'.")
            prefix, iri = part.split(":", 1)
            iri = iri.strip()
            if not iri:
                raise ValueError(f"Missing IRI for prefix '{prefix}'.")
            ns_map[prefix] = Namespace(iri)
        return cls(prefixes=ns_map)


def _slug(label: str) -> str:
    return (
        label.strip()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace("-", "_")
    )


def _resolve_iri(
    token: str,
    prefixes: Dict[str, Namespace],
    base_iri: str,
    kind: str,
    fallback_label: Optional[str] = None,
) -> URIRef:
    token = (token or "").strip()
    if token:
        if ":" in token:
            pfx, local = token.split(":", 1)
            if pfx in prefixes:
                return prefixes[pfx][local]
        return URIRef(base_iri.rstrip("#/") + "#" + _slug(token))

    if fallback_label:
        return URIRef(base_iri.rstrip("#/") + "#" + _slug(fallback_label))

    raise ValueError(f"Cannot mint IRI for empty {kind} identifier")


def _is_xsd_datatype(s: str) -> bool:
    return s.startswith("xsd:") or s.startswith(str(XSD))


def _datatype_iri(type_token: str) -> URIRef:
    if type_token.startswith("xsd:"):
        local = type_token.split(":", 1)[1]
        return getattr(XSD, local)
    return URIRef(type_token)


def _build_restricted_datatype(
    g: Graph,
    base_dt: URIRef,
    row: Dict[str, str],
) -> URIRef:
    """Build an owl:DatatypeRestriction node if facet columns are present.

    Supported facet columns (on either Attributes.tsv or Datatypes.tsv):
      - MinInclusive, MaxInclusive, MinExclusive, MaxExclusive
      - Pattern
      - MinLength, MaxLength
      - TotalDigits, FractionDigits

    If no facets are present, returns base_dt unchanged.
    """
    facets: Dict[str, str] = {}

    if row.get("MinInclusive"):
        facets["minInclusive"] = row["MinInclusive"]
    if row.get("MaxInclusive"):
        facets["maxInclusive"] = row["MaxInclusive"]
    if row.get("MinExclusive"):
        facets["minExclusive"] = row["MinExclusive"]
    if row.get("MaxExclusive"):
        facets["maxExclusive"] = row["MaxExclusive"]

    if row.get("MinLength"):
        facets["minLength"] = row["MinLength"]
    if row.get("MaxLength"):
        facets["maxLength"] = row["MaxLength"]

    if row.get("TotalDigits"):
        facets["totalDigits"] = row["TotalDigits"]
    if row.get("FractionDigits"):
        facets["fractionDigits"] = row["FractionDigits"]

    if row.get("Pattern"):
        facets["pattern"] = row["Pattern"]

    if not facets:
        return base_dt

    dt_node = BNode()
    # Use open OWL namespace so DatatypeRestriction is always available
    g.add((dt_node, RDF.type, OWL_NS.DatatypeRestriction))
    g.add((dt_node, OWL.onDatatype, base_dt))

    lst = BNode()
    g.add((dt_node, OWL.withRestrictions, lst))

    facet_nodes = []
    for facet_name, literal_lex in facets.items():
        facet_node = BNode()
        # Use open XSD namespace for facet IRIs (minInclusive, pattern, etc.)
        facet_prop = XSD_FACET[facet_name]

        if facet_name in {"minInclusive", "maxInclusive", "minExclusive", "maxExclusive"}:
            lit_dt = base_dt
        elif facet_name in {"minLength", "maxLength", "totalDigits", "fractionDigits"}:
            lit_dt = XSD.integer
        elif facet_name == "pattern":
            lit_dt = XSD.string
        else:
            lit_dt = XSD.string

        g.add((facet_node, facet_prop, Literal(literal_lex, datatype=lit_dt)))
        facet_nodes.append(facet_node)

    Collection(g, lst, facet_nodes)

    return dt_node


Node = Union[URIRef, BNode]


class Uml2OwlConverter:
    def __init__(self, base_iri: str, prefixes: Dict[str, Namespace] | None = None):
        if not base_iri:
            raise ValueError("base_iri (ontology IRI) is required")

        self.base_iri = base_iri.rstrip("#/")
        self.prefixes = prefixes or {}

        g = Graph()
        g.bind("owl", OWL)
        g.bind("rdfs", RDFS)
        g.bind("xsd", XSD)
        for p, ns in self.prefixes.items():
            g.bind(p, ns)

        self.ontology_iri = URIRef(self.base_iri)
        g.add((self.ontology_iri, RDF.type, OWL.Ontology))

        self.graph = g

        self.class_iris: Dict[str, URIRef] = {}
        self.enum_class_iris: Dict[str, URIRef] = {}
        self.enum_value_iris: Dict[Tuple[str, str], URIRef] = {}
        self.property_iris: Dict[Tuple[str, str], URIRef] = {}
        self.named_datatypes: Dict[str, URIRef] = {}
        self.annotation_prop_iris: Dict[str, URIRef] = {}

    # ---------- Datatypes -------------------------------------------------------

    def add_datatypes(self, rows: List[Dict[str, str]]) -> None:
        for row in rows:
            curie = (row.get("Curie") or "").strip()
            name = (row.get("Name") or "").strip()
            base = (row.get("BaseDatatype") or "").strip()
            definition = (row.get("Definition") or "").strip()

            if not base:
                raise ValueError("Datatypes.tsv row missing BaseDatatype")

            key = curie or name
            if not key:
                raise ValueError("Datatypes.tsv row requires Curie or Name")

            dt_iri = _resolve_iri(curie or name, self.prefixes, self.base_iri,
                                  "datatype", fallback_label=name or curie)
            base_dt = _datatype_iri(base)

            restriction_node = _build_restricted_datatype(self.graph, base_dt, row)

            g = self.graph
            g.add((dt_iri, RDF.type, RDFS.Datatype))
            if name:
                g.add((dt_iri, RDFS.label, Literal(name)))
            if definition:
                g.add((dt_iri, RDFS.comment, Literal(definition)))

            if restriction_node != base_dt:
                g.add((dt_iri, OWL.equivalentClass, restriction_node))

            self.named_datatypes[key] = dt_iri

    # ---------- Classes / Enums -------------------------------------------------

    def add_classes(self, rows: List[Dict[str, str]]) -> None:
        for row in rows:
            curie = row.get("Curie", "")
            name = row.get("Name", "")
            definition = row.get("Definition", "")
            parents = (row.get("ParentNames", "") or "").split("|")

            if not (curie or name):
                raise ValueError("Class row requires at least Curie or Name")

            cls_iri = _resolve_iri(curie or name, self.prefixes,
                                   self.base_iri, "class", fallback_label=name)
            key = name or curie
            self.class_iris[key] = cls_iri

            g = self.graph
            g.add((cls_iri, RDF.type, OWL.Class))
            if name:
                g.add((cls_iri, RDFS.label, Literal(name)))
            if definition:
                g.add((cls_iri, RDFS.comment, Literal(definition)))

            for p in parents:
                p = p.strip()
                if p:
                    parent_iri = _resolve_iri(
                        p, self.prefixes,
                        self.base_iri,
                        "parent-class",
                        fallback_label=p,
                    )
                    g.add((cls_iri, RDFS.subClassOf, parent_iri))

    def add_enumerations(self, rows: List[Dict[str, str]]) -> None:
        for row in rows:
            curie = row.get("Curie", "")
            name = row.get("Name", "")
            definition = row.get("Definition", "")

            if not (curie or name):
                raise ValueError("Enumeration row requires Curie or Name")

            enum_iri = _resolve_iri(curie or name, self.prefixes,
                                    self.base_iri, "enumeration", fallback_label=name)
            key = curie or name
            self.enum_class_iris[key] = enum_iri

            g = self.graph
            g.add((enum_iri, RDF.type, OWL.Class))
            if name:
                g.add((enum_iri, RDFS.label, Literal(name)))
            if definition:
                g.add((enum_iri, RDFS.comment, Literal(definition)))

    def add_enum_values(self, rows: List[Dict[str, str]]) -> None:
        for row in rows:
            enum_ref = (row.get("Enumeration") or "").strip()
            curie = row.get("Curie", "")
            name = row.get("Name", "")
            definition = row.get("Definition", "")

            if not enum_ref:
                raise ValueError("EnumerationNamedValues row missing 'Enumeration'")
            if not (curie or name):
                raise ValueError("EnumerationNamedValues row requires Curie or Name")

            enum_cls_iri = self.enum_class_iris.get(enum_ref)
            if not enum_cls_iri:
                enum_cls_iri = _resolve_iri(
                    enum_ref,
                    self.prefixes,
                    self.base_iri,
                    "enumeration-ref",
                    fallback_label=enum_ref,
                )

            indiv_iri = _resolve_iri(
                curie or name,
                self.prefixes,
                self.base_iri,
                "enum-value",
                fallback_label=name,
            )

            self.enum_value_iris[(enum_ref, name or curie)] = indiv_iri

            g = self.graph
            g.add((indiv_iri, RDF.type, enum_cls_iri))
            if name:
                g.add((indiv_iri, RDFS.label, Literal(name)))
            if definition:
                g.add((indiv_iri, RDFS.comment, Literal(definition)))

    # ---------- Attributes ------------------------------------------------------

    def add_attributes(self, rows: List[Dict[str, str]]) -> None:
        for row in rows:
            cls_ref = (row.get("Class") or row.get("ClassCurie") or "").strip()
            if not cls_ref:
                raise ValueError("Attribute row missing 'Class'")

            attr_curie = (row.get("Curie") or "").strip()
            attr_name = (row.get("Name") or "").strip()
            type_ref = (row.get("ClassEnumOrPrimitiveType") or "").strip()
            min_mult = (row.get("MinMultiplicity") or "").strip()
            max_mult = (row.get("MaxMultiplicity") or "").strip()
            definition = (row.get("Definition") or "").strip()

            domain_iri = _resolve_iri(
                cls_ref,
                self.prefixes,
                self.base_iri,
                "class",
                fallback_label=cls_ref,
            )

            prop_iri = _resolve_iri(
                attr_curie or attr_name or f"{cls_ref}_{type_ref or 'attr'}",
                self.prefixes,
                self.base_iri,
                "property",
                fallback_label=attr_name or f"{cls_ref}_{type_ref or 'attr'}",
            )

            self.property_iris[(cls_ref, attr_name or attr_curie or str(prop_iri))] = prop_iri

            g = self.graph

            if not type_ref:
                prop_type = OWL.ObjectProperty
                range_iri = OWL.Thing
                is_datatype = False
            elif type_ref in self.named_datatypes:
                prop_type = OWL.DatatypeProperty
                range_iri = self.named_datatypes[type_ref]
                is_datatype = True
            elif type_ref in self.enum_class_iris:
                prop_type = OWL.ObjectProperty
                range_iri = self.enum_class_iris[type_ref]
                is_datatype = False
            elif _is_xsd_datatype(type_ref):
                prop_type = OWL.DatatypeProperty
                base_dt = _datatype_iri(type_ref)
                range_iri = _build_restricted_datatype(self.graph, base_dt, row)
                is_datatype = True
            else:
                prop_type = OWL.ObjectProperty
                is_datatype = False
                if type_ref in self.class_iris:
                    range_iri = self.class_iris[type_ref]
                elif type_ref in self.enum_class_iris:
                    range_iri = self.enum_class_iris[type_ref]
                else:
                    range_iri = _resolve_iri(
                        type_ref,
                        self.prefixes,
                        self.base_iri,
                        "range-class",
                        fallback_label=type_ref,
                    )

            g.add((prop_iri, RDF.type, prop_type))
            g.add((prop_iri, RDFS.domain, domain_iri))
            g.add((prop_iri, RDFS.range, range_iri))
            if attr_name:
                g.add((prop_iri, RDFS.label, Literal(attr_name)))
            if definition:
                g.add((prop_iri, RDFS.comment, Literal(definition)))

            self._add_multiplicity_restrictions(
                domain_iri,
                prop_iri,
                range_iri,
                is_datatype,
                min_mult,
                max_mult,
            )

    # ---------- Multiplicity ----------------------------------------------------

    def _add_multiplicity_restrictions(
        self,
        domain_iri: URIRef,
        prop_iri: URIRef,
        range_iri: URIRef,
        is_datatype: bool,
        min_mult: str,
        max_mult: str,
    ) -> None:
        g = self.graph

        min_m = (min_mult or "").strip()
        max_m = (max_mult or "").strip()

        # Default multiplicity = 1..1
        if not min_m and not max_m:
            min_m, max_m = "1", "1"

        # Exact cardinality when both numeric and equal
        if min_m.isdigit() and max_m.isdigit() and int(min_m) == int(max_m):
            card = int(min_m)
            r = BNode()
            g.add((domain_iri, RDFS.subClassOf, r))
            g.add((r, RDF.type, OWL.Restriction))
            g.add((r, OWL.onProperty, prop_iri))
            g.add((r, OWL.cardinality, Literal(card)))
            return

        # someValuesFrom if min > 0
        if min_m and min_m != "0":
            r = BNode()
            g.add((domain_iri, RDFS.subClassOf, r))
            g.add((r, RDF.type, OWL.Restriction))
            g.add((r, OWL.onProperty, prop_iri))
            g.add((r, OWL.someValuesFrom, range_iri))

        # maxCardinality restriction if max is numeric
        if max_m and max_m != "*" and max_m.isdigit():
            card = int(max_m)
            r = BNode()
            g.add((domain_iri, RDFS.subClassOf, r))
            g.add((r, RDF.type, OWL.Restriction))
            g.add((r, OWL.onProperty, prop_iri))
            g.add((r, OWL.maxCardinality, Literal(card)))

    # ---------- Annotation properties ------------------------------------------

    def add_annotation_properties(self, rows: List[Dict[str, str]]) -> None:
        for row in rows:
            curie = (row.get("Curie") or "").strip()
            name = (row.get("Name") or "").strip()
            definition = (row.get("Definition") or "").strip()

            key = curie or name
            if not key:
                raise ValueError("AnnotationProperties.tsv row requires Curie or Name")

            ap_iri = _resolve_iri(curie or name, self.prefixes, self.base_iri,
                                  "annotation-property", fallback_label=name or curie)

            g = self.graph
            g.add((ap_iri, RDF.type, OWL.AnnotationProperty))
            if name:
                g.add((ap_iri, RDFS.label, Literal(name)))
            if definition:
                g.add((ap_iri, RDFS.comment, Literal(definition)))

            self.annotation_prop_iris[key] = ap_iri

    def _resolve_annotation_target(self, kind: str, ident: str) -> URIRef:
        kind_l = (kind or "").strip().lower()
        ident = (ident or "").strip()

        # Ontology-level annotations
        if kind_l == "ontology":
            return self.ontology_iri

        # Attempt direct CURIE/IRI resolution first
        if ident:
            direct = _resolve_iri(ident, self.prefixes, self.base_iri,
                                  "annotation-target", fallback_label=ident)
        else:
            direct = self.ontology_iri

        if kind_l == "class":
            return self.class_iris.get(ident, direct)
        if kind_l == "datatype":
            return self.named_datatypes.get(ident, direct)
        if kind_l in {"enumeration", "enum"}:
            return self.enum_class_iris.get(ident, direct)
        if kind_l in {"property", "objectproperty", "datatypeproperty"}:
            for (_, name), iri in self.property_iris.items():
                if name == ident:
                    return iri
            return direct
        if kind_l == "individual":
            for (_, name), iri in self.enum_value_iris.items():
                if name == ident:
                    return iri
            return direct

        return direct

    def _build_annotation_literal(self, value: str, lang: str, datatype: str) -> Literal:
        value = value or ""
        lang = (lang or "").strip()
        dt = (datatype or "").strip()

        if dt:
            dt_iri = _datatype_iri(dt) if _is_xsd_datatype(dt) else URIRef(dt)
            return Literal(value, datatype=dt_iri)
        if lang:
            return Literal(value, lang=lang)
        return Literal(value)

    def add_annotations(self, rows: List[Dict[str, str]]) -> None:
        for row in rows:
            kind = row.get("TargetKind", "")
            target_id = row.get("TargetId", "")
            prop_id = row.get("PropertyId", "")
            value = row.get("Value", "")
            lang = row.get("Lang", "")
            datatype = row.get("Datatype", "")

            if not prop_id:
                raise ValueError("Annotations.tsv row missing PropertyId")

            target_iri = self._resolve_annotation_target(kind, target_id)

            # Resolve or mint the annotation property IRI
            if prop_id in self.annotation_prop_iris:
                ap_iri = self.annotation_prop_iris[prop_id]
            else:
                ap_iri = _resolve_iri(prop_id, self.prefixes, self.base_iri,
                                      "annotation-property", fallback_label=prop_id)
                # Treat it as an annotation property in the graph
                self.graph.add((ap_iri, RDF.type, OWL.AnnotationProperty))

            lit = self._build_annotation_literal(value, lang, datatype)
            self.graph.add((target_iri, ap_iri, lit))
