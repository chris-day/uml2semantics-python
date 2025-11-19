# uml2semantics (Python)

CLI/library to convert UML-style TSV specifications (Classes, Attributes, Enumerations, EnumerationNamedValues, Datatypes)
into an OWL 2 ontology using rdflib.

Based upon the original works by Henriette Harmse https://github.com/henrietteharmse/uml2semantics

## New in v0.4.0

- **Named datatypes** via `Datatypes.tsv`:
  - Columns: `Curie`, `Name`, `BaseDatatype`, `Definition`, plus facet columns
  - Facets: `MinInclusive`, `MaxInclusive`, `MinExclusive`, `MaxExclusive`, `Pattern`, `MinLength`, `MaxLength`, `TotalDigits`, `FractionDigits`
  - Emitted as OWL 2 `DatatypeRestriction` with a named `rdfs:Datatype` linked by `owl:equivalentClass`.
- **Reuse in Attributes.tsv**:
  - `ClassEnumOrPrimitiveType` can now reference:
    - primitive XSD types (e.g. `xsd:string`, `xsd:decimal`, `xsd:gYearMonth`)
    - or **named datatypes** defined in `Datatypes.tsv` (e.g. `ISO4217CurrencyCode`, `BIC11`, `LEI20`).
- Existing features retained:
  - Choice patterns (Option A: `ChoiceOf` / `ChoiceSemantics` in `Classes.tsv`; Option B: `Choices.tsv` / `ChoiceMembers.tsv`).
  - Datatype facet support directly on attributes when you don't want to define a reusable datatype.


## Quickstart

```bash
pip install .

uml2semantics   -c examples/Classes.tsv   -a examples/Attributes.tsv   --datatypes examples/Datatypes.tsv   -o out.owl   -p "iso:http://iso20022.example/ontology#"   -i "http://iso20022.example/ontology"
```

Open `out.owl` in Protégé to inspect:

- `AcknowledgementReason7Choice` (code vs text) and `Quantity6Choice` (XOR between two classes)
- Faceted datatypes on attributes (decimal, string with pattern, gYearMonth)
- Named datatypes such as `ISO4217CurrencyCode`, `BIC11`, and `LEI20`.
