"""Bounded machine-local conversation serialization and storage."""

import json
import os
import re
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from ..core.findings import Finding, MAX_FINDINGS, finding_from_json

SCHEMA_VERSION = 2
MAX_MESSAGES = 200
MAX_MESSAGE_CHARS = 1_000_000
MAX_RECORD_BYTES = 8_000_000
_IDENTIFIER = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ConversationMessage:
    role: str
    body: str
    meta: str = ""
    evidence: tuple[int, ...] = ()
    unresolved_evidence: tuple[int, ...] = ()
    findings: tuple[Finding, ...] = ()


@dataclass(frozen=True)
class ConversationRecord:
    binary_id: str
    binary_name: str
    messages: tuple[ConversationMessage, ...]
    updated_at: str
    schema_version: int = SCHEMA_VERSION


def new_record(
    binary_id: str,
    binary_name: str,
    messages: tuple[ConversationMessage, ...],
) -> ConversationRecord:
    for message in messages:
        if len(message.body) > MAX_MESSAGE_CHARS:
            raise ValueError("Conversation message exceeds the local storage limit")
    return ConversationRecord(
        binary_id=binary_id,
        binary_name=binary_name,
        messages=messages[-MAX_MESSAGES:],
        updated_at=datetime.now(timezone.utc).isoformat(),
    )


def _validate_identifier(binary_id: str) -> None:
    if _IDENTIFIER.fullmatch(binary_id) is None:
        raise ValueError("Conversation binary identifier must be a SHA-256 hex digest")


def _message_from_json(value: object) -> ConversationMessage:
    if not isinstance(value, dict):
        raise ValueError("Conversation message must be an object")
    role = value.get("role", "")
    body = value.get("body", "")
    meta = value.get("meta", "")
    if not all(isinstance(item, str) for item in (role, body, meta)):
        raise ValueError("Conversation message text fields must be strings")
    if len(body) > MAX_MESSAGE_CHARS:
        raise ValueError("Conversation message exceeds the local storage limit")

    def addresses(key: str) -> tuple[int, ...]:
        raw = value.get(key, [])
        if not isinstance(raw, list) or not all(
            isinstance(address, int) and address >= 0 for address in raw
        ):
            raise ValueError(f"Conversation {key} must contain addresses")
        return tuple(raw)

    findings = value.get("findings", [])
    if not isinstance(findings, list) or len(findings) > MAX_FINDINGS:
        raise ValueError("Too many findings")
    return ConversationMessage(
        role=role,
        body=body,
        meta=meta,
        evidence=addresses("evidence"),
        unresolved_evidence=addresses("unresolved_evidence"),
        findings=tuple(finding_from_json(finding) for finding in findings),
    )


def record_from_json(payload: object) -> ConversationRecord:
    if not isinstance(payload, dict) or payload.get("schema_version") not in (1, SCHEMA_VERSION):
        raise ValueError("Unsupported conversation schema")
    binary_id = payload.get("binary_id", "")
    binary_name = payload.get("binary_name", "")
    updated_at = payload.get("updated_at", "")
    messages = payload.get("messages", [])
    if not all(isinstance(item, str) for item in (binary_id, binary_name, updated_at)):
        raise ValueError("Conversation metadata must be strings")
    _validate_identifier(binary_id)
    if not isinstance(messages, list) or len(messages) > MAX_MESSAGES:
        raise ValueError("Conversation contains too many messages")
    return ConversationRecord(
        binary_id=binary_id,
        binary_name=binary_name,
        updated_at=updated_at,
        messages=tuple(_message_from_json(message) for message in messages),
    )


def render_conversation_markdown(record: ConversationRecord) -> str:
    lines = [
        f"# Axio Analyst conversation - {record.binary_name}",
        "",
        f"Updated: {record.updated_at}",
        "",
    ]
    for message in record.messages:
        lines.extend([f"## {message.role}", ""])
        if message.meta:
            lines.extend([f"_{message.meta}_", ""])
        lines.extend([message.body, ""])
        if message.evidence:
            refs = ", ".join(f"0x{address:x}" for address in message.evidence)
            lines.extend([f"Evidence: {refs}", ""])
        if message.unresolved_evidence:
            refs = ", ".join(
                f"0x{address:x}" for address in message.unresolved_evidence
            )
            lines.extend([f"Unresolved addresses: {refs}", ""])
        for finding in message.findings:
            lines.extend(["### Finding (unverified)", "", finding.claim, "",
                          f"Context SHA-256: {finding.context_sha256}",
                          f"Analysis version: {finding.analysis_version}",
                          f"Provider/model: {finding.provider} / {finding.model}", "",
                          "Supplied context excerpt:", ""])
            lines.extend("> " + line for line in finding.context_excerpt.splitlines())
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


class ConversationStore:
    def __init__(self, directory: Path):
        self.directory = directory

    def _path(self, binary_id: str) -> Path:
        _validate_identifier(binary_id)
        return self.directory / f"{binary_id}.json"

    def load(self, binary_id: str) -> ConversationRecord | None:
        path = self._path(binary_id)
        if not path.exists():
            return None
        if path.stat().st_size > MAX_RECORD_BYTES:
            raise ValueError("Conversation file exceeds the local storage limit")
        payload = json.loads(path.read_text(encoding="utf-8"))
        record = record_from_json(payload)
        if record.binary_id != binary_id:
            raise ValueError("Conversation identifier does not match its filename")
        return record

    def save(self, record: ConversationRecord) -> None:
        _validate_identifier(record.binary_id)
        if record.schema_version != SCHEMA_VERSION:
            raise ValueError("Unsupported conversation schema")
        if len(record.messages) > MAX_MESSAGES:
            raise ValueError("Conversation contains too many messages")
        for message in record.messages:
            if len(message.body) > MAX_MESSAGE_CHARS:
                raise ValueError("Conversation message exceeds the local storage limit")
        self.directory.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            asdict(record),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ).encode("utf-8")
        if len(payload) > MAX_RECORD_BYTES:
            raise ValueError("Conversation exceeds the local storage limit")
        record_from_json(json.loads(payload))  # Validate findings on writes as well as reads.
        target = self._path(record.binary_id)
        temporary_name = ""
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=self.directory,
                prefix=f".{record.binary_id}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary.write(payload)
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_name = temporary.name
            try:
                os.chmod(temporary_name, 0o600)
            except OSError:
                pass
            os.replace(temporary_name, target)
        finally:
            if temporary_name and os.path.exists(temporary_name):
                os.unlink(temporary_name)

    def delete(self, binary_id: str) -> bool:
        path = self._path(binary_id)
        if not path.exists():
            return False
        path.unlink()
        return True

    @staticmethod
    def export_markdown(record: ConversationRecord, path: Path) -> None:
        path.write_text(render_conversation_markdown(record), encoding="utf-8")
