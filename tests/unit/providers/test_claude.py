"""Claude Code adapter tests."""

import unittest

from tests import package_loader  # noqa: F401

from axio_analyst.core.models import ProviderConfig, ProviderError
from axio_analyst.providers import ClaudeCodeProvider
from axio_analyst.providers.claude import (
    claude_stream_delta,
    parse_claude_output,
)
from axio_analyst.providers.streaming import JsonLineStream


class TestClaudeCodeProvider(unittest.TestCase):
    def setUp(self):
        self.config = ProviderConfig(
            backend="claude-code",
            executable="claude",
            model="sonnet",
            timeout_seconds=30,
            reasoning_effort="high",
        )

    def test_command_is_noninteractive_and_read_only(self):
        command = ClaudeCodeProvider(self.config).command()

        self.assertIn("-p", command)
        self.assertEqual(command[command.index("--output-format") + 1], "stream-json")
        self.assertIn("--include-partial-messages", command)
        self.assertIn("--safe-mode", command)
        self.assertIn("--no-session-persistence", command)
        self.assertIn("--tools", command)
        self.assertEqual(command[command.index("--tools") + 1], "")
        self.assertEqual(command[command.index("--model") + 1], "sonnet")
        self.assertEqual(command[command.index("--effort") + 1], "high")

    def test_prompt_is_not_part_of_command_line(self):
        command = ClaudeCodeProvider(self.config).command()

        self.assertNotIn("sensitive decompiler text", command)

    def test_parse_claude_json(self):
        text, model = parse_claude_output(
            '{"result":"Observed at 0x401000.","model":"claude-test"}'
        )

        self.assertEqual(text, "Observed at 0x401000.")
        self.assertEqual(model, "claude-test")

    def test_parse_claude_event_array(self):
        text, model = parse_claude_output(
            "["
            '{"type":"system","subtype":"init","model":"claude-test"},'
            '{"type":"assistant","message":{"content":[]}},'
            '{"type":"result","is_error":false,"result":"Observed fact."}'
            "]"
        )

        self.assertEqual(text, "Observed fact.")
        self.assertEqual(model, "claude-test")

    def test_parse_claude_jsonl_stream(self):
        text, model = parse_claude_output(
            '{"type":"system","subtype":"init","model":"claude-test"}\n'
            '{"type":"stream_event","event":{"type":"content_block_delta",'
            '"delta":{"type":"text_delta","text":"Observed"}}}\n'
            '{"type":"result","is_error":false,"result":"Observed fact."}\n'
        )

        self.assertEqual(text, "Observed fact.")
        self.assertEqual(model, "claude-test")

    def test_claude_stream_parser_handles_split_json_lines(self):
        chunks = []
        stream = JsonLineStream(claude_stream_delta, chunks.append)
        stream.feed(
            '{"type":"stream_event","event":{"type":"content_block_delta",'
        )
        stream.feed(
            '"delta":{"type":"text_delta","text":"first "}}}\n'
            '{"type":"stream_event","event":{"type":"content_block_delta",'
            '"delta":{"type":"text_delta","text":"second"}}}'
        )
        stream.finish()

        self.assertEqual(chunks, ["first ", "second"])

    def test_parse_claude_json_strips_terminal_sequences(self):
        text, model = parse_claude_output(
            '{"result":"Observed \\u001b[1mfact\\u001b[0m.",'
            '"model":"claude-opus-5\\u001b[1m"}'
        )

        self.assertEqual(text, "Observed fact.")
        self.assertEqual(model, "claude-opus-5")

    def test_parse_claude_json_requires_result(self):
        with self.assertRaises(ProviderError):
            parse_claude_output('{"result":""}')
