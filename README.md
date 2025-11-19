# uml2semantics (Python)

CLI/library to convert UML-style TSV specifications into an OWL 2 ontology using rdflib.

Supported inputs:
- Classes.tsv
- Attributes.tsv
- Enumerations.tsv
- EnumerationNamedValues.tsv
- Datatypes.tsv

## New in v0.5.0

- Added **ISO 4217 CurrencyCode enumeration examples**:
  - `examples/Enumerations.tsv` defining `CurrencyCode`
  - `examples/EnumerationNamedValues.tsv` with `GBP`, `EUR`, `USD`, `JPY`, `CHF`
  - `examples/Attributes.tsv` now includes `PartyIdentification.AccountCurrencyCode` using the enumeration.
- Retains:
  - Named datatypes via `Datatypes.tsv` (e.g. `ISO4217CurrencyCode`).
  - Datatype facets for attributes.

## Quickstart

```bash
pip install .

uml2semantics   -c examples/Classes.tsv   -a examples/Attributes.tsv   --datatypes examples/Datatypes.tsv   -e examples/Enumerations.tsv   -n examples/EnumerationNamedValues.tsv   -o out.owl   -p "iso:http://iso20022.example/ontology#"   -i "http://iso20022.example/ontology"
```
