"""Request and preview identity tests of the actual sidebar controller."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from tests import package_loader  # noqa: F401
from tests.host_fakes import BackgroundTask, QObject, load_host_module, module
from axio_analyst.application.conversations import ConversationMessage
from axio_analyst.core.models import ContextBundle, ContextItem, FunctionContext, ProviderConfig, ProviderResult


class TestSidebarCallbacks(unittest.TestCase):
    def setUp(self):
        provider = ProviderConfig("ollama-cloud", "ollama", "test:cloud", 30)
        self.config = SimpleNamespace(provider=provider, persist_conversations=True, max_context_chars=1000)
        settings = module(
            "axio_analyst.host.settings", BACKEND_LABELS={"ollama-cloud": "Ollama Cloud"},
            RuntimeConfig=object, get_runtime_config=lambda: self.config,
            get_provider_config=lambda _backend: provider,
        )
        stubs = {
            "binaryninjaui": module("binaryninjaui", **{key: object for key in (
                "Sidebar", "SidebarWidget", "SidebarWidgetLocation", "SidebarWidgetType", "UIContext", "ViewFrame"
            )}),
            "PySide6": module("PySide6", QtCore=SimpleNamespace(QObject=QObject, QUrl=object),
                             QtWidgets=SimpleNamespace()),
            "axio_analyst.host.settings": settings,
            "axio_analyst.host.model_discovery": module("axio_analyst.host.model_discovery", OllamaModelDiscovery=object),
            "axio_analyst.host.storage": module("axio_analyst.host.storage",
                binary_fingerprint=lambda bv: bv.identity, conversation_store=lambda: None),
            "axio_analyst.host.task": module("axio_analyst.host.task",
                AnalyzeFunctionTask=BackgroundTask, ContextPreviewTask=BackgroundTask),
            "axio_analyst.ui.progress": module("axio_analyst.ui.progress", RequestProgress=object),
            "axio_analyst.ui.sidebar_view": module("axio_analyst.ui.sidebar_view", SidebarView=object),
            "axio_analyst.ui.transcript": module("axio_analyst.ui.transcript", Transcript=object),
            "axio_analyst.ui.branding": module("axio_analyst.ui.branding"),
        }
        sidebar = load_host_module("ui.sidebar", stubs)
        self.controller = object.__new__(sidebar.AxioAnalystSidebar)
        self.a = SimpleNamespace(identity="a" * 64, file=SimpleNamespace(filename="/path/a.bin"),
                                 is_valid_offset=lambda addr: 0x1000 <= addr < 0x2000)
        self.b = SimpleNamespace(identity="b" * 64, file=SimpleNamespace(filename="/path/b.bin"),
                                 is_valid_offset=lambda addr: 0x3000 <= addr < 0x4000)
        self.controller.bv = self.a
        self.controller.frame = None
        self.controller._current_function = None
        self.controller._alive = True
        self.controller._request_generation = 1
        self.controller._preview_generation = 1
        self.controller._task = BackgroundTask()
        self.controller._preview_task = None
        self.controller._binary_id = self.a.identity
        self.controller.view = Mock()
        self.controller.request_progress = Mock()
        self.controller.model_discovery = Mock()
        self.controller.conversation = Mock()
        self.controller.conversation.snapshot.return_value = (ConversationMessage("You", "question"),)
        self.controller._conversation_store = Mock()
        self.controller._conversation_store.load.return_value = None
        self.controller._update_actions = Mock()
        self.controller._refresh_scope = Mock()
        self.controller._refresh_backend_label = Mock()
        primary = FunctionContext("a.bin", "a", 0x1000, "test", "test", "int a()", "0x1000: A-only context")
        self.context = ContextBundle(primary, (ContextItem("current-function", "A", primary.hlil, 0x1000),), 1000)
        self.result = ProviderResult("Observed at 0x1000.", "ollama-cloud", "test:cloud")

    def test_current_result_uses_originating_binary_and_validates_addresses(self):
        callback = self.controller._request_callback(self.controller._analysis_complete)
        callback(self.context, (self.result,))
        record = self.controller._conversation_store.save.call_args.args[0]
        self.assertEqual(record.binary_id, self.a.identity)
        self.assertEqual(record.binary_name, "a.bin")
        args = self.controller.conversation.complete.call_args.args
        self.assertEqual(args[2], (0x1000,))
        self.assertEqual(args[3], ())
        self.assertIsNone(self.controller._task)

    def test_restored_citations_are_revalidated_instead_of_trusting_stored_flags(self):
        stored = ConversationMessage(
            "Axio Analyst", "Observed at 0x1000 and 0x3000.",
            evidence=(0x3000,), unresolved_evidence=(0x1000,),
        )
        self.controller._conversation_store.load.return_value = SimpleNamespace(messages=(stored,))
        self.controller._load_transcript()
        restored, = self.controller.conversation.load.call_args.args[0]
        self.assertEqual(restored.evidence, (0x1000,))
        self.assertEqual(restored.unresolved_evidence, (0x3000,))

    def test_generic_and_malformed_links_cannot_navigate(self):
        navigator = Mock()
        self.controller.frame = SimpleNamespace(
            getCurrentViewInterface=lambda: SimpleNamespace(navigate=navigator),
        )
        for scheme, host, path in (
            ("https", "address", "/1000"),
            ("file", "", "/1000"),
            ("axio", "other", "/1000"),
            ("axio", "address", "/not-hex"),
            ("axio", "address", "/3000"),
        ):
            with self.subTest(scheme=scheme, host=host, path=path):
                url = SimpleNamespace(scheme=lambda: scheme, host=lambda: host, path=lambda: path)
                self.controller._navigate_evidence(url)
        navigator.assert_not_called()

    def test_navigation_rechecks_the_active_binary_after_a_switch(self):
        navigator = Mock()
        self.controller.frame = SimpleNamespace(
            getCurrentViewInterface=lambda: SimpleNamespace(navigate=navigator),
        )
        old_url = SimpleNamespace(scheme=lambda: "axio", host=lambda: "address", path=lambda: "/1000")
        self.controller._navigate_evidence(old_url)
        navigator.assert_called_once_with(0x1000)
        navigator.reset_mock()
        self.controller._replace_binary_view(self.b)
        self.controller._navigate_evidence(old_url)
        navigator.assert_not_called()
        new_url = SimpleNamespace(scheme=lambda: "axio", host=lambda: "address", path=lambda: "/3000")
        self.controller._navigate_evidence(new_url)
        navigator.assert_called_once_with(0x3000)

    def test_old_result_cannot_complete_or_persist_after_view_change(self):
        old_task = self.controller._task
        callback = self.controller._request_callback(self.controller._analysis_complete)
        self.controller._replace_binary_view(self.b)
        callback(self.context, (self.result,))
        self.assertTrue(old_task.cancelled)
        self.assertEqual(self.controller._binary_id, self.b.identity)
        self.controller.conversation.complete.assert_not_called()
        self.controller._conversation_store.save.assert_not_called()

    def test_every_queued_callback_rejects_old_generation_and_binary(self):
        for role in ("stream", "progress", "context", "error", "cancelled", "complete"):
            with self.subTest(role=role):
                target = Mock()
                callback = self.controller._request_callback(target)
                self.controller._request_generation += 1
                self.controller._task = BackgroundTask()
                callback("late")
                target.assert_not_called()
        target = Mock()
        callback = self.controller._request_callback(target)
        self.controller.bv = self.b
        callback("late")
        target.assert_not_called()

    def test_terminal_callback_cannot_be_delivered_twice(self):
        target = Mock(side_effect=lambda: setattr(self.controller, "_task", None))
        callback = self.controller._request_callback(target)
        callback()
        callback()
        target.assert_called_once()

    def test_late_preview_cannot_clear_newer_preview_task(self):
        old_task = BackgroundTask()
        self.controller._preview_task = old_task
        old = self.controller._preview_callback(self.controller._context_ready)
        self.controller._invalidate_context_preview()
        newer_task = BackgroundTask()
        self.controller._preview_task = newer_task
        current = self.controller._preview_callback(self.controller._context_ready)
        old(self.context)
        self.assertIs(self.controller._preview_task, newer_task)
        self.assertTrue(old_task.cancelled)
        current(self.context)
        self.assertIsNone(self.controller._preview_task)
        self.assertIn("A-only context", self.controller.view.set_context_snapshot.call_args.args[1])

    def test_settings_apply_invalidates_pending_preview(self):
        task = BackgroundTask()
        self.controller._preview_task = task
        callback = self.controller._preview_callback(self.controller._context_ready)
        self.controller._settings_applied()
        callback(self.context)
        self.assertTrue(task.cancelled)
        self.assertEqual(self.controller.view.set_context_snapshot.call_args.args, ("Preview not built", ""))

    def test_settings_apply_refreshes_discovery_with_the_applied_executable(self):
        self.controller.view.settings_page.selected_backend.return_value = "ollama-cloud"
        self.controller.view.settings_page.selected_ollama_executable.return_value = "changed-ollama"
        self.controller._settings_applied()
        self.controller.model_discovery.refresh.assert_called_once_with("changed-ollama")

    def test_closed_sidebar_rejects_all_late_work(self):
        target = Mock()
        callback = self.controller._request_callback(target)
        self.controller._mark_dead()
        callback("late")
        target.assert_not_called()
        self.assertTrue(self.controller._task.cancelled)

    def test_absent_view_detaches_request_and_clears_binary(self):
        callback = self.controller._request_callback(self.controller._analysis_complete)
        self.controller._refresh_from_frame()
        callback(self.context, (self.result,))
        self.assertIsNone(self.controller.bv)
        self.assertEqual(self.controller._binary_id, "")
        self.controller._conversation_store.save.assert_not_called()

    def test_partial_comparison_cancellation_keeps_primary_findings_and_usage(self):
        cancelled = ProviderResult("", "codex-cli", error="Request cancelled.", cancelled=True)
        callback = self.controller._request_callback(self.controller._analysis_complete)
        callback(self.context, (self.result, cancelled))
        args = self.controller.conversation.complete.call_args.args
        self.assertIn("Observed at 0x1000.", args[0])
        self.assertIn("Request cancelled", args[0])
        self.assertEqual(len(args[4]), 1)
        self.assertIn("Ollama Cloud:", args[1])
        self.assertIn("Comparison cancelled", self.controller.request_progress.finish.call_args.args[0])
