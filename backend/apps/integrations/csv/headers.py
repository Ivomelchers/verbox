"""CSV-header extractie (gedeeld door detectie en parsers)."""

import csv
import io
import re


def normalize_header(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip().lower())


def detect_delimiter(content: str) -> str:
    sample = content[:2048]
    return ";" if sample.count(";") > sample.count(",") else ","


def strip_metadata_header_lines(content: str) -> str:
    """Verwijder leidende account-metadata regels (bv. "UID: 123,Company Name: ").

    Sommige exchange-exports (Bybit, OKX) zetten vóór de echte kolomkoppen
    één of meer regels met accountinfo. Die regels hebben meer ':' dan ','
    en worden daarom als ruis herkend en overgeslagen.
    """
    lines = content.split("\n")
    start = 0
    for line in lines:
        if line.strip() and line.count(":") > line.count(","):
            start += 1
        else:
            break
    return "\n".join(lines[start:]) if start else content


def read_csv_headers(content: str) -> tuple[set[str], str, list[str]]:
    """Genormaliseerde headers, delimiter en originele veldnamen."""
    if not content.strip():
        raise ValueError("CSV-bestand is leeg.")

    cleaned = strip_metadata_header_lines(content)
    delimiter = detect_delimiter(cleaned)
    reader = csv.DictReader(io.StringIO(cleaned), delimiter=delimiter)
    if not reader.fieldnames:
        raise ValueError("CSV heeft geen kolomkoppen.")

    original = [name for name in reader.fieldnames if name]
    normalized = {normalize_header(name) for name in original}
    return normalized, delimiter, original
