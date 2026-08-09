"""Supervised provider-process integration tests."""

import sys
import time
import unittest

from tests import package_loader  # noqa: F401

from axio_analyst.core.models import ProviderCancelled, ProviderConfig
from axio_analyst.providers.process import CliProvider


class TestStreamingProcess(unittest.TestCase):
    @staticmethod
    def _provider(script):
        class ProbeProvider(CliProvider):
            @property
            def display_name(self):
                return "Probe"

            def command(self):
                return [sys.executable, "-c", script]

            def complete(self, prompt, is_cancelled=None, on_stream=None):
                raise NotImplementedError

        return ProbeProvider(
            ProviderConfig(
                backend="probe",
                executable=sys.executable,
                model="",
                timeout_seconds=10,
            )
        )

    def test_cli_reader_streams_stdout_while_draining_stderr(self):
        provider = self._provider(
            "import sys; "
            "sys.stdin.buffer.read(); "
            "sys.stdout.buffer.write(b'first '); sys.stdout.flush(); "
            "sys.stderr.buffer.write(b'diagnostic'); sys.stderr.flush(); "
            "sys.stdout.buffer.write(b'second'); sys.stdout.flush()"
        )
        chunks = []

        output = provider.run_cli("input", None, on_stdout=chunks.append)

        self.assertEqual(output, "first second")
        self.assertEqual("".join(chunks), "first second")

    def test_cli_reader_cancels_sleeping_process(self):
        provider = self._provider(
            "import sys,time; sys.stdin.buffer.read(); time.sleep(5)"
        )
        started = time.monotonic()

        with self.assertRaises(ProviderCancelled):
            provider.run_cli(
                "input",
                lambda: time.monotonic() - started > 0.05,
            )
