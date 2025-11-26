from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class ConversionOptions:
    """All options controlling the conversion.

    This object is designed to be a superset of the options exposed in the
    0.8.2 command‑line interface so that scripts remain source‑compatible.
    """

    input_path: Path
    output_path: Optional[Path] = None
    output_format: str = "rdfxml"  # rdfxml | turtle | owlxml
    base_iri: str = "http://example.org/uml2semantics#"
    profile: str = "generic"  # generic | iso20022
    imports: List[str] = field(default_factory=list)
    auto_imports: bool = True
    validate: bool = True
    log_level: str = "INFO"
    dry_run: bool = False

    def normalised_format(self) -> str:
        fmt = self.output_format.lower()
        if fmt in {"rdf", "xml", "rdf/xml"}:
            return "application/rdf+xml"
        if fmt in {"ttl", "turtle"}:
            return "text/turtle"
        if fmt in {"owl", "owlxml", "owl/xml"}:
            return "application/owl+xml"
        return fmt
