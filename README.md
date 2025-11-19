# uml2semantics (Python)

CLI/library to convert UML-style TSV specifications into an OWL 2 ontology using rdflib.

Supported inputs:
- Classes.tsv
- Attributes.tsv
- Enumerations.tsv
- EnumerationNamedValues.tsv
- Datatypes.tsv

## New in v0.5.1

- Fix: use an open OWL namespace for `DatatypeRestriction` and an open XSD namespace for facet IRIs.
  - This resolves `AttributeError: term 'DatatypeRestriction' not in namespace 'http://www.w3.org/2002/07/owl#'`.
- Keeps:
  - Named datatypes via `Datatypes.tsv` (e.g. `ISO4217CurrencyCode`).
  - Datatype facets for attributes.
  - ISO 4217 `CurrencyCode` enumeration examples.

## Quickstart

```bash
pip install .

uml2semantics   -c examples/Classes.tsv   -a examples/Attributes.tsv   --datatypes examples/Datatypes.tsv   -e examples/Enumerations.tsv   -n examples/EnumerationNamedValues.tsv   -o out.owl   -p "iso:http://iso20022.example/ontology#"   -i "http://iso20022.example/ontology"
```
