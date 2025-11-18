# uml2semantics (Python)

CLI/library to convert UML-style TSV specifications (Classes, Attributes, Enumerations, EnumerationNamedValues)
into an OWL 2 ontology using rdflib.

## New in v0.3.0
- **Choice support** (ISO 20022-style): express a class as a union of alternatives with optional *exclusive* semantics (XOR).
  - Option A: add `ChoiceOf` and `ChoiceSemantics` columns to `Classes.tsv`.
  - Option B: use `Choices.tsv` and `ChoiceMembers.tsv` for clearer models with many alternatives.
- **Datatype facet support** in `Attributes.tsv`:
  - `MinInclusive`, `MaxInclusive`, `MinExclusive`, `MaxExclusive`
  - `Pattern`
  - `MinLength`, `MaxLength`
  - `TotalDigits`, `FractionDigits`
- Facets are mapped to OWL 2 `owl:DatatypeRestriction` nodes transparently.

## Quickstart

```bash
pip install .

uml2semantics   -c examples/Classes.tsv   -a examples/Attributes.tsv   -o out.owl   -p "iso:http://iso20022.example/ontology#"   -i "http://iso20022.example/ontology"
```

Open `out.owl` in Protégé to inspect the axioms for:

- `AcknowledgementReason7Choice` (code vs text)
- `Quantity6Choice` (FinancialInstrumentQuantity1Choice vs OriginalAndCurrentQuantities1)
- Faceted datatypes (decimal, string with pattern, gYearMonth with pattern).
