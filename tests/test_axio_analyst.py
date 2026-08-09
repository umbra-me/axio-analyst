"""Tests for Axio Analyst logic that does not require Binary Ninja."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_SPEC = importlib.util.spec_from_file_location(
    "axio_analyst",
    REPO_ROOT / "__init__.py",
    submodule_search_locations=[str(REPO_ROOT)],
)
if PACKAGE_SPEC is None or PACKAGE_SPEC.loader is None:
    raise RuntimeError("Could not create the axio_analyst test package")
PACKAGE = importlib.util.module_from_spec(PACKAGE_SPEC)
sys.modules["axio_analyst"] = PACKAGE
PACKAGE_SPEC.loader.exec_module(PACKAGE)

from axio_analyst.models import (  # noqa: E402
    FunctionContext,
    ProviderCancelled,
    ProviderConfig,
    ProviderError,
)
from axio_analyst.prompts import build_prompt, truncate_text  # noqa: E402
from axio_analyst.providers import (  # noqa: E402
    ClaudeCodeProvider,
    CodexCliProvider,
    OllamaCloudProvider,
    _CliProvider,
    _JsonLineStream,
    _claude_stream_delta,
    _codex_stream_delta,
    _parse_claude_output,
    _parse_codex_output,
    fetch_ollama_cloud_catalog,
    parse_ollama_cloud_catalog,
    parse_ollama_cloud_models,
)
from axio_analyst.rendering import restored_scroll_value, safe_markdown  # noqa: E402


class TestRepositoryContract(unittest.TestCase):
    def test_plugin_metadata_uses_product_name_and_version(self):
        metadata = json.loads((REPO_ROOT / "plugin.json").read_text(encoding="utf-8"))

        self.assertEqual(metadata["name"], "Axio Analyst")
        self.assertEqual(metadata["version"], "0.7.0")
        self.assertIn("ui", metadata["type"])

    def test_sidebar_icon_uses_axio_initials(self):
        sidebar = (REPO_ROOT / "sidebar.py").read_text(encoding="utf-8")

        self.assertIn('            "AX",', sidebar)

    def test_development_installer_copies_a_current_runtime(self):
        tool = REPO_ROOT / "tools" / "plugin_dev.py"
        with tempfile.TemporaryDirectory() as directory:
            plugins_dir = Path(directory) / "plugins"
            install = subprocess.run(
                [
                    sys.executable,
                    str(tool),
                    "install",
                    "--plugins-dir",
                    str(plugins_dir),
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            current = subprocess.run(
                [
                    sys.executable,
                    str(tool),
                    "status",
                    "--plugins-dir",
                    str(plugins_dir),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(install.returncode, 0, install.stderr)
        self.assertEqual(current.returncode, 0, current.stderr)
        self.assertIn("Axio Analyst is current", current.stdout)


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
        self.assertEqual(
            command[command.index("--output-format") + 1],
            "stream-json",
        )
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
        text, model = _parse_claude_output(
            '{"result":"Observed at 0x401000.","model":"claude-test"}'
        )

        self.assertEqual(text, "Observed at 0x401000.")
        self.assertEqual(model, "claude-test")

    def test_parse_claude_event_array(self):
        text, model = _parse_claude_output(
            "["
            '{"type":"system","subtype":"init","model":"claude-test"},'
            '{"type":"assistant","message":{"content":[]}},'
            '{"type":"result","is_error":false,"result":"Observed fact."}'
            "]"
        )

        self.assertEqual(text, "Observed fact.")
        self.assertEqual(model, "claude-test")

    def test_parse_claude_jsonl_stream(self):
        text, model = _parse_claude_output(
            '{"type":"system","subtype":"init","model":"claude-test"}\n'
            '{"type":"stream_event","event":{"type":"content_block_delta",'
            '"delta":{"type":"text_delta","text":"Observed"}}}\n'
            '{"type":"result","is_error":false,"result":"Observed fact."}\n'
        )

        self.assertEqual(text, "Observed fact.")
        self.assertEqual(model, "claude-test")

    def test_claude_stream_parser_handles_split_json_lines(self):
        chunks = []
        stream = _JsonLineStream(_claude_stream_delta, chunks.append)
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
        text, model = _parse_claude_output(
            '{"result":"Observed \\u001b[1mfact\\u001b[0m.",'
            '"model":"claude-opus-5\\u001b[1m"}'
        )

        self.assertEqual(text, "Observed fact.")
        self.assertEqual(model, "claude-opus-5")

    def test_parse_claude_json_requires_result(self):
        with self.assertRaises(ProviderError):
            _parse_claude_output('{"result":""}')


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
        text = _parse_codex_output(
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
            _parse_codex_output('{"type":"turn.completed"}\n')

    def test_codex_stream_emits_completed_agent_message(self):
        chunks = []
        stream = _JsonLineStream(_codex_stream_delta, chunks.append)
        stream.feed(
            '{"type":"item.completed","item":{"type":"agent_message",'
            '"text":"Final **analysis**"}}\n'
        )

        self.assertEqual(chunks, ["Final **analysis**"])


class TestOllamaCloudProvider(unittest.TestCase):
    def test_command_uses_model_stdin_and_thinking_level(self):
        config = ProviderConfig(
            backend="ollama-cloud",
            executable="ollama",
            model="gpt-oss:120b-cloud",
            timeout_seconds=30,
            reasoning_effort="high",
        )

        command = OllamaCloudProvider(config).command()

        self.assertEqual(command[:3], ["ollama", "run", "gpt-oss:120b-cloud"])
        self.assertIn("--nowordwrap", command)
        self.assertIn("--hidethinking", command)
        self.assertIn("--think=high", command)
        self.assertNotIn("sensitive decompiler text", command)

    def test_parse_cloud_models_filters_local_models_and_deduplicates(self):
        models = parse_ollama_cloud_models(
            "NAME                  ID              SIZE    MODIFIED\n"
            "kimi-k3:cloud         630e737485bd    -       7 days ago\n"
            "qwen3.5:9b            abcdef123456    6 GB    2 days ago\n"
            "gpt-oss:120b-cloud    ac7f7a1e7785    -       7 days ago\n"
            "kimi-k3:cloud         630e737485bd    -       7 days ago\n"
        )

        self.assertEqual(models, ["kimi-k3:cloud", "gpt-oss:120b-cloud"])

    def test_parse_cloud_models_accepts_empty_list(self):
        self.assertEqual(parse_ollama_cloud_models("NAME ID SIZE MODIFIED\n"), [])

    def test_parse_remote_catalog_normalizes_cli_cloud_tags(self):
        models = parse_ollama_cloud_catalog(
            '{"models":['
            '{"name":"glm-5.1"},'
            '{"name":"gpt-oss:120b"},'
            '{"name":"deepseek-v4-flash:preview"},'
            '{"name":"already:cloud"},'
            '{"model":"qwen3.5:397b"}'
            "]}"
        )

        self.assertEqual(
            models,
            [
                "glm-5.1:cloud",
                "gpt-oss:120b-cloud",
                "deepseek-v4-flash:preview-cloud",
                "already:cloud",
                "qwen3.5:397b-cloud",
            ],
        )

    def test_parse_remote_catalog_rejects_invalid_shape(self):
        with self.assertRaises(ProviderError):
            parse_ollama_cloud_catalog('{"items":[]}')

    def test_fetch_remote_catalog_uses_bounded_public_request(self):
        payload = b'{"models":[{"name":"glm-5.1"}]}'
        with patch("axio_analyst.providers.urllib.request.urlopen") as open_url:
            response = open_url.return_value.__enter__.return_value
            response.read.return_value = payload

            models = fetch_ollama_cloud_catalog(timeout_seconds=7)

        request = open_url.call_args.args[0]
        self.assertEqual(request.full_url, "https://ollama.com/api/tags")
        self.assertEqual(open_url.call_args.kwargs["timeout"], 7)
        response.read.assert_called_once_with(1_000_001)
        self.assertEqual(models, ["glm-5.1:cloud"])


class TestStreamingProcess(unittest.TestCase):
    @staticmethod
    def _provider(script):
        class ProbeProvider(_CliProvider):
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

        output = provider._run_cli("input", None, on_stdout=chunks.append)

        self.assertEqual(output, "first second")
        self.assertEqual("".join(chunks), "first second")

    def test_cli_reader_cancels_sleeping_process(self):
        provider = self._provider(
            "import sys,time; sys.stdin.buffer.read(); time.sleep(5)"
        )
        started = time.monotonic()

        with self.assertRaises(ProviderCancelled):
            provider._run_cli(
                "input",
                lambda: time.monotonic() - started > 0.05,
            )


class TestMarkdownRendering(unittest.TestCase):
    def test_safe_markdown_preserves_formatting_and_escapes_html(self):
        rendered = safe_markdown("**bold** <img src=x> & text")

        self.assertEqual(
            rendered,
            "**bold** &lt;img src=x&gt; &amp; text",
        )

    def test_safe_markdown_removes_nul(self):
        self.assertEqual(safe_markdown("before\x00after"), "beforeafter")

    def test_live_tail_follows_when_reader_is_at_bottom(self):
        self.assertEqual(restored_scroll_value(100, 100, 140), 140)

    def test_live_tail_preserves_reader_scroll_position(self):
        self.assertEqual(restored_scroll_value(40, 100, 140), 40)

    def test_forced_scroll_moves_new_message_into_view(self):
        self.assertEqual(restored_scroll_value(40, 100, 140, True), 140)


if __name__ == "__main__":
    unittest.main()
