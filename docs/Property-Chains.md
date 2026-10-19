# Property chains

Pass a TSV file using `--property-chains PATH`.

`property_chains.tsv` columns (header required):

- `superproperty_iri` (required) - IRI of the owl:ObjectProperty to be asserted as the super property
- `chain_property_iris` (required) - `|`-separated list of object property IRIs in order
- `label` (optional) - rdfs:label for the super property (emitted only if absent)
- `comment` (optional) - rdfs:comment for the super property (emitted only if absent)
- `source` (optional) - provenance string emitted as `dct:source` on the super property (if absent)
- `enabled` (optional) - true/false (default true)

Example (ISO 20022 style navigation chain):

```
superproperty_iri	chain_property_iris	label	comment	source	enabled
http://example.com/rel/trace	http://example.com/rel/ME|http://example.com/rel/BE|http://example.com/rel/BC|http://example.com/rel/BA	TracePath	ME -> BE -> BC -> BA	spec-v1	true
```

Emits (Turtle excerpt):

```turtle
@prefix dct: <http://purl.org/dc/terms/> .

<http://example.com/rel/trace>
  dct:source "spec-v1" .
```


Also supply at least one model input (for example `--classes`); the CLI currently rejects a property-chain-only invocation. Use full IRIs for chain members.
