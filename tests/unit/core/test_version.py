"""Plugin version source and validation tests."""

import tempfile
import unittest
from pathlib import Path

from tests import package_loader  # noqa: F401

from axio_analyst.core.version import VERSION, read_version


class TestVersion(unittest.TestCase):
    def test_current_version_comes_from_plugin_metadata(self):
        self.assertEqual(VERSION, read_version())

    def test_invalid_semantic_version_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            metadata = Path(directory) / "plugin.json"
            metadata.write_text('{"version":"release-eight"}', encoding="utf-8")

            with self.assertRaises(RuntimeError):
                read_version(metadata)
