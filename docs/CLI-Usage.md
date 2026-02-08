# CLI Usage – Full Expanded Documentation

This section documents **every CLI parameter**, usage patterns, validation modes, error scenarios and complete examples.

## 1. Required Parameters

### -i, --ontology-iri
Base IRI of the ontology.

### At least one input TSV
Provide at least one of:
`--classes`, `--attributes`, `--enumerations`, `--enum-values`,
`--datatypes`, `--annotation-properties`, `--annotations`.

### -o, --output
Output ontology file. Required unless `--dry-run` is set.

---

## 2. Optional Model Parameters

### --datatypes
Path to Datatypes.tsv for named datatype definitions.

### -e, --enumerations
Path to Enumerations.tsv defining enumeration classes.

### -n, --enum-values
Path to EnumerationNamedValues.tsv defining enumeration individuals.

---

## 3. Annotation Parameters

### --annotation-properties
Path to AnnotationProperties.tsv.

### --annotations
Path to Annotations.tsv.

---

## 4. Namespace and Prefix Parameters

### --prefixes / --prefix
Declare one or more prefixes using comma- or semicolon-separated syntax. Each entry may use `=` or `:` between prefix and IRI:
```
--prefixes "iso=http://example/ns#;rdfs=http://www.w3.org/2000/01/rdf-schema#"
--prefix "iso:http://example/ns#,rdfs:http://www.w3.org/2000/01/rdf-schema#"
```

### --profile
Mapping profile to apply (`generic` or `iso20022`). Current behavior is a no-op placeholder; mapping is driven by TSV content.

---

## 5. Diagnostic and Behaviour Flags
### --strict
Promote validation warnings to errors.

### --no-validate / --validate
Toggle structural validation (default is enabled).

### --log-level
Set logging verbosity (`ERROR`, `WARNING`, `INFO`, `DEBUG`).

### --dry-run
Build the ontology graph without writing a file.

### --format
Serialisation format (`rdfxml`, `turtle`, `nt`, `jsonld`, `trig`, `n3`).

### --xml-base
Set `xml:base` when writing RDF/XML.

### --imports / --no-imports
Add `owl:imports` axioms or suppress automatic imports.

### --version
Print the tool version and exit.

---

## 6. Full Worked Examples

### Example: Minimal
```
uml2semantics -c Classes.tsv -a Attributes.tsv -o out.ttl -i http://example.org/ns
```

### Example: Complete ISO-style model
```
uml2semantics   -c tsv/Classes.tsv   -a tsv/Attributes.tsv   --datatypes tsv/Datatypes.tsv   -e tsv/Enumerations.tsv   -n tsv/EnumerationNamedValues.tsv   --annotation-properties tsv/AnnotationProperties.tsv   --annotations tsv/Annotations.tsv   -o build/iso-model.ttl   -p "iso:http://iso20022.example/ontology#,rdfs:http://www.w3.org/2000/01/rdf-schema#"   -i http://iso20022.example/ontology
```

### Example: Validation Only
```
uml2semantics -c C.tsv -a A.tsv --datatypes D.tsv --validate -o val.ttl -i http://validation/ns --dry-run
```

---

## 7. Summary Table

| Option | Description |
|--------|-------------|
| -c | Classes.tsv |
| -a | Attributes.tsv |
| --datatypes | Datatypes.tsv |
| -e | Enumerations.tsv |
| -n | EnumerationNamedValues.tsv |
| --annotation-properties | AnnotationProperties.tsv |
| --annotations | Annotations.tsv |
| -o | Output ontology file |
| -i | Base ontology IRI |
| --prefix / --prefixes | Prefix declarations |
| --profile | Mapping profile (generic/iso20022) |
| --imports / --no-imports | Imports control |
| --format | Output format |
| --xml-base | RDF/XML base |
| --strict | Strict validation |
| --validate / --no-validate | Toggle validation |
| --log-level | Logging verbosity |
| --dry-run | Build without writing |
| --version | Print version |
