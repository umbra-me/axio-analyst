"""Optional native Qt regression tests; opt in with AXIO_QT_TESTS=1."""

import os
import unittest
from unittest.mock import patch

from tests import package_loader  # noqa: F401


@unittest.skipUnless(os.environ.get("AXIO_QT_TESTS") == "1", "native Qt tests require explicit opt-in")
class TestNativeTranscript(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6 import QtWidgets
        from axio_analyst.ui.transcript import Transcript
        cls.QtWidgets = QtWidgets
        cls.Transcript = Transcript
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        self.browser = self.QtWidgets.QTextBrowser()
        self.transcript = self.Transcript(self.browser)

    def tearDown(self):
        self.browser.deleteLater()
        self.app.processEvents()

    def test_many_chunks_do_not_rebuild_markdown_and_stay_before_footer(self):
        self.transcript.start_response("model-footer")
        with patch.object(self.transcript, "render", wraps=self.transcript.render) as render:
            for _ in range(256):
                self.assertTrue(self.transcript.stream("part🙂\n"))
            render.assert_not_called()
        text = self.browser.toPlainText()
        self.assertEqual(text.count("part🙂"), 256)
        self.assertNotIn("Receiving response", text)
        self.assertTrue(text.endswith("model-footer"))
        self.assertEqual(self.transcript.snapshot()[0].body, "part🙂\n" * 256)

    def test_live_preview_cap_keeps_complete_text_for_snapshot_and_cancellation(self):
        source = "0123456789abcdef"
        self.transcript.start_response("footer")
        with patch("axio_analyst.ui.transcript.MAX_LIVE_RESPONSE_CHARS", 8):
            self.transcript.stream(source)
            preview = self.browser.toPlainText()
            self.assertIn("01234567", preview)
            self.assertNotIn("89abcdef", preview)
            self.assertIn("Live preview limited", preview)
            self.transcript.stream("more")
            self.assertEqual(self.browser.toPlainText(), preview)
        self.assertEqual(self.transcript.snapshot()[0].body, source + "more")
        self.transcript.cancel()
        self.assertIn(source + "more", self.browser.toPlainText())
        self.assertNotIn("Live preview limited", self.browser.toPlainText())

    def test_near_limit_chunk_stream_keeps_a_bounded_preview_and_exact_snapshot(self):
        self.transcript.start_response("footer")
        with patch("axio_analyst.ui.transcript.MAX_LIVE_RESPONSE_CHARS", 16), \
                patch.object(self.transcript, "render", wraps=self.transcript.render) as render:
            for _ in range(15_625):
                self.transcript.stream("x" * 512)
            render.assert_not_called()
        self.assertLess(len(self.browser.toPlainText()), 200)
        self.assertEqual(self.transcript.messages[0].body, "")
        self.assertEqual(self.transcript.snapshot()[0].body, "x" * 8_000_000)
        self.transcript.complete("Canonical response", "usage")
        self.assertEqual(self.transcript.snapshot()[0].body, "Canonical response")

    def test_html_and_incomplete_markdown_are_literal_until_completion(self):
        self.transcript.start_response("footer")
        source = "**bold** <img src=x onerror=bad()> <script>bad()</script>"
        self.transcript.stream(source)
        self.assertIn(source, self.browser.toPlainText())
        self.transcript.complete(source, "footer")
        self.assertIn("<img src=x onerror=bad()>", self.browser.toPlainText())
        self.assertIn("<script>bad()</script>", self.browser.toPlainText())
        self.assertNotIn("<img src=\"x\"", self.browser.toHtml())

    def test_completion_replaces_stream_with_canonical_result_once(self):
        self.transcript.start_response("footer")
        self.transcript.stream("draft")
        with patch.object(self.transcript, "render", wraps=self.transcript.render) as render:
            self.transcript.complete("**Canonical answer**", "usage")
            render.assert_called_once()
        self.assertNotIn("draft", self.browser.toPlainText())
        self.assertIn("Canonical answer", self.browser.toPlainText())
        self.assertFalse(self.transcript.stream("late"))

    def test_cancel_and_failure_keep_partial_text_and_reject_late_stream(self):
        for terminal in ("cancel", "fail"):
            with self.subTest(terminal=terminal):
                self.transcript.reset()
                self.transcript.start_response("footer")
                self.transcript.stream("partial")
                with patch.object(self.transcript, "render", wraps=self.transcript.render) as render:
                    if terminal == "cancel":
                        self.transcript.cancel()
                    else:
                        self.transcript.fail("diagnostic")
                    render.assert_called_once()
                self.assertIn("partial", self.browser.toPlainText())
                self.assertFalse(self.transcript.stream("late"))

    def test_reset_discards_stream_range_and_old_content(self):
        self.transcript.start_response("footer")
        self.transcript.stream("old")
        self.transcript.reset()
        self.assertFalse(self.transcript.stream("late"))
        self.assertEqual(self.browser.toPlainText(), "")
        self.transcript.start_response("new-footer")
        self.transcript.stream("new")
        self.assertNotIn("old", self.browser.toPlainText())
        self.assertTrue(self.browser.toPlainText().endswith("new-footer"))

    def test_stream_filters_controls_without_escaping_code(self):
        self.transcript.start_response("footer")
        self.transcript.stream("a\x00")
        self.transcript.stream("< > &&\x07\n\tb")
        self.assertIn("a< > &&\n\tb", self.browser.toPlainText())
        self.assertNotIn("\x00", self.browser.toPlainText())
        self.assertNotIn("&lt;", self.browser.toPlainText())

    def test_completion_without_active_response_renders_once(self):
        with patch.object(self.transcript, "render", wraps=self.transcript.render) as render:
            self.transcript.complete("answer", "usage")
            render.assert_called_once()
        self.assertEqual(len(self.transcript.messages), 1)
