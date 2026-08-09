"""Extract and classify provider-supplied address citations."""

import re
from collections.abc import Callable

_ADDRESS = re.compile(r"(?<![0-9A-Za-z_])0x[0-9a-fA-F]+")


def extract_evidence_addresses(text: str) -> tuple[int, ...]:
    seen: set[int] = set()
    addresses: list[int] = []
    for match in _ADDRESS.finditer(text):
        address = int(match.group(0), 16)
        if address not in seen:
            seen.add(address)
            addresses.append(address)
    return tuple(addresses)


def classify_evidence(
    text: str,
    is_valid: Callable[[int], bool],
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    valid: list[int] = []
    unresolved: list[int] = []
    for address in extract_evidence_addresses(text):
        (valid if is_valid(address) else unresolved).append(address)
    return tuple(valid), tuple(unresolved)
