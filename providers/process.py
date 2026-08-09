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

MAX_PROVIDER_OUTPUT_BYTES = 8_000_000


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
    ) -> str:
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        workdir = os.path.join(tempfile.gettempdir(), "axio-analyst")
        os.makedirs(workdir, exist_ok=True)
        try:
            process = subprocess.Popen(
                self.command(),
                cwd=workdir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creation_flags,
                env=environment,
            )
        except FileNotFoundError as exc:
            raise ProviderError(
                f"{self.display_name} executable not found: {self.config.executable}"
            ) from exc
        except OSError as exc:
            raise ProviderError(f"Could not start {self.display_name}: {exc}") from exc

        assert process.stdin is not None
        assert process.stdout is not None
        assert process.stderr is not None

        chunks: queue.Queue[tuple[str, bytes | None]] = queue.Queue()

        def pump(channel: str, pipe: Any) -> None:
            read = getattr(pipe, "read1", pipe.read)
            try:
                while True:
                    chunk = read(4096)
                    if not chunk:
                        break
                    chunks.put((channel, chunk))
            except (OSError, ValueError):
                pass
            finally:
                chunks.put((channel, None))

        readers = [
            threading.Thread(
                target=pump,
                args=("stdout", process.stdout),
                name=f"AxioAnalyst-{self.config.backend}-stdout",
                daemon=True,
            ),
            threading.Thread(
                target=pump,
                args=("stderr", process.stderr),
                name=f"AxioAnalyst-{self.config.backend}-stderr",
                daemon=True,
            ),
        ]
        for reader in readers:
            reader.start()

        try:
            process.stdin.write(prompt.encode("utf-8"))
            process.stdin.close()
        except OSError:
            pass

        deadline = time.monotonic() + self.config.timeout_seconds
        decoders = {
            "stdout": codecs.getincrementaldecoder("utf-8")("replace"),
            "stderr": codecs.getincrementaldecoder("utf-8")("replace"),
        }
        output = {"stdout": [], "stderr": []}
        finished_channels: set[str] = set()
        total_bytes = 0

        while len(finished_channels) < 2:
            if is_cancelled is not None and is_cancelled():
                self.stop(process)
                raise ProviderCancelled(f"{self.display_name} request cancelled.")

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self.stop(process)
                raise ProviderError(
                    f"{self.display_name} timed out after "
                    f"{self.config.timeout_seconds} seconds."
                )

            try:
                channel, chunk = chunks.get(timeout=min(0.1, remaining))
            except queue.Empty:
                continue

            if chunk is None:
                finished_channels.add(channel)
                continue

            total_bytes += len(chunk)
            if total_bytes > MAX_PROVIDER_OUTPUT_BYTES:
                self.stop(process)
                raise ProviderError(
                    f"{self.display_name} exceeded the 8 MB output safety limit."
                )

            text = decoders[channel].decode(chunk)
            output[channel].append(text)
            if channel == "stdout" and text and on_stdout is not None:
                on_stdout(text)

        for channel, decoder in decoders.items():
            tail = decoder.decode(b"", final=True)
            if tail:
                output[channel].append(tail)
                if channel == "stdout" and on_stdout is not None:
                    on_stdout(tail)

        process.wait()
        for reader in readers:
            reader.join(timeout=0.5)
        process.stdout.close()
        process.stderr.close()

        stdout = "".join(output["stdout"])
        stderr = "".join(output["stderr"])

        if process.returncode != 0:
            detail = stderr.strip() or "no diagnostic output on stderr"
            raise ProviderError(
                f"{self.display_name} exited with code {process.returncode}: "
                f"{detail[:2000]}"
            )
        return stdout

    @staticmethod
    def stop(process: subprocess.Popen[bytes]) -> None:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        for pipe in (process.stdin, process.stdout, process.stderr):
            if pipe is not None and not pipe.closed:
                pipe.close()
