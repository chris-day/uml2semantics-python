# Getting Started

## Overview

`uml2semantics` converts a set of UML-style TSV files into a complete OWL 2 ontology.

The basic workflow is:

1. Define your model in TSV files (classes, attributes, datatypes, enumerations, annotations).  
2. Run the CLI with those TSV files.  
3. Load the generated ontology into Protégé or another OWL tool.

---

## Installation

From a local checkout or release zip:

```bash
pip install .
```

Or using the zip artefact directly:

```bash
unzip uml2semantics-python-<version>.zip
cd uml2semantics-python-<version>
pip install .
```

---

## Minimal Example

```bash
uml2semantics   -c examples/Classes.tsv   -a examples/Attributes.tsv   --datatypes examples/Datatypes.tsv   -e examples/Enumerations.tsv   -n examples/EnumerationNamedValues.tsv   --annotation-properties examples/AnnotationProperties.tsv   --annotations examples/Annotations.tsv   -o out.ttl   -p "iso:http://iso20022.example/ontology#,rdfs:http://www.w3.org/2000/01/rdf-schema#,skos:http://www.w3.org/2004/02/skos/core#"   -i "http://iso20022.example/ontology"
```

---

## Output Formats

The output format is inferred from the `-o/--output` extension:

- `.ttl` → Turtle (`turtle`)  
- `.owl` or `.rdf` → RDF/XML (`xml`)  
- `.jsonld` or `.json` → JSON-LD (`json-ld`)  
- `.nt` → N-Triples (`nt`)  
