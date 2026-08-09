"""Install or compare a development copy of Axio Analyst."""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
TARGET_NAME = "axio_analyst"
RUNTIME_FILES = (
    "__init__.py",
    "models.py",
    "plugin.json",
    "prompts.py",
    "providers.py",
    "registration.py",
    "rendering.py",
    "settings.py",
    "settings_page.py",
    "sidebar.py",
    "task.py",
)


def target_directory(plugins_dir: Path) -> Path:
    return plugins_dir.resolve() / TARGET_NAME


def compare(target: Path) -> tuple[list[str], list[str]]:
    missing: list[str] = []
    changed: list[str] = []
    for name in RUNTIME_FILES:
        destination = target / name
        if not destination.is_file():
            missing.append(name)
        elif not filecmp.cmp(ROOT / name, destination, shallow=False):
            changed.append(name)
    return missing, changed


def status(plugins_dir: Path) -> int:
    target = target_directory(plugins_dir)
    missing, changed = compare(target)
    if not missing and not changed:
        print(f"Axio Analyst is current: {target}")
        return 0
    print(f"Axio Analyst differs: {target}")
    if missing:
        print("  missing: " + ", ".join(missing))
    if changed:
        print("  changed: " + ", ".join(changed))
    return 1


def install(plugins_dir: Path, dry_run: bool) -> int:
    target = target_directory(plugins_dir)
    for name in RUNTIME_FILES:
        source = ROOT / name
        destination = target / name
        print(f"{source} -> {destination}")
        if not dry_run:
            target.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
    if dry_run:
        print("Dry run complete; no files changed.")
        return 0
    return status(plugins_dir)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install or compare the Axio Analyst runtime files."
    )
    parser.add_argument("action", choices=("status", "install"))
    parser.add_argument(
        "--plugins-dir",
        type=Path,
        required=True,
        help="Binary Ninja user plugins directory",
    )
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.action == "status":
        if args.dry_run:
            raise SystemExit("--dry-run is valid only with install")
        return status(args.plugins_dir)
    return install(args.plugins_dir, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
