# Changelog

## 0.9.15

- Implemented Choice semantics over **attributes**: `ChoiceOf` is now interpreted as a list of attribute names on the class, not class names.
- For attributes participating in a Choice that have no explicit multiplicity, defaulted their restriction to `min 0`, `max 1`.
- Choice classes now become subclasses of a union of the corresponding attribute restrictions
  (e.g. `(Proprietary exactly 1 GenericIdentification30) or (Code exactly 1 AcknowledgementReason7Code)`).
- Preserved qualified cardinality restrictions with `owl:onClass` / `owl:onDataRange` so Protégé does not fall back to `owl:Thing` / `rdfs:Literal`.
- Retained OWL 2 datatype facet support and the TSV validation rules for required `Name` fields.
