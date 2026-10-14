"""Authoritative allowlist for the loadable Binary Ninja plugin."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

RUNTIME_PACKAGE_ROOTS = ("application", "core", "host", "providers", "ui")

OBSOLETE_RUNTIME_FILES = (
    "models.py",
    "prompts.py",
    "providers.py",
    "registration.py",
    "rendering.py",
    "settings.py",
    "settings_page.py",
    "sidebar.py",
    "task.py",
)

RUNTIME_FILES = (
    "__init__.py",
    "plugin.json",
    "application/__init__.py",
    "application/analyze.py",
    "application/conversations.py",
    "core/__init__.py",
    "core/evidence.py",
    "core/findings.py",
    "core/models.py",
    "core/policy.py",
    "core/prompts.py",
    "core/provider.py",
    "core/usage.py",
    "core/version.py",
    "host/__init__.py",
    "host/context.py",
    "host/model_discovery.py",
    "host/registration.py",
    "host/settings.py",
    "host/storage.py",
    "host/task.py",
    "providers/__init__.py",
    "providers/claude.py",
    "providers/codex.py",
    "providers/ollama.py",
    "providers/process.py",
    "providers/process_tree.py",
    "providers/streaming.py",
    "ui/__init__.py",
    "ui/branding.py",
    "ui/markdown.py",
    "ui/progress.py",
    "ui/settings_page.py",
    "ui/sidebar.py",
    "ui/sidebar_view.py",
    "ui/transcript.py",
)


def check(root: Path) -> list[str]:
    """Return manifest errors without importing any host-only modules."""
    errors = [f"missing runtime file: {name}" for name in RUNTIME_FILES if not (root / name).is_file()]
    errors.extend(
        f"obsolete runtime file remains: {name}"
        for name in OBSOLETE_RUNTIME_FILES
        if (root / name).exists()
    )
    try:
        json.loads((root / "plugin.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid plugin.json: {exc}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="validate the runtime file allowlist")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = check(Path(__file__).resolve().parents[1])
    if errors:
        for error in errors:
            print(error)
        return 1
    print(f"runtime manifest: {len(RUNTIME_FILES)} files present; metadata valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
