"""Context budgeting, rendering, and evidence tests."""

import unittest

from tests import package_loader  # noqa: F401

from axio_analyst.core.evidence import classify_evidence, extract_evidence_addresses
from axio_analyst.core.models import ContextItem, FunctionContext
from axio_analyst.core.policy import build_context_bundle
from axio_analyst.core.prompts import build_prompt, render_context


def primary() -> FunctionContext:
    return FunctionContext(
        binary_name="sample.exe",
        function_name="main",
        function_start=0x1000,
        architecture="x86_64",
        platform="windows-x86_64",
        function_type="int32_t ()",
        hlil="0x1000: return 0",
    )


class TestContextBundle(unittest.TestCase):
    def test_budget_is_stable_deduplicated_and_bounded(self):
        current = ContextItem("current-function", "Current", "a" * 40, 0x1000)
        duplicate = ContextItem("current-function", "Duplicate", "a" * 40, 0x1000)
        caller = ContextItem("caller", "Caller", "b" * 40, 0x2000)

        bundle = build_context_bundle(primary(), [current, duplicate, caller], 60)

        self.assertEqual([item.kind for item in bundle.items], ["current-function", "caller"])
        self.assertLessEqual(bundle.total_chars, 60)
        self.assertTrue(bundle.truncated)

    def test_rendered_prompt_discloses_every_context_item(self):
        bundle = build_context_bundle(
            primary(),
            [
                ContextItem("current-function", "Current main", "0x1000: return 0", 0x1000),
                ContextItem("string", "Referenced string", "hello", 0x3000),
            ],
            1000,
        )

        rendered = render_context(bundle)
        prompt = build_prompt(bundle, "What is returned?")

        self.assertIn("## Current main at 0x1000", rendered)
        self.assertIn("## Referenced string at 0x3000", rendered)
        self.assertIn("Context items: 2", prompt)
        self.assertIn("What is returned?", prompt)

    def test_evidence_is_unique_ordered_and_classified(self):
        text = "Observed at 0x1000, inferred from 0x2000 and 0x1000."

        self.assertEqual(extract_evidence_addresses(text), (0x1000, 0x2000))
        self.assertEqual(
            classify_evidence(text, lambda address: address == 0x1000),
            ((0x1000,), (0x2000,)),
        )
