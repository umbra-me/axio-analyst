"""Markdown sanitization and scroll restoration tests."""

import unittest

from tests import package_loader  # noqa: F401

from axio_analyst.ui.markdown import restored_scroll_value, sanitize_markdown


class TestMarkdownRendering(unittest.TestCase):
    def test_sanitize_preserves_markdown_and_code_punctuation(self):
        source = "**bold** <img src=x> & text\n\n```c\nif (a > b && c < d)\n```"

        self.assertEqual(sanitize_markdown(source), source)

    def test_sanitize_removes_nul_and_control_characters(self):
        self.assertEqual(sanitize_markdown("before\x00after"), "beforeafter")
        self.assertEqual(sanitize_markdown("bell\x07escape\x1b"), "bellescape")

    def test_sanitize_keeps_newlines_and_tabs(self):
        self.assertEqual(sanitize_markdown("a\n\tb"), "a\n\tb")

    def test_live_tail_follows_when_reader_is_at_bottom(self):
        self.assertEqual(restored_scroll_value(100, 100, 140), 140)

    def test_live_tail_preserves_reader_scroll_position(self):
        self.assertEqual(restored_scroll_value(40, 100, 140), 40)

    def test_forced_scroll_moves_new_message_into_view(self):
        self.assertEqual(restored_scroll_value(40, 100, 140, True), 140)
