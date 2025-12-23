# Command‑line reference

This document describes the `uml2semantics` command‑line interface. It is
kept backwards‑compatible with version 0.8.2, while extending support
for OWL 2 semantics and profiles.

Run:

```bash
uml2semantics --help
```

to see the full list of options.

Additional TSV inputs:

- `--property-chains PATH` - TSV defining OWL 2 object property chains
  - `source` values are emitted as `dct:source` annotations on the super property

Example:

```
superproperty_iri	chain_property_iris	label	comment	source	enabled
http://example.com/rel/trace	http://example.com/rel/ME|http://example.com/rel/BE|http://example.com/rel/BC|http://example.com/rel/BA	TracePath	ME -> BE -> BC -> BA	spec-v1	true
```
