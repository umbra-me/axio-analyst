"""Repository layout, metadata, and development installer contracts."""

import ast
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.package_loader import REPO_ROOT
from tools.runtime_manifest import (
    OBSOLETE_RUNTIME_FILES,
    RUNTIME_FILES,
    RUNTIME_PACKAGE_ROOTS,
)

from axio_analyst import __version__


class TestRepositoryContract(unittest.TestCase):
    @staticmethod
    def _imports(path: Path) -> list[str]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        return imports

    def test_plugin_metadata_uses_product_name_and_version(self):
        metadata = json.loads((REPO_ROOT / "plugin.json").read_text(encoding="utf-8"))

        self.assertEqual(metadata["name"], "Axio Analyst")
        self.assertEqual(metadata["version"], __version__)
        self.assertIsNotNone(
            re.fullmatch(
                r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
                r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?",
                __version__,
            )
        )
        self.assertIn("ui", metadata["type"])

    def test_sidebar_icon_uses_axio_initials(self):
        sidebar = (REPO_ROOT / "ui" / "sidebar.py").read_text(encoding="utf-8")

        self.assertIn('            "AX",', sidebar)

    def test_version_is_visible_in_binary_ninja_surfaces(self):
        sidebar_view = (REPO_ROOT / "ui" / "sidebar_view.py").read_text(
            encoding="utf-8"
        )
        settings_page = (REPO_ROOT / "ui" / "settings_page.py").read_text(
            encoding="utf-8"
        )
        registration = (REPO_ROOT / "host" / "registration.py").read_text(
            encoding="utf-8"
        )

        self.assertIn('QtWidgets.QLabel(f"v{VERSION}")', sidebar_view)
        self.assertIn("header.addWidget(self.version_label)", sidebar_view)
        self.assertIn('f"Axio Analyst v{VERSION}.', settings_page)
        self.assertIn('"Axio Analyst\\\\About Axio Analyst"', registration)

    def test_runtime_manifest_covers_all_runtime_modules(self):
        expected = {"__init__.py", "plugin.json"}
        for package_name in RUNTIME_PACKAGE_ROOTS:
            package = REPO_ROOT / package_name
            expected.update(
                path.relative_to(REPO_ROOT).as_posix()
                for path in package.rglob("*.py")
            )

        self.assertEqual(set(RUNTIME_FILES), expected)

    def test_root_contains_only_the_plugin_entry_module(self):
        root_modules = {path.name for path in REPO_ROOT.glob("*.py")}

        self.assertEqual(root_modules, {"__init__.py"})

    def test_core_and_application_keep_external_boundaries_out(self):
        forbidden = ("binaryninja", "PySide6", "subprocess", "urllib")
        for package_name in ("core", "application"):
            for path in (REPO_ROOT / package_name).rglob("*.py"):
                self.assertFalse(
                    any(
                        name.startswith(forbidden)
                        for name in self._imports(path)
                    ),
                    f"{path.relative_to(REPO_ROOT)} crosses a core boundary",
                )

    def test_providers_remain_binary_ninja_and_qt_independent(self):
        forbidden = ("binaryninja", "binaryninjaui", "PySide6")
        for path in (REPO_ROOT / "providers").rglob("*.py"):
            self.assertFalse(
                any(name.startswith(forbidden) for name in self._imports(path)),
                f"{path.relative_to(REPO_ROOT)} imports a host or UI module",
            )

    def test_development_installer_copies_a_current_runtime(self):
        tool = REPO_ROOT / "tools" / "plugin_dev.py"
        with tempfile.TemporaryDirectory() as directory:
            plugins_dir = Path(directory) / "plugins"
            install = subprocess.run(
                [
                    sys.executable,
                    str(tool),
                    "install",
                    "--plugins-dir",
                    str(plugins_dir),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            current = subprocess.run(
                [
                    sys.executable,
                    str(tool),
                    "status",
                    "--plugins-dir",
                    str(plugins_dir),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(install.returncode, 0, install.stderr)
        self.assertEqual(current.returncode, 0, current.stderr)
        self.assertIn("Axio Analyst is current", current.stdout)

    def test_development_installer_prunes_only_known_flat_modules(self):
        tool = REPO_ROOT / "tools" / "plugin_dev.py"
        with tempfile.TemporaryDirectory() as directory:
            plugins_dir = Path(directory) / "plugins"
            target = plugins_dir / "axio_analyst"
            target.mkdir(parents=True)
            for name in OBSOLETE_RUNTIME_FILES:
                (target / name).write_text("obsolete", encoding="utf-8")
            preserved = target / "README.md"
            preserved.write_text("keep", encoding="utf-8")

            install = subprocess.run(
                [
                    sys.executable,
                    str(tool),
                    "install",
                    "--plugins-dir",
                    str(plugins_dir),
                    "--prune-obsolete",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            remaining = [name for name in OBSOLETE_RUNTIME_FILES if (target / name).exists()]
            preserved_text = preserved.read_text(encoding="utf-8")

        self.assertEqual(install.returncode, 0, install.stderr)
        self.assertEqual(remaining, [])
        self.assertEqual(preserved_text, "keep")
        self.assertIn("remove obsolete:", install.stdout)
