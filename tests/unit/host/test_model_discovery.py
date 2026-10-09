"""Bounded discovery and late-result tests without a live provider or Qt loop."""

import threading
import unittest
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch

from tests import package_loader  # noqa: F401
from tests.host_fakes import QObject, Signal, load_host_module, module
from tests.integration import test_cli_process


class TestModelDiscovery(unittest.TestCase):
    def setUp(self):
        self.module = load_host_module("host.model_discovery", {
            "PySide6": module("PySide6", QtCore=SimpleNamespace(QObject=QObject, Signal=Signal)),
        })
        self.discovery = self.module.OllamaModelDiscovery(None)
        self.discovery.busyChanged = Signal()
        self.discovery.modelsReady = Signal()
        self.discovery.statusChanged = Signal()
        self.discovery._generation = 1

    def test_refresh_is_async_and_same_executable_refresh_is_ignored_while_busy(self):
        with patch.object(self.module.threading, "Thread") as thread:
            self.discovery.refresh("first")
            self.discovery.refresh("first")
        thread.assert_called_once()
        thread.return_value.start.assert_called_once()
        self.assertTrue(self.discovery.busy)
        self.assertEqual(self.discovery._executable, "first")

    def test_new_executable_cancels_old_discovery_and_rejects_its_fallback(self):
        with patch.object(self.module.threading, "Thread") as thread:
            self.discovery.refresh("old")
            old_generation = self.discovery._generation
            old_cancelled = self.discovery._cancelled
            self.discovery.refresh("new")
            self.discovery._catalog_finished(old_generation, [], "offline")
            self.assertEqual(thread.call_count, 2)
            self.discovery._catalog_finished(self.discovery._generation, [], "offline")
            self.assertEqual(thread.call_count, 3)
            self.assertEqual(thread.call_args.kwargs["args"][1], "new")
        self.assertTrue(old_cancelled.is_set())
        self.assertEqual(self.discovery._executable, "new")
        self.assertFalse(self.discovery._cancelled.is_set())

    def test_fallback_uses_shared_runner_timeout_output_cap_and_empty_stdin(self):
        self.discovery._registered_loading = True
        with patch.object(self.module._OllamaListProvider, "run_cli", autospec=True,
                          return_value="NAME ID SIZE\nmodel:cloud id size\n") as run:
            self.discovery._fetch_registered_models(1, "ollama", threading.Event(), "offline")
        provider, prompt, cancelled = run.call_args.args
        self.assertEqual(provider.command(), ["ollama", "list"])
        self.assertEqual(provider.config.timeout_seconds, 10)
        self.assertEqual(prompt, "")
        self.assertFalse(cancelled())
        self.assertEqual(run.call_args.kwargs["max_output_bytes"], 1_000_000)
        self.assertEqual(self.discovery.modelsReady.values, [(["model:cloud"],)])
        self.assertFalse(self.discovery.busy)

    def test_late_catalog_and_list_results_are_ignored(self):
        with patch.object(self.module.threading, "Thread") as thread:
            self.discovery._catalog_finished(0, [], "offline")
            self.discovery._registered_models_finished(0, ["old:cloud"], "", "offline")
        thread.assert_not_called()
        self.assertEqual(self.discovery.modelsReady.values, [])

    def test_close_cancels_fallback_and_ignores_queued_completion(self):
        self.discovery._registered_loading = True
        cancelled = self.discovery._cancelled
        self.discovery.close()
        self.assertFalse(self.discovery.busy)
        self.assertTrue(cancelled.is_set())
        self.discovery._registered_models_finished(1, ["old:cloud"], "", "")
        self.assertEqual(self.discovery.modelsReady.values, [])

    def test_real_harmless_hung_fallback_resets_busy(self):
        provider = test_cli_process.TestStreamingProcess._provider("import time; time.sleep(10)")
        provider.config = replace(provider.config, timeout_seconds=0.1)
        self.discovery._registered_loading = True
        with patch.object(self.module, "_OllamaListProvider", return_value=provider):
            self.discovery._fetch_registered_models(1, "synthetic", threading.Event(), "offline")
        self.assertFalse(self.discovery.busy)
        self.assertIn("timed out", self.discovery.statusChanged.values[-1][0])

    def test_real_harmless_noisy_fallback_resets_busy(self):
        provider = test_cli_process.TestStreamingProcess._provider(
            "import sys; sys.stdout.buffer.write(b'x' * 1_100_000)"
        )
        self.discovery._registered_loading = True
        with patch.object(self.module, "_OllamaListProvider", return_value=provider):
            self.discovery._fetch_registered_models(1, "synthetic", threading.Event(), "offline")
        self.assertFalse(self.discovery.busy)
        self.assertIn("output safety limit", self.discovery.statusChanged.values[-1][0])
