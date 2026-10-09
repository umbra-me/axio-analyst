"""Deadline, buffering, and cleanup regression tests with harmless child processes."""

import os
import signal
import subprocess
import sys
import time
import unittest
from dataclasses import replace
from unittest.mock import patch

from tests import package_loader  # noqa: F401
from tests.integration import test_cli_process
from axio_analyst.core.models import ProviderCancelled, ProviderError


class TestProcessLifecycle(unittest.TestCase):
    def provider(self, script, timeout=0.2):
        provider = test_cli_process.TestStreamingProcess._provider(script)
        provider.config = replace(provider.config, timeout_seconds=timeout)
        return provider

    def test_cancelled_request_never_spawns(self):
        with patch("axio_analyst.providers.process.subprocess.Popen") as spawn:
            with self.assertRaises(ProviderCancelled):
                self.provider("pass").run_cli("input", lambda: True)
        spawn.assert_not_called()

    def test_invalid_utf8_prompt_is_rejected_before_spawn(self):
        with patch("axio_analyst.providers.process.subprocess.Popen") as spawn:
            with self.assertRaisesRegex(ProviderError, "not valid UTF-8"):
                self.provider("pass").run_cli("\ud800", None)
        spawn.assert_not_called()

    def test_cleanup_failure_still_closes_pipes(self):
        processes = []
        original_spawn = subprocess.Popen

        def spawn(*args, **kwargs):
            process = original_spawn(*args, **kwargs)
            processes.append(process)
            return process

        with patch("axio_analyst.providers.process.subprocess.Popen", side_effect=spawn):
            with patch("axio_analyst.providers.process.ProcessTree.terminate", side_effect=OSError("cleanup failed")):
                with self.assertRaisesRegex(ProviderError, "cleanup failed"):
                    self.provider("import time; time.sleep(10)", timeout=0.1).run_cli("", None)
        self.assertEqual(len(processes), 1)
        self.assertIsNotNone(processes[0].poll())
        self.assertTrue(all(pipe.closed for pipe in (processes[0].stdin, processes[0].stdout, processes[0].stderr)))

    def test_timeout_interrupts_blocked_stdin(self):
        started = time.monotonic()
        with self.assertRaisesRegex(ProviderError, "timed out"):
            self.provider("import time; time.sleep(10)").run_cli("x" * 3_000_000, None)
        self.assertLess(time.monotonic() - started, 2)

    def test_cancellation_interrupts_blocked_stdin(self):
        started = time.monotonic()
        with self.assertRaises(ProviderCancelled):
            self.provider("import time; time.sleep(10)", timeout=5).run_cli(
                "x" * 3_000_000, lambda: time.monotonic() - started > 0.1
            )
        self.assertLess(time.monotonic() - started, 2)

    def test_eof_does_not_bypass_deadline(self):
        started = time.monotonic()
        with self.assertRaisesRegex(ProviderError, "timed out"):
            self.provider(
                "import os,time; os.close(1); os.close(2); time.sleep(10)"
            ).run_cli("input", None)
        self.assertLess(time.monotonic() - started, 2)

    def test_cancellation_still_checked_after_eof(self):
        started = time.monotonic()
        with self.assertRaises(ProviderCancelled):
            self.provider(
                "import os,time; os.close(1); os.close(2); time.sleep(10)", timeout=5
            ).run_cli("", lambda: time.monotonic() - started > 0.1)

    def test_output_ceiling_is_enforced_while_stdin_is_blocked(self):
        script = (
            "import sys,time; sys.stderr.buffer.write(b'x' * 32768); "
            "sys.stderr.flush(); time.sleep(10)"
        )
        with patch("axio_analyst.providers.process.MAX_PROVIDER_OUTPUT_BYTES", 8192):
            with self.assertRaisesRegex(ProviderError, "output safety limit"):
                self.provider(script, timeout=5).run_cli("x" * 3_000_000, None)

    def test_nonzero_exit_preserves_bounded_stderr(self):
        with self.assertRaisesRegex(ProviderError, "exited with code 3: diagnostic"):
            self.provider(
                "import sys; sys.stdin.read(); print('diagnostic',file=sys.stderr); sys.exit(3)",
                timeout=2,
            ).run_cli("input", None)

    def test_missing_executable_is_normalized(self):
        provider = self.provider("pass")
        provider.command = lambda: ["axio-analyst-nonexistent-test-executable"]
        with self.assertRaisesRegex(ProviderError, "executable not found"):
            provider.run_cli("", None)

    def test_utf8_split_across_pipe_chunks_is_preserved(self):
        script = (
            "import sys,time; sys.stdin.read(); data='a🙂b'.encode(); "
            "sys.stdout.buffer.write(data[:3]); sys.stdout.flush(); time.sleep(.05); "
            "sys.stdout.buffer.write(data[3:]); sys.stdout.flush()"
        )
        chunks = []
        output = self.provider(script, timeout=2).run_cli("", None, on_stdout=chunks.append)
        self.assertEqual(output, "a🙂b")
        self.assertEqual("".join(chunks), output)

    @staticmethod
    def running(pid):
        state = subprocess.run(
            ["ps", "-p", str(pid), "-o", "stat="], capture_output=True, text=True
        ).stdout.strip()
        return bool(state) and not state.startswith("Z")

    @unittest.skipUnless(os.name == "posix", "POSIX process-group runtime check")
    def test_callback_failure_reaps_process_and_descendant(self):
        pids = []
        script = (
            "import os,subprocess,sys,time; "
            "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(10)']); "
            "print(os.getpid(), child.pid, flush=True); time.sleep(10)"
        )

        def fail(chunk):
            pids.extend(int(value) for value in chunk.split())
            raise RuntimeError("consumer failed")

        with self.assertRaisesRegex(RuntimeError, "consumer failed"):
            self.provider(script, timeout=2).run_cli("", None, on_stdout=fail)
        self.assertEqual(len(pids), 2)
        deadline = time.monotonic() + 1
        while any(self.running(pid) for pid in pids) and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertFalse(any(self.running(pid) for pid in pids))

    @unittest.skipUnless(os.name == "posix", "POSIX process-group runtime check")
    def test_cancellation_reaps_process_and_descendant(self):
        pids = []
        script = (
            "import os,subprocess,sys,time; "
            "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(10)']); "
            "print(os.getpid(), child.pid, flush=True); time.sleep(10)"
        )
        with self.assertRaises(ProviderCancelled):
            self.provider(script, timeout=2).run_cli(
                "", lambda: len(pids) == 2,
                on_stdout=lambda chunk: pids.extend(int(value) for value in chunk.split()),
            )
        self.assertEqual(len(pids), 2)
        deadline = time.monotonic() + 1
        while any(self.running(pid) for pid in pids) and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertFalse(any(self.running(pid) for pid in pids))

    @unittest.skipUnless(os.name == "posix", "POSIX process-group runtime check")
    def test_group_termination_error_still_reaps_process_and_descendant(self):
        pids = []
        script = (
            "import os,subprocess,sys,time; "
            "child=subprocess.Popen([sys.executable,'-c','import time; time.sleep(10)']); "
            "print(os.getpid(), child.pid, flush=True); time.sleep(10)"
        )
        original_killpg = os.killpg

        def killpg(pid, sig):
            if sig == signal.SIGTERM:
                raise OSError("graceful cleanup failed")
            original_killpg(pid, sig)

        with patch("axio_analyst.providers.process_tree.os.killpg", side_effect=killpg):
            with self.assertRaisesRegex(ProviderError, "graceful cleanup failed"):
                self.provider(script, timeout=2).run_cli(
                    "", lambda: len(pids) == 2,
                    on_stdout=lambda chunk: pids.extend(int(value) for value in chunk.split()),
                )
        self.assertEqual(len(pids), 2)
        deadline = time.monotonic() + 1
        while any(self.running(pid) for pid in pids) and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertFalse(any(self.running(pid) for pid in pids))

    def test_working_directory_is_unique_and_removed(self):
        script = "import os,sys; sys.stdin.read(); print(os.getcwd(),end='')"
        first = self.provider(script, timeout=2).run_cli("", None)
        second = self.provider(script, timeout=2).run_cli("", None)
        self.assertNotEqual(first, second)
        self.assertFalse(os.path.exists(first))
        self.assertFalse(os.path.exists(second))
