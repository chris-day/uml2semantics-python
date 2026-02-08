# Getting Started

Welcome to **uml2semantics** — a deterministic TSV-to-OWL 2 transformation system designed for semantic modelling, FAIR data engineering, and ISO-style metadata-driven pipelines.

This Getting Started guide provides a full onboarding workflow covering installation, project structure, input preparation, execution, and ontology validation.

---

# 1. Installation

## 1.1. Install from source
In your project directory:
```
pip install .
```

## 1.2. Install globally (editable mode)
```
pip install -e .
```

## 1.3. Verify installation
```
uml2semantics --help
```

You should see the full CLI help, including all parameters, prefixes, diagnostics, and example usage.

---

# 2. Directory Layout

A recommended project layout is:

```
project/
  tsv/
    Classes.tsv
    Attributes.tsv
    Datatypes.tsv
    Enumerations.tsv
    EnumerationNamedValues.tsv
    AnnotationProperties.tsv
    Annotations.tsv
  out/
  docs/
```

This structure aligns with large-scale ISO-style models, enabling you to separate controlled inputs from generated outputs and documentation.

---

# 3. Preparing the TSV Inputs

uml2semantics relies entirely on TSV inputs representing UML elements and semantic constraints.

## 3.1. Classes.tsv
Contains:
- Class CURIE
- Human-readable name
- Parent classes
- Definition
- Optional ISO-style ChoiceOf and ChoiceSemantics

## 3.2. Attributes.tsv
Defines:
- Datatype and object properties
- Multiplicity rules
- XSD facets (pattern, length, numeric bounds)
- Inline datatype restrictions

## 3.3. Datatypes.tsv
Defines named datatypes, e.g. LEI20, BIC11, CurrencyCode.

## 3.4. Enumerations
Two files:
- Enumerations.tsv – enumeration class
- EnumerationNamedValues.tsv – individuals

## 3.5. Annotations
Two files:
- AnnotationProperties.tsv – annotation IRIs
- Annotations.tsv – annotation assertions

---

# 4. Minimal Example Run

Generate a basic ontology:

```
uml2semantics   -c tsv/Classes.tsv   -a tsv/Attributes.tsv   -o out/ontology.ttl   -i http://example.org/ontology
```

Result:  
`out/ontology.ttl` in Turtle format.

---

# 5. Full Example Run (all TSVs)

```
uml2semantics   -c tsv/Classes.tsv   -a tsv/Attributes.tsv   --datatypes tsv/Datatypes.tsv   --enumerations tsv/Enumerations.tsv   --enum-values tsv/EnumerationNamedValues.tsv   --annotation-properties tsv/AnnotationProperties.tsv   --annotations tsv/Annotations.tsv   -o out/model.ttl   -p "iso:http://example.org/ns#,rdfs:http://www.w3.org/2000/01/rdf-schema#,skos:http://www.w3.org/2004/02/skos/core#}"   -i http://example.org/ns
```

This produces a fully structured OWL ontology including:
- Named datatypes
- Enumeration classes + individuals
- Annotation properties
- Annotation assertions
- ISO-style choice patterns
- XSD facet restrictions

---

# 6. Validating the Output

Load the ontology into **Protege**:
1. Open Protege
2. Select: File → Open
3. Choose `model.ttl`
4. Verify:
   - Class hierarchy
   - Property hierarchy
   - Datatype restrictions
   - Choice (union + disjoint) axioms
   - Annotation assertions

(Optional) Enable a reasoner such as **ELK** or **HermiT** to confirm structural consistency.

---

# 7. Typical Workflow in Practice

1. Define your UML model in tabular TSV format.
2. Apply choice rules, multiplicities, datatypes, and enumerations.
3. Generate OWL using `uml2semantics`.
4. Validate in Protege.
5. Run SHACL validation externally (optional).
6. Commit TSVs and ontology under version control.
7. Use golden tests to ensure deterministic builds.

This workflow supports FAIR modelling, ISO-compatible structures, and reproducible semantic engineering.

---

# 8. Next Steps

Now continue to:
- [[TSV-Specification]] for a detailed schema definition  
- [[CLI-Usage]] for full command-line reference  
- [[Examples]] for sample TSV sets and outputs

Return to [[Home]].
