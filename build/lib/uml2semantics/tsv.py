import csv
from pathlib import Path
from typing import Dict, List


def read_tsv(path: str | None) -> List[Dict[str, str]]:
    if not path:
        return []

    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"TSV file not found: {path}")

    rows: List[Dict[str, str]] = []
    with p.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            if not row:
                continue
            clean = {(k or "").strip(): (v or "").strip()
                     for k, v in row.items()
                     if k is not None}
            if any(v for v in clean.values()):
                rows.append(clean)
    return rows
