 uml2semantics (Python)

CLI/library to convert UML-style TSV specifications (Classes, Attributes, Enumerations, EnumerationNamedValues)
into an OWL 2 ontology using rdflib.

## New (v0.2.0)
- **Choice support** (ISO 20022-style): express a class as a union of alternatives with optional *exclusive* semantics (XOR).
  - Option A: add `ChoiceOf` and `ChoiceSemantics` columns to `Classes.tsv`.
  - Option B: use `Choices.tsv` and `ChoiceMembers.tsv` for clearer models with many alternatives.

## Quickstart

```bash
pip install .
uml2semantics   -c examples/Classes.tsv   -a examples/Attributes.tsv   -o out.owl   -p "iso:http://iso20022.example/ontology#"   -i "http://iso20022.example/ontology"
```

Open `out.owl` in Protégé to inspect the axioms. The example encodes:

```
Class: AcknowledgementReason7Choice
  SubClassOf:
    AcknowledgementReason7Code or (AddtlRsnInf some xsd:string)

DisjointClasses:
  (AcknowledgementReason7Choice and AcknowledgementReason7Code)
  (AcknowledgementReason7Choice and (AddtlRsnInf some xsd:string))
```
chrisd@midna:uml2semantics-python_v0.2.0 > ls
build  examples  pyproject.toml  README.md  src  tests
chrisd@midna:uml2semantics-python_v0.2.0 > cat README.md
# uml2semantics (Python)

CLI/library to convert UML-style TSV specifications (Classes, Attributes, Enumerations, EnumerationNamedValues)
into an OWL 2 ontology using rdflib.

## New (v0.2.0)
- **Choice support** (ISO 20022-style): express a class as a union of alternatives with optional *exclusive* semantics (XOR).
  - Option A: add `ChoiceOf` and `ChoiceSemantics` columns to `Classes.tsv`.
  - Option B: use `Choices.tsv` and `ChoiceMembers.tsv` for clearer models with many alternatives.

## Quickstart

```bash
pip install .
uml2semantics   -c examples/Classes.tsv   -a examples/Attributes.tsv   -o out.owl   -p "iso:http://iso20022.example/ontology#"   -i "http://iso20022.example/ontology"
```

Open `out.owl` in Protégé to inspect the axioms. The example encodes:

```
Class: AcknowledgementReason7Choice
  SubClassOf:
    AcknowledgementReason7Code or (AddtlRsnInf some xsd:string)

DisjointClasses:
  (AcknowledgementReason7Choice and AcknowledgementReason7Code)
  (AcknowledgementReason7Choice and (AddtlRsnInf some xsd:string))
```
