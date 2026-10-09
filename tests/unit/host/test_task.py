"""Background-task cancellation/comparison tests without the Binary Ninja GUI."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tests import package_loader  # noqa: F401
from tests.host_fakes import load_host_module, module
from axio_analyst.core.models import ContextBundle, ContextItem, FunctionContext, ProviderCancelled, ProviderConfig, ProviderError, ProviderResult


class TestAnalysisTask(unittest.TestCase):
    def setUp(self):
        self.primary = ProviderConfig("ollama-cloud", "ollama", "test:cloud", 30)
        self.secondary = ProviderConfig("codex-cli", "codex", "test", 30)
        self.config = SimpleNamespace(provider=self.primary, max_context_chars=1000)
        self.function = SimpleNamespace(name="test", start=0x1000)
        primary = FunctionContext("demo", "test", 0x1000, "test", "test", "int test()", "0x1000: test")
        self.context = ContextBundle(primary, (ContextItem("current-function", "test", primary.hlil),), 1000)
        stubs = {
            "axio_analyst.host.settings": module("axio_analyst.host.settings", RuntimeConfig=object,
                BACKEND_LABELS={"ollama-cloud": "Ollama Cloud", "codex-cli": "Codex"}),
            "axio_analyst.host.context": module("axio_analyst.host.context", render_context_bundle=lambda *_args, **_kwargs: self.context),
        }
        self.tasks = load_host_module("host.task", stubs)

    def task(self):
        return self.tasks.AnalyzeFunctionTask(
            object(), self.function, "question", self.config, show_report=False,
            comparison_provider=self.secondary, on_complete=Mock(), on_cancelled=Mock(), on_error=Mock(),
        )

    def test_secondary_cancellation_preserves_completed_primary(self):
        task = self.task()
        primary = ProviderResult("observed", self.primary.backend, self.primary.model)
        with patch.object(self.tasks, "create_provider", return_value=object()), \
                patch.object(self.tasks, "analyze", side_effect=[primary, ProviderCancelled("stopped")]):
            task.run()
        task.on_complete.assert_called_once()
        results = task.on_complete.call_args.args[1]
        self.assertIs(results[0], primary)
        self.assertTrue(results[1].cancelled)
        task.on_cancelled.assert_not_called()

    def test_cancellation_between_providers_does_not_dispatch_secondary(self):
        task = self.task()
        def primary(*_args, **_kwargs):
            task.cancel()
            return ProviderResult("complete", self.primary.backend)
        with patch.object(self.tasks, "create_provider", return_value=object()), \
                patch.object(self.tasks, "analyze", side_effect=primary) as analyze:
            task.run()
        analyze.assert_called_once()
        results = task.on_complete.call_args.args[1]
        self.assertEqual(results[0].text, "complete")
        self.assertTrue(results[1].cancelled)

    def test_primary_cancellation_retains_existing_cancel_path(self):
        task = self.task()
        with patch.object(self.tasks, "create_provider", return_value=object()), \
                patch.object(self.tasks, "analyze", side_effect=ProviderCancelled("stopped")):
            task.run()
        task.on_cancelled.assert_called_once()
        task.on_complete.assert_not_called()
        task.on_error.assert_not_called()

    def test_comparison_failure_preserves_primary_and_shared_snapshot(self):
        task = self.task()
        with patch.object(self.tasks, "create_provider", return_value=object()), \
                patch.object(self.tasks, "analyze", side_effect=[
                    ProviderResult("complete", self.primary.backend), ProviderError("unavailable")
                ]) as analyze:
            task.run()
        results = task.on_complete.call_args.args[1]
        self.assertEqual(results[1].error, "unavailable")
        self.assertFalse(results[1].cancelled)
        self.assertTrue(all(call.args[0] is self.context for call in analyze.call_args_list))

    def test_preview_cancellation_does_not_emit_error_or_completion(self):
        complete, error = Mock(), Mock()
        preview = self.tasks.ContextPreviewTask(
            object(), self.function, 1000, self.tasks.ContextOptions(), None, complete, error
        )
        preview.cancel()
        with patch.object(self.tasks, "render_context_bundle", side_effect=ProviderCancelled("stopped")):
            preview.run()
        complete.assert_not_called()
        error.assert_not_called()

    def test_cancellation_during_collection_prevents_provider_dispatch(self):
        task = self.task()
        with patch.object(self.tasks, "render_context_bundle", side_effect=ProviderCancelled("stopped")), \
                patch.object(self.tasks, "create_provider") as create:
            task.run()
        create.assert_not_called()
        task.on_cancelled.assert_called_once()
