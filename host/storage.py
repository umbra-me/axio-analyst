"""Binary identity and machine-local conversation storage location."""

import hashlib
from pathlib import Path

from binaryninja import BinaryView, user_directory

from ..application.conversations import ConversationStore


def binary_fingerprint(bv: BinaryView) -> str:
    """Build a path-free content fingerprint from bounded BinaryView samples."""
    start = int(getattr(bv, "start", 0))
    end = int(getattr(bv, "end", start))
    length = max(0, end - start)
    digest = hashlib.sha256()
    digest.update(length.to_bytes(8, "big", signed=False))
    sample_size = 65536
    offsets = {
        start,
        start + max(0, length // 2 - sample_size // 2),
        start + max(0, length - sample_size),
    }
    for offset in sorted(offsets):
        digest.update(offset.to_bytes(8, "big", signed=False))
        remaining = max(0, end - offset)
        digest.update(bytes(bv.read(offset, min(sample_size, remaining))))
    return digest.hexdigest()


def conversation_store() -> ConversationStore:
    directory = user_directory()
    if not directory:
        raise OSError("Binary Ninja did not provide a user directory")
    return ConversationStore(Path(directory) / "axio-analyst" / "conversations")
