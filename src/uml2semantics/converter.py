from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD
from rdflib.collection import Collection


@dataclass
class PrefixConfig:
    prefixes: Dict[str, Namespace] = field(default_factory=dict)

    @classmethod
    def from_string(cls, prefix_str: str | None) -> "PrefixConfig":
        """Parse one or more prefix declarations of the form:
            "emp:http://example.com/ns#"
        Multiple entries may be comma-separated.
        """
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


Node = Union[URIRef, BNode]


class Uml2OwlConverter:
    """Core converter: given TSV rows (already parsed), produce an OWL ontology,
    including Choice (union) with optional exclusive semantics (disjointness to choice class).
    """

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
                        p, self.prefixes, self.base_iri,
                        "parent-class", fallback_label=p,
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
            elif _is_xsd_datatype(type_ref):
                prop_type = OWL.DatatypeProperty
                range_iri = _datatype_iri(type_ref)
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

    # ---------- Choice support --------------------------------------------------

    def add_choices_from_classes(self, class_rows: List[Dict[str, str]]) -> None:
        """Option A: read ChoiceOf & ChoiceSemantics from Classes.tsv rows."""
        for row in class_rows:
            choice_of = (row.get("ChoiceOf") or "").strip()
            if not choice_of:
                continue
            semantics = (row.get("ChoiceSemantics") or "exclusive").strip().lower()
            name = row.get("Name") or row.get("Curie")
            if not name:
                continue
            choice_cls = _resolve_iri(name, self.prefixes, self.base_iri, "choice-class")
            disjuncts = self._parse_choice_disjuncts(choice_of)
            self._emit_choice_axioms(choice_cls, disjuncts, semantics)

    def add_choices(self, choices_rows: List[Dict[str, str]], member_rows: List[Dict[str, str]]) -> None:
        """Option B: separate Choices.tsv and ChoiceMembers.tsv."""
        # Index members
        by_choice: Dict[str, list[Dict[str, str]]] = {}
        for m in member_rows or []:
            by_choice.setdefault(m.get("ChoiceClass", ""), []).append(m)

        for row in choices_rows or []:
            choice_name = (row.get("ChoiceClass") or "").strip()
            if not choice_name:
                continue
            semantics = (row.get("Semantics") or "exclusive").strip().lower()
            choice_cls = _resolve_iri(choice_name, self.prefixes, self.base_iri, "choice-class")
            members = by_choice.get(choice_name, [])
            # Build disjuncts
            disjuncts: list[Node] = []
            for m in members:
                kind = (m.get("Kind") or "").strip().lower()
                if kind == "class":
                    ref = (m.get("Ref") or "").strip()
                    if not ref:
                        continue
                    disjuncts.append(_resolve_iri(ref, self.prefixes, self.base_iri, "class", fallback_label=ref))
                elif kind == "datatyperestriction":
                    prop = (m.get("Property") or "").strip()
                    dtype = (m.get("Datatype") or "").strip()
                    if not prop or not dtype:
                        continue
                    prop_iri = _resolve_iri(prop, self.prefixes, self.base_iri, "property", fallback_label=prop)
                    restr = BNode()
                    self.graph.add((restr, RDF.type, OWL.Restriction))
                    self.graph.add((restr, OWL.onProperty, prop_iri))
                    self.graph.add((restr, OWL.someValuesFrom, _datatype_iri(dtype)))
                    disjuncts.append(restr)
            if disjuncts:
                self._emit_choice_axioms(choice_cls, disjuncts, semantics)

    # ---------- Internals -------------------------------------------------------

    def _parse_choice_disjuncts(self, choice_of: str) -> list[Node]:
        parts = [p.strip() for p in choice_of.split("|") if p.strip()]
        disjuncts: list[Node] = []
        for part in parts:
            if "xsd:" in part and ":" in part:
                # propertyName:xsd:type
                prop, dtype = part.split(":", 1)
                prop_iri = _resolve_iri(prop, self.prefixes, self.base_iri, "property", fallback_label=prop)
                restr = BNode()
                self.graph.add((restr, RDF.type, OWL.Restriction))
                self.graph.add((restr, OWL.onProperty, prop_iri))
                self.graph.add((restr, OWL.someValuesFrom, _datatype_iri(dtype)))
                disjuncts.append(restr)
            else:
                # class (name or CURIE)
                disjuncts.append(_resolve_iri(part, self.prefixes, self.base_iri, "class", fallback_label=part))
        return disjuncts

    def _emit_choice_axioms(self, choice_cls: URIRef, disjuncts: list[Node], semantics: str) -> None:
        # 1) SubClassOf (unionOf disjuncts)
        union_node = BNode()
        Collection(self.graph, union_node, disjuncts)
        union_expr = BNode()
        self.graph.add((union_expr, OWL.unionOf, union_node))
        self.graph.add((choice_cls, RDFS.subClassOf, union_expr))

        # 2) Disjointness against each disjunct if exclusive (XOR flavour)
        if semantics == "exclusive":
            for disj in disjuncts:
                ax = BNode()
                mem = BNode()
                self.graph.add((ax, RDF.type, OWL.AllDisjointClasses))
                self.graph.add((ax, OWL.members, mem))
                Collection(self.graph, mem, [choice_cls, disj])

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

        if not min_m and not max_m:
            min_m, max_m = "1", "1"

        if min_m and min_m != "0":
            r = BNode()
            g.add((domain_iri, RDFS.subClassOf, r))
            g.add((r, RDF.type, OWL.Restriction))
            g.add((r, OWL.onProperty, prop_iri))
            g.add((r, OWL.someValuesFrom, range_iri))

        if max_m and max_m != "*" and max_m.isdigit():
            card = int(max_m)
            r = BNode()
            g.add((domain_iri, RDFS.subClassOf, r))
            g.add((r, RDF.type, OWL.Restriction))
            g.add((r, OWL.onProperty, prop_iri))
            g.add((r, OWL.maxCardinality, Literal(card)))
