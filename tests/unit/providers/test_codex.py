"""Codex CLI adapter tests."""

import unittest

from tests import package_loader  # noqa: F401

from axio_analyst.core.models import ProviderConfig, ProviderError
from axio_analyst.providers import CodexCliProvider
from axio_analyst.providers.codex import codex_stream_delta, parse_codex_output
from axio_analyst.providers.streaming import JsonLineStream


class TestCodexCliProvider(unittest.TestCase):
    def setUp(self):
        self.config = ProviderConfig(
            backend="codex-cli",
            executable="codex",
            model="gpt-5.6-sol",
            timeout_seconds=30,
            reasoning_effort="xhigh",
        )

    def test_command_is_ephemeral_read_only_and_uses_stdin(self):
        command = CodexCliProvider(self.config).command()

        self.assertEqual(command[:2], ["codex", "exec"])
        self.assertIn("--json", command)
        self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
        self.assertIn("--ephemeral", command)
        self.assertIn("--ignore-user-config", command)
        self.assertIn("--ignore-rules", command)
        self.assertEqual(command[command.index("--model") + 1], "gpt-5.6-sol")
        self.assertIn('model_reasoning_effort="xhigh"', command)
        self.assertEqual(command[-1], "-")

    def test_parse_codex_jsonl_uses_final_agent_message(self):
        text = parse_codex_output(
            '{"type":"thread.started","thread_id":"test"}\n'
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"First draft"}}\n'
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"Final analysis"}}\n'
            '{"type":"turn.completed"}\n'
        )

        self.assertEqual(text, "Final analysis")

    def test_parse_codex_jsonl_requires_agent_message(self):
        with self.assertRaises(ProviderError):
            parse_codex_output('{"type":"turn.completed"}\n')

    def test_codex_stream_emits_completed_agent_message(self):
        chunks = []
        stream = JsonLineStream(codex_stream_delta, chunks.append)
        stream.feed(
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"Final **analysis**"}}\n'
        )

        self.assertEqual(chunks, ["Final **analysis**"])
