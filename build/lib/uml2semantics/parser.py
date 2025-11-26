from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from .model import UmlModel, UmlClass, UmlProperty


class UmlParser:
    """Very lightweight UML/XMI parser.

    This is deliberately minimal and intended as a placeholder for the real
    parsing logic from the original uml2semantics project. It focuses on
    extracting enough structure to exercise the OWL 2 mapping end‑to‑end.
    """

    def parse(self, path: Path) -> UmlModel:
        tree = ET.parse(path)
        root = tree.getroot()

        model = UmlModel()

        # This logic is intentionally simplistic and should be replaced by
        # a proper UML/XMI parser aligned with the upstream project.
        for pack in root.findall(".//packagedElement"):
            name = pack.get("name")
            if not name:
                continue
            uml_class = model.get_or_create_class(name)

        return model
