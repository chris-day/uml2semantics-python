# Troubleshooting – Errors and Warnings You May See

This page lists **actual errors and warnings** raised by the current
`uml2semantics-python` codebase and how to fix them.

---

# 1. CLI Errors (Argument Parsing)

These errors are reported by the CLI and exit with a non-zero status.

## Missing ontology IRI

```
Missing required --ontology-iri value.
```

Fix:
- Provide `--ontology-iri` (or `-i`) with a valid IRI.

## No input TSVs provided

```
No input TSVs provided. Supply at least one of --classes, --attributes,
--enumerations, --enum-values, --datatypes, --annotation-properties, or --annotations.
```

Fix:
- Pass at least one TSV input file.

## Missing output when not using --dry-run

```
Missing required --output value (or use --dry-run).
```

Fix:
- Provide `--output` (or `-o`) or use `--dry-run`.

---

# 2. TSV Parsing Errors (Load-Time)

These are raised while reading TSVs.

## Class missing Name

```
Class with CURIE '<curie>' is missing a Name; TSV Name must be populated for all classes.
```

Fix:
- Ensure **Classes.tsv** has a Name for every row.

## Enumeration missing Name

```
Enumeration with CURIE '<curie>' is missing a Name; TSV Name must be populated for all enumerations.
```

Fix:
- Ensure **Enumerations.tsv** has a Name for every row.

## Attribute missing Name

```
Attribute for class '<class>' with CURIE '<curie>' is missing a Name; TSV Name must be populated for all attributes.
```

Fix:
- Ensure **Attributes.tsv** has a Name for every row.

---

# 3. Model Validation Errors (Build-Time)

These are raised during ontology build (unless `--no-validate` is used).

## Missing identifiers

```
Validation failed: <Kind> is missing both CURIE and Name
```

Fix:
- Provide at least one of **Curie** or **Name** for classes, enumerations,
  datatypes, attributes, and annotation properties.

## Duplicate identifiers

```
Validation failed: Duplicate <Kind> identifier '<id>'
```

Fix:
- Ensure identifiers are unique across each TSV category.

## Invalid multiplicities

```
Validation failed: Attribute '<name>' has min_cardinality < 0
Validation failed: Attribute '<name>' has min_cardinality > max_cardinality
```

Fix:
- Use non-negative multiplicities and ensure min ≤ max.

## Missing attribute type

```
Validation failed: Attribute '<attr>' on '<class>' is missing ClassEnumOrPrimitiveType
```

Fix:
- Populate **ClassEnumOrPrimitiveType** (or the legacy
  **ClassEnumOrPrimativeType**) in **Attributes.tsv**.

## Unknown attribute type

```
Validation failed: Unknown ClassEnumOrPrimitiveType '<token>' for attribute '<attr>' on class '<class>'.
```

Fix:
- Ensure the type token resolves to a class, enumeration, named datatype, or
  an `xsd:` primitive.

## Datatype facets without BaseDatatype

```
Datatype '<name or curie>' has facet constraints but no BaseDatatype; populate BaseDatatype in Datatypes.tsv to avoid defaulting to xsd:string.
```

Fix:
- If any facet columns are set in **Datatypes.tsv**, populate **BaseDatatype**.

---

# 4. Warnings (Logged at INFO/WARNING)

These do not stop execution unless `--strict` is set.

## Missing prefixes

```
Validation warnings (prefix): <prefixes>
```

Fix:
- Add the missing prefix declarations via `--prefix` or `--prefixes`.

## Unresolved choice members

```
Choice member '<token>' on class '<class>' not found as class or attribute
```

Fix:
- Ensure **ChoiceOf** values reference existing class tokens or attribute
  tokens on the choice class.

## Unrecognized ChoiceSemantics

```
ChoiceSemantics '<value>' on class '<class>' is not recognized
```

Fix:
- Use `exclusive`, `inclusive`, or leave blank.

## Missing CURIE fallbacks

```
<Class|Enumeration|Datatype|AnnotationProperty> '<name>' is missing a CURIE; falling back to Name for identifier
```

Fix:
- Prefer explicit CURIEs to keep stable IRIs across builds.

---

# 5. Tips for Diagnosing Issues

- Run with `--log-level DEBUG` to see detailed processing logs.
- Use `--dry-run` to validate without writing output.
- Keep prefix declarations explicit so CURIE resolution is predictable.

---

# 6. Navigation

- Return to [[Home]]
- Go to [[CLI-Usage]]
- Go to [[TSV-Specification]]
