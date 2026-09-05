"""Bounded claims with reproducible context provenance, never verified conclusions."""
import hashlib
import json
from dataclasses import asdict, dataclass
from .evidence import extract_evidence_addresses
from .models import ContextBundle

SCHEMA_VERSION = 1
MAX_FINDINGS = 64

@dataclass(frozen=True)
class Finding:
    claim: str
    addresses: tuple[int, ...]
    context_excerpt: str
    context_sha256: str
    analysis_version: str
    provider: str
    model: str
    status: str = "unverified"
    schema_version: int = SCHEMA_VERSION

    def stale(self, context: ContextBundle) -> bool:
        return self.context_sha256 != context_digest(context)


def context_digest(context: ContextBundle) -> str:
    payload = json.dumps(asdict(context), sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_findings(text: str, context: ContextBundle, version: str, provider: str, model: str) -> tuple[Finding, ...]:
    digest = context_digest(context)
    sources = [context.primary.hlil, *(item.text for item in context.items)]
    findings = []
    for paragraph in text.split("\n\n"):
        addresses = extract_evidence_addresses(paragraph)
        if not addresses:
            continue
        # Preserve exact supplied lines, never manufacture evidence from a model's claim.
        lines = list(dict.fromkeys(line for source in sources for line in source.splitlines()
                    if set(extract_evidence_addresses(line)).intersection(addresses)))
        findings.append(Finding(paragraph[:16000], addresses[:256], "\n".join(lines)[:8000], digest,
                                version, provider, model))
        if len(findings) == MAX_FINDINGS:
            break
    return tuple(findings)


def finding_from_json(value: object) -> Finding:
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported finding schema")
    fields = ("claim", "context_excerpt", "context_sha256", "analysis_version", "provider", "model")
    if not all(isinstance(value.get(k), str) for k in fields):
        raise ValueError("Invalid finding metadata")
    if len(value["claim"]) > 16000 or len(value["context_excerpt"]) > 8000:
        raise ValueError("Finding exceeds context limits")
    digest = value["context_sha256"]
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("Invalid finding context digest")
    addresses = value.get("addresses")
    if not isinstance(addresses, list) or len(addresses) > 256 or any(type(a) is not int or a < 0 for a in addresses):
        raise ValueError("Invalid finding addresses")
    if value.get("status") != "unverified":
        raise ValueError("Imported findings cannot assert verified status")
    return Finding(**{k: value[k] for k in fields}, addresses=tuple(addresses))
