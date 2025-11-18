import csv
from pathlib import Path
from typing import Dict, List


def read_tsv(path: str | None) -> List[Dict[str, str]]:
    """Read a TSV file into a list of dicts, normalising headers and trimming values.
    Empty or None path -> empty list.
    """
    if not path:
        return []

    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"TSV file not found: {path}")

    rows: List[Dict[str, str]] = []
    with p.open(newline="", encoding="utf-8") as f:
        sample = f.read(4096)
        f.seek(0)

        try:
            dialect = csv.Sniffer().sniff(sample, delimiters="\t")
        except csv.Error:
            class Dialect(csv.Dialect):
                delimiter = "\t"
                quotechar = '"'
                escapechar = None
                doublequote = True
                skipinitialspace = False
                lineterminator = "\n"
                quoting = csv.QUOTE_MINIMAL
            dialect = Dialect()

        f.seek(0)

        reader = csv.DictReader(f, dialect=dialect)
        for row in reader:
            if not row:
                continue
            clean = {(k or "").strip(): (v or "").strip()
                     for k, v in row.items()
                     if k is not None}
            if any(v for v in clean.values()):
                rows.append(clean)

    return rows
