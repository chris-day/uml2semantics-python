# uml2semantics-python Documentation

## Overview

`uml2semantics-python` turns UML export TSVs into OWL 2 ontologies.

The current focus is on:

- Datatype modelling with OWL 2 `owl:DatatypeRestriction`
- Clean separation of classes, datatypes, and enumeration/code-list values
- A small, hackable Python codebase you can evolve alongside the Java tooling

## Getting Started

```bash
pip install .
uml2semantics --help
```

Then supply TSV files:

```bash
uml2semantics   --classes class.tsv   --attributes attribute.tsv   --datatypes datatypes.tsv   --enumerations enumerations.tsv   --out iso20022.owl
```
