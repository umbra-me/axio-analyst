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
