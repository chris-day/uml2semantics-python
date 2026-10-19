# Python API

Run this example from the repository root after installing the project.


```python
from uml2semantics.ontology_builder import build_ontology
from uml2semantics.tsv_loader import load_model

model = load_model(
    classes_tsv="examples/Classes.tsv",
    attributes_tsv="examples/Attributes.tsv",
    datatypes_tsv="examples/Datatypes.tsv",
    enums_tsv="examples/Enumerations.tsv",
    enum_literals_tsv="examples/EnumerationNamedValues.tsv",
    annotation_properties_tsv="examples/AnnotationProperties.tsv",
    annotations_tsv="examples/Annotations.tsv",
)

g = build_ontology(
    model,
    ontology_iri="http://example.org/uml2semantics/demo#",
    prefix_str="iso=http://iso20022.example/ontology#;ex=http://example.org/;rdfs=http://www.w3.org/2000/01/rdf-schema#;dct=http://purl.org/dc/terms/;xsd=http://www.w3.org/2001/XMLSchema#",
)
g.serialize("examples/demo.ttl", format="turtle")
```


See [annotations](Annotations.md) and [property chains](Property-Chains.md) for additional inputs.
