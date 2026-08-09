"""Markdown sanitization and scroll restoration tests."""

import unittest

from tests import package_loader  # noqa: F401

from axio_analyst.ui.markdown import restored_scroll_value, safe_markdown


class TestMarkdownRendering(unittest.TestCase):
    def test_safe_markdown_preserves_formatting_and_escapes_html(self):
        rendered = safe_markdown("**bold** <img src=x> & text")

        self.assertEqual(rendered, "**bold** &lt;img src=x&gt; &amp; text")

    def test_safe_markdown_removes_nul(self):
        self.assertEqual(safe_markdown("before\x00after"), "beforeafter")

    def test_live_tail_follows_when_reader_is_at_bottom(self):
        self.assertEqual(restored_scroll_value(100, 100, 140), 140)

    def test_live_tail_preserves_reader_scroll_position(self):
        self.assertEqual(restored_scroll_value(40, 100, 140), 40)

    def test_forced_scroll_moves_new_message_into_view(self):
        self.assertEqual(restored_scroll_value(40, 100, 140, True), 140)
