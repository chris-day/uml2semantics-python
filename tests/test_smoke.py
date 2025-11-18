from pathlib import Path
from rdflib.namespace import RDFS
from rdflib import Namespace

from uml2semantics import Uml2OwlConverter


def test_graph_and_choice_union(tmp_path: Path):
    iso = Namespace("http://iso20022.example/ontology#")
    conv = Uml2OwlConverter(base_iri="http://iso20022.example/ontology")
    classes = [
        {"Curie":"iso:AckRsn7Choice", "Name":"AcknowledgementReason7Choice", "ChoiceOf":"AcknowledgementReason7Code|AddtlRsnInf:xsd:string", "ChoiceSemantics":"exclusive"},
        {"Curie":"iso:AckRsn7Code", "Name":"AcknowledgementReason7Code"},
    ]
    attrs = [
        {"Class":"AcknowledgementReason7Choice", "Name":"AddtlRsnInf", "ClassEnumOrPrimitiveType":"xsd:string", "MinMultiplicity":"0", "MaxMultiplicity":"1"}
    ]
    conv.add_classes(classes)
    conv.add_attributes(attrs)
    conv.add_choices_from_classes(classes)

    # Basic check: class exists
    assert (iso.AckRsn7Choice, None, None) in conv.graph
    # There should be a SubClassOf triple
    assert any(p == RDFS.subClassOf for s,p,o in conv.graph.triples((iso.AckRsn7Choice, None, None)))
