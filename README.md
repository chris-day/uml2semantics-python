# uml2semantics-python

Convert UML-style TSV models into OWL 2 ontologies, including classes, properties,
enumerations, datatype facets, choice patterns, annotations, and property chains.
The current CLI consumes TSV files; the profile option is a placeholder.

[Documentation](https://chris-day.github.io/uml2semantics-python/) ·
[Examples](docs/Examples.md) · [Changelog](CHANGELOG.md) · [Apache-2.0 license](LICENSE)

## Install and run

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
uml2semantics --help
python -m pytest
```

Example TSV and OWL files that were previously distributed with the repository
are now local-only. Supply those files before running examples that use them.

See [Getting started](docs/Getting-Started.md) for conversion commands and
[documentation maintenance](docs/Documentation.md) for Zensical setup, preview,
build, verification, and deployment instructions.

## Attribution

This work builds on Henriette Harmse's
[UML-to-OWL reference](https://henrietteharmse.com/uml-vs-owl/uml-class-diagram-to-owl-and-sroiq-reference/)
and [reference implementation](https://github.com/henrietteharmse/uml2semantics).
