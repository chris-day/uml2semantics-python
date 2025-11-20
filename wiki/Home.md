# uml2semantics – Wiki Home

Welcome to the **uml2semantics** project wiki.

This project converts UML-style TSV specifications into **OWL 2 ontologies**, supporting:

- UML-style Classes & Attributes  
- ISO 20022-style **Choice patterns** (union + disjoint)  
- XSD datatype facets (pattern, min/max length, numeric bounds)  
- Enumerations & enumeration individuals  
- Annotation properties and annotation assertions  
- Reusable named datatypes  
- A CLI with golden regression tests and examples  

```mermaid
graph TD
  A[TSV Inputs] --> B[uml2semantics CLI]
  B --> C[OWL 2 Ontology]
  B --> D[Reasoner / Tools (Protege, SHACL, etc.)]
```

---

## Wiki Contents

1. [[Getting-Started]]  
2. [[TSV-Specification]]  
3. [[Choice-Patterns]]  
4. [[Datatypes-and-Facets]]  
5. [[Enumerations]]  
6. [[Annotations]]  
7. [[CLI-Usage]]  
8. [[Architecture]]  
9. [[Examples]]  
10. [[Golden-Tests]]  
