# uml2semantics (Python)

CLI/library to convert UML-style TSV specifications into an OWL 2 ontology using rdflib.

## Features

- UML-style **Classes** and **Attributes / Associations** from TSV
- **Enumerations** and **enumeration individuals**
- **Named datatypes** with XSD facets (pattern, min/max length, inclusive/exclusive bounds)
- ISO-style **Choice patterns** (union + disjoint classes)
- **Exact cardinality** emission (`n..n -> owl:cardinality n`)
- TSV-driven **annotation properties** and annotation assertions
- Worked examples for ISO 4217 currency codes, LEI, BIC
- Example ontology in **Turtle** and **Manchester OWL** renderings

The package includes:

- `examples/` – ready-to-run TSVs, PlantUML architecture, and sample OWL ontologies
- `docs/tutorial.md` – tutorial-style walkthrough
- `docs/uml2semantics-architecture.md` – docs page embedding the PlantUML diagram

---

## Command line usage

```bash
uml2semantics   -c examples/Classes.tsv   -a examples/Attributes.tsv   --datatypes examples/Datatypes.tsv   -e examples/Enumerations.tsv   -n examples/EnumerationNamedValues.tsv   --annotation-properties examples/AnnotationProperties.tsv   --annotations examples/Annotations.tsv   -o out.ttl   -p "iso:http://iso20022.example/ontology#,rdfs:http://www.w3.org/2000/01/rdf-schema#,skos:http://www.w3.org/2004/02/skos/core#"   -i "http://iso20022.example/ontology"
```

See `docs/tutorial.md` for a full walkthrough and `examples/example-ontology.ttl` / `examples/example-ontology.manchester.owl` for the output.
