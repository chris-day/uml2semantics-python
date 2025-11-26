# Architecture overview

The core pipeline has three stages:

1. **Parse UML/XMI** – `UmlModel` and related helpers perform a lightweight
   read of the UML model (classes, properties, enumerations, generalisations).
2. **Semantic mapping** – `Uml2OwlConverter` translates UML constructs into
   OWL 2 axioms using RDFlib:
   - Classes → `owl:Class`
   - Associations → `owl:ObjectProperty`
   - Attributes → `owl:DatatypeProperty`
   - Enumerations → individuals plus `owl:oneOf`
   - Multiplicities → `owl:Restriction` with `owl:minCardinality`, `owl:maxCardinality`
   - Datatypes with facets → `owl:DatatypeRestriction` with `owl:onDatatype` and
     `owl:withRestrictions`
3. **Serialisation** – the final `rdflib.Graph` is serialised in the format
   requested on the command line (RDF/XML, Turtle, or OWL/XML).

Profiles (such as `iso20022`) are implemented as thin layers that configure IRIs,
naming conventions, and selected mapping rules.
