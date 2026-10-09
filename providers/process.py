"""Bounded supervision for provider command-line processes."""

import codecs
import os
import queue
import subprocess
import tempfile
import threading
import time
from typing import Any

from ..core.models import ProviderCancelled, ProviderConfig, ProviderError
from ..core.provider import CancelCheck, Provider, StreamCallback
from .process_tree import ProcessTree

MAX_PROVIDER_OUTPUT_BYTES = 8_000_000
MAX_QUEUED_CHUNKS = 64


class CliProvider(Provider):
    def __init__(self, config: ProviderConfig):
        self.config = config

    @property
    def display_name(self) -> str:
        raise NotImplementedError

    def command(self) -> list[str]:
        raise NotImplementedError

    def run_cli(
        self,
        prompt: str,
        is_cancelled: CancelCheck,
        environment: dict[str, str] | None = None,
        on_stdout: StreamCallback = None,
        max_output_bytes: int | None = None,
    ) -> str:
        output_limit = MAX_PROVIDER_OUTPUT_BYTES if max_output_bytes is None else max_output_bytes
        if output_limit < 1:
            raise ValueError("max_output_bytes must be positive")
        deadline = time.monotonic() + self.config.timeout_seconds
        self._check_request(is_cancelled, deadline)
        try:
            prompt_bytes = prompt.encode("utf-8")
        except UnicodeEncodeError as exc:
            raise ProviderError(f"{self.display_name} prompt is not valid UTF-8 text.") from exc
        self._check_request(is_cancelled, deadline)
        stopped = threading.Event()
        overflow = threading.Event()
        writer_done = threading.Event()
        chunks: queue.Queue[tuple[str, bytes | None]] = queue.Queue(MAX_QUEUED_CHUNKS)
        byte_lock = threading.Lock()
        total_bytes = 0
        workers: list[threading.Thread] = []
        process = None
        tree = None

        def enqueue(channel: str, chunk: bytes | None) -> None:
            while not stopped.is_set():
                try:
                    chunks.put((channel, chunk), timeout=0.05)
                    return
                except queue.Full:
                    continue

        def pump(channel: str, pipe: Any) -> None:
            nonlocal total_bytes
            try:
                while not stopped.is_set():
                    chunk = pipe.read(4096)
                    if not chunk:
                        break
                    with byte_lock:
                        total_bytes += len(chunk)
                        if total_bytes > output_limit:
                            overflow.set()
                            break
                    enqueue(channel, chunk)
            except (OSError, ValueError):
                pass
            finally:
                enqueue(channel, None)

        def write_prompt() -> None:
            assert process is not None and process.stdin is not None
            try:
                data = memoryview(prompt_bytes)
                while data and not stopped.is_set():
                    written = process.stdin.write(data[:65536])
                    if not written:
                        break
                    data = data[written:]
            except (OSError, ValueError):
                pass  # A child may close stdin; its exit/output decides the result.
            finally:
                try:
                    process.stdin.close()
                except OSError:
                    pass
                writer_done.set()

        try:
            tree = ProcessTree()
            with tempfile.TemporaryDirectory(prefix="axio-analyst-") as workdir:
                process = subprocess.Popen(
                    self.command(),
                    cwd=workdir,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    bufsize=0,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    start_new_session=os.name != "nt", env=environment,
                )
                try:
                    tree.attach(process)
                    assert process.stdout is not None and process.stderr is not None
                    for channel, pipe in (("stdout", process.stdout), ("stderr", process.stderr)):
                        workers.append(threading.Thread(
                            target=pump, args=(channel, pipe),
                            name=f"AxioAnalyst-{self.config.backend}-{channel}", daemon=True,
                        ))
                    workers.append(threading.Thread(
                        target=write_prompt, name=f"AxioAnalyst-{self.config.backend}-stdin",
                        daemon=True,
                    ))
                    for worker in workers:
                        worker.start()

                    decoders = {channel: codecs.getincrementaldecoder("utf-8")("replace")
                                for channel in ("stdout", "stderr")}
                    output: dict[str, list[str]] = {"stdout": [], "stderr": []}
                    finished: set[str] = set()
                    while len(finished) < 2 or not writer_done.is_set() or process.poll() is None:
                        self._check_request(is_cancelled, deadline)
                        if overflow.is_set():
                            raise ProviderError(
                                f"{self.display_name} exceeded the {output_limit:,}-byte output safety limit."
                            )
                        try:
                            remaining = max(0.001, deadline - time.monotonic())
                            channel, chunk = chunks.get(timeout=min(0.05, remaining))
                        except queue.Empty:
                            continue
                        if chunk is None:
                            finished.add(channel)
                            text = decoders[channel].decode(b"", final=True)
                        else:
                            text = decoders[channel].decode(chunk)
                        if text:
                            output[channel].append(text)
                            if channel == "stdout" and on_stdout is not None:
                                on_stdout(text)
                    self._check_request(is_cancelled, deadline)
                    if overflow.is_set():
                        raise ProviderError(f"{self.display_name} exceeded the {output_limit:,}-byte output safety limit.")
                    if process.returncode != 0:
                        detail = "".join(output["stderr"]).strip() or "no diagnostic output on stderr"
                        raise ProviderError(
                            f"{self.display_name} exited with code {process.returncode}: {detail[:2000]}"
                        )
                    return "".join(output["stdout"])
                finally:
                    stopped.set()
                    cleanup_complete = False
                    try:
                        tree.terminate(process)
                        cleanup_complete = True
                    finally:
                        try:
                            if not cleanup_complete:
                                tree.kill(process)
                        finally:
                            for pipe in (process.stdin, process.stdout, process.stderr):
                                if pipe is not None:
                                    try:
                                        pipe.close()
                                    except OSError:
                                        pass
                            for worker in workers:
                                if worker.ident is not None:
                                    worker.join(timeout=0.5)
        except FileNotFoundError as exc:
            raise ProviderError(
                f"{self.display_name} executable not found: {self.config.executable}"
            ) from exc
        except OSError as exc:
            raise ProviderError(f"Could not run {self.display_name}: {exc}") from exc
        except subprocess.TimeoutExpired as exc:
            raise ProviderError(f"Could not stop {self.display_name} after killing its process tree.") from exc
        finally:
            if tree is not None:
                tree.close()

    def _check_request(self, is_cancelled: CancelCheck, deadline: float) -> None:
        if is_cancelled is not None and is_cancelled():
            raise ProviderCancelled(f"{self.display_name} request cancelled.")
        if time.monotonic() >= deadline:
            raise ProviderError(
                f"{self.display_name} timed out after {self.config.timeout_seconds} seconds."
            )
