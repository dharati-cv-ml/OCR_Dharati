"""Parse the documented synthetic SKU/LOT/EXP test payloads; NOT a GS1 parser.

GS1 production payloads must go through app.track_trace.parse_gs1.
"""
from __future__ import annotations
import re

KEY_MAP = {'SKU': 'product_code', 'LOT': 'batch', 'EXP': 'expiry'}

def parse_demo_payload(data: str) -> dict[str, str | None]:
    """Parse keys separated by : or ^, and fields separated by ; _ or |.

    Restrict to recognized keys and bounded alphanumerics to avoid arbitrary text
    being treated as a valid serialized code. Reject conflicting repeated fields.
    """
    if not isinstance(data, str) or len(data) > 1024:
        return {}
    matches = list(re.finditer(r'(?:^|[;_|\s])\s*(SKU|LOT|EXP)\s*[:^=]\s*([A-Za-z0-9-]{1,40})(?=$|[;_|\s])', data, re.I))
    found = {}
    for m in matches:
        field = KEY_MAP[m.group(1).upper()]
        value = m.group(2).upper()
        if field in found and found[field] != value:
            return {}
        found[field] = value
    if not found:
        return {}
    return found
