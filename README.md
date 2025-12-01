
# uml2semantics-python 0.9.26

A refactored Python implementation of the original `uml2semantics` tool, updated so that
OWL 2 semantics are used consistently throughout the generated ontology.

## Key features

- Converts UML models (via XMI/TSV) into OWL 2 ontologies
- Preserves UML class, property, and enumeration structure
- Generates OWL 2 class, object property, and data property axioms
- Supports datatype restrictions using proper OWL 2 patterns (DatatypeRestriction, facets)
- Choice patterns (inclusive/exclusive) mapped to union/disjointness
- Pluggable profiles for ISO 20022 and generic UML
- Declarative annotations via `AnnotationProperties.tsv` + `Annotations.tsv`

## Installation

```bash
pip install .
```

or, using `pipx`:

```bash
pipx install .
```

## Command-line usage

The main entry point is:

```bash
uml2semantics [OPTIONS]
```

Supported options (compatible with 0.8.2, extended):

- `-i, --input PATH` - UML/XMI input file
- `-o, --output PATH` - Output ontology path (RDF/XML, Turtle, or OWL/XML)
- `-f, --format {rdfxml,turtle,owlxml}` - Output serialisation format
- `-b, --base-iri IRI` - Base IRI for generated ontology
- `-p, --profile {generic,iso20022}` - Mapping profile to apply
- `--imports IRI` - Additional ontology IRI to import (repeatable)
- `--no-imports` - Disable automatic imports
- `--validate / --no-validate` - Turn structural validation on/off
- `--log-level {ERROR,WARNING,INFO,DEBUG}` - Logging verbosity
- `--dry-run` - Parse and build in memory, but do not write a file
- `--version` - Show version information and exit
- `--annotation-properties PATH` - TSV defining annotation properties
- `--annotations PATH` - TSV of annotation assertions

Example:

```bash
uml2semantics -i examples/simple-model.xmi -o examples/simple-model.owl -f turtle -p iso20022
```

## Python API

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
    prefix_str="ex=http://example.org/;rdfs=http://www.w3.org/2000/01/rdf-schema#;dct=http://purl.org/dc/terms/;xsd=http://www.w3.org/2001/XMLSchema#",
)
g.serialize("examples/demo.ttl", format="turtle")
```

### Annotation TSVs
- `AnnotationProperties.tsv` columns: `Curie`, `Name`, `Definition`
- `Annotations.tsv` columns: `TargetCurie`, `AnnotationProperty`, `Value`, `Language`, `Datatype`

### Choice semantics
- `ChoiceOf` on a class lists alternative class/attribute tokens.
- `ChoiceSemantics` = `exclusive` emits an `owl:unionOf` plus an `AllDisjointClasses` covering the choice and its members. Blank or `inclusive` emits only the union.

### Datatypes
- `BaseDatatype` is required when facets are present; a missing base raises an error to avoid defaulting to `xsd:string`.

See `docs/cli.md` and `docs/architecture.md` for more details.
