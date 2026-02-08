# Golden Tests – Current Behavior and Suggested Expansion

This document explains the **current test coverage** for `uml2semantics-python`
related to golden outputs, and outlines a realistic path to expand it.

---

# 1. Current Golden-Style Coverage

The current repository contains a lightweight golden-style test in
`tests/test_golden.py` that:

- runs the CLI against the `examples/` TSV bundle
- parses the generated Turtle
- asserts the ontology IRI exists
- asserts the graph is non-empty
- asserts at least one `owl:Class` and one `owl:AnnotationProperty` exist

This confirms the end-to-end pipeline works and produces a valid RDF graph,
but it does **not** compare full outputs against a canonical `expected.ttl`.

---

# 2. What Is Not Implemented Yet

The following golden-test features are **not** present in the codebase today:

- canonical Turtle normalisation
- deterministic blank-node ordering
- full file-to-file diffs between `expected.ttl` and actual output
- a suite of per-feature golden cases

---

# 3. Recommended Expansion (If Desired)

If you want true golden regression testing, a practical next step is:

1. Create a `tests/golden/` directory with per-case TSV bundles.
2. Generate `expected.ttl` once per case.
3. Add a normalisation step (or accept stable `rdflib` output with sorted
   triples).
4. Diff actual output against `expected.ttl` in the test.

This would allow detection of changes in:

- choice semantics
- datatype facets
- enumeration individuals
- annotations
- prefix handling

---

# 4. Navigation

- Return to [[Home]]
- Go to [[Examples]]
- Go to [[CLI-Usage]]
