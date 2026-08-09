"""Load and validate the plugin version from Binary Ninja metadata."""

import json
import re
from pathlib import Path

_SEMVER = re.compile(
    r"^(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


def read_version(metadata_path: Path | None = None) -> str:
    path = metadata_path or Path(__file__).resolve().parent.parent / "plugin.json"
    metadata = json.loads(path.read_text(encoding="utf-8"))
    version = metadata.get("version")
    if not isinstance(version, str) or _SEMVER.fullmatch(version) is None:
        raise RuntimeError(f"Invalid Axio Analyst semantic version in {path}")
    return version


VERSION = read_version()
