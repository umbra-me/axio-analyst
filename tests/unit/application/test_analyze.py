"""Analysis use-case tests."""

import unittest

from tests import package_loader  # noqa: F401

from axio_analyst.application import analyze
from axio_analyst.core.models import FunctionContext, ProviderResult
from axio_analyst.core.provider import Provider


class RecordingProvider(Provider):
    def __init__(self):
        self.prompt = ""

    def complete(self, prompt, is_cancelled=None, on_stream=None):
        self.prompt = prompt
        return ProviderResult(text="done", backend="probe")


class TestAnalyze(unittest.TestCase):
    def test_builds_prompt_and_delegates_to_injected_provider(self):
        provider = RecordingProvider()
        starts = []
        context = FunctionContext(
            binary_name="sample.exe",
            function_name="main",
            function_start=0x1000,
            architecture="x86_64",
            platform="windows-x86_64",
            function_type="int32_t ()",
            hlil="0x1000: return 0",
        )

        result = analyze(
            context,
            "What is returned?",
            provider,
            on_provider_start=lambda: starts.append(True),
        )

        self.assertEqual(result.text, "done")
        self.assertEqual(starts, [True])
        self.assertIn("What is returned?", provider.prompt)
        self.assertIn("0x1000: return 0", provider.prompt)
        self.assertEqual(result.usage.input_chars, len(provider.prompt))
        self.assertEqual(result.usage.output_chars, len("done"))
        self.assertGreaterEqual(result.usage.duration_seconds, 0)


class TestDeterministicStreaming(unittest.TestCase):
    def test_streaming_and_cancellation_use_the_same_frozen_prompt(self):
        from axio_analyst.core.models import ProviderCancelled
        context = FunctionContext("fixture", "main", 0x1000, "x86_64", "test", "int()", "0x1000: return 0")
        class Fixture(Provider):
            def complete(self, prompt, is_cancelled=None, on_stream=None):
                for chunk in ("At ", "0x1000", " returns zero."):
                    if is_cancelled and is_cancelled(): raise ProviderCancelled("cancelled")
                    if on_stream: on_stream(chunk)
                return ProviderResult("At 0x1000 returns zero.", "fixture")
        chunks = []
        result = analyze(context, "Explain", Fixture(), on_stream=chunks.append)
        self.assertEqual("".join(chunks), result.text)
        chunks = []
        with self.assertRaises(ProviderCancelled):
            analyze(context, "Explain", Fixture(), is_cancelled=lambda: len(chunks) == 1, on_stream=chunks.append)
        self.assertEqual(chunks, ["At "])
