"""Prompt construction and request-boundary policy tests."""

import unittest

from tests import package_loader  # noqa: F401

from axio_analyst.core.models import FunctionContext
from axio_analyst.core.policy import truncate_text
from axio_analyst.core.prompts import build_prompt


class TestPromptConstruction(unittest.TestCase):
    def test_prompt_preserves_evidence_addresses(self):
        context = FunctionContext(
            binary_name="sample.exe",
            function_name="sub_401000",
            function_start=0x401000,
            architecture="x86_64",
            platform="windows-x86_64",
            function_type="int32_t ()",
            hlil="0x401000: return 1",
        )

        prompt = build_prompt(context, "What is returned?")

        self.assertIn("What is returned?", prompt)
        self.assertIn("0x401000: return 1", prompt)
        self.assertIn("Separate observed facts from inference", prompt)

    def test_truncate_text_marks_truncated_context(self):
        rendered, truncated = truncate_text("a" * 100, 50)

        self.assertTrue(truncated)
        self.assertEqual(len(rendered), 50)
        self.assertIn("truncated", rendered)

    def test_truncate_text_leaves_small_context_unchanged(self):
        rendered, truncated = truncate_text("short", 50)

        self.assertFalse(truncated)
        self.assertEqual(rendered, "short")
