"""Codex CLI adapter tests."""

import json
import unittest

from tests import package_loader  # noqa: F401

from axio_analyst.core.models import ProviderConfig, ProviderError
from axio_analyst.providers import CodexCliProvider
from axio_analyst.providers.codex import (
    codex_stream_delta,
    parse_codex_output,
    parse_codex_response,
)
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
        disabled = [command[index + 1] for index, value in enumerate(command) if value == "--disable"]
        self.assertEqual(disabled, ["shell_tool", "view_image"])
        self.assertIn('web_search="disabled"', command)
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

    def test_parse_codex_usage(self):
        text, usage = parse_codex_response(
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"done"}}\n'
            '{"type":"turn.completed","usage":{"input_tokens":20,'
            '"cached_input_tokens":8,"output_tokens":6}}\n'
        )

        self.assertEqual(text, "done")
        self.assertEqual(usage.input_tokens, 20)
        self.assertEqual(usage.cached_input_tokens, 8)
        self.assertEqual(usage.output_tokens, 6)

    def test_failed_turn_wins_over_partial_message(self):
        for error in ("failed", {"message": "failed"}, {}, None):
            with self.subTest(error=error), self.assertRaises(ProviderError):
                parse_codex_response("\n".join(json.dumps(event) for event in (
                    {"type": "item.completed", "item": {"type": "agent_message", "text": "draft"}},
                    {"type": "turn.failed", "error": error},
                )))

    def test_error_wins_even_with_completion_event(self):
        with self.assertRaisesRegex(ProviderError, "failed"):
            parse_codex_response(
                '{"type":"error","message":"failed"}\n'
                '{"type":"item.completed","item":{"type":"agent_message","text":"draft"}}\n'
                '{"type":"turn.completed"}\n'
            )

    def test_missing_completion_is_not_success(self):
        with self.assertRaisesRegex(ProviderError, "completed turn"):
            parse_codex_response(
                '{"type":"item.completed","item":{"type":"agent_message","text":"draft"}}\n'
            )

    def test_non_object_events_and_malformed_usage_are_safe(self):
        text, usage = parse_codex_response(
            '[]\nnull\n42\n'
            '{"type":"item.completed","item":{"type":"agent_message","text":"done"}}\n'
            '{"type":"turn.completed","usage":{"input_tokens":true,"output_tokens":-1,"cached_input_tokens":"4"}}\n'
        )
        self.assertEqual(text, "done")
        self.assertIsNone(usage.input_tokens)
        self.assertIsNone(usage.output_tokens)
        self.assertIsNone(usage.cached_input_tokens)

    def test_invalid_json_and_control_only_messages_fail(self):
        for response in ("not-json", '{"type":"item.completed","item":{"type":"agent_message","text":"\\u001b[31m"}}\n{"type":"turn.completed"}'):
            with self.subTest(response=response), self.assertRaises(ProviderError):
                parse_codex_response(response)
