"""OS-owned cleanup for provider processes and their descendants."""

import ctypes
import os
import signal
import subprocess


class ProcessTree:
    """Use a POSIX session or a Windows kill-on-close job, without extra packages."""

    def __init__(self):
        self._job = None
        if os.name != "nt":
            return

        from ctypes import wintypes

        class BasicLimits(ctypes.Structure):
            _fields_ = [
                ("process_time", ctypes.c_int64),
                ("job_time", ctypes.c_int64),
                ("flags", wintypes.DWORD),
                ("minimum_working_set", ctypes.c_size_t),
                ("maximum_working_set", ctypes.c_size_t),
                ("active_process_limit", wintypes.DWORD),
                ("affinity", ctypes.c_size_t),
                ("priority", wintypes.DWORD),
                ("scheduling", wintypes.DWORD),
            ]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [
                ("basic", BasicLimits),
                ("io", ctypes.c_uint64 * 6),
                ("process_memory", ctypes.c_size_t),
                ("job_memory", ctypes.c_size_t),
                ("peak_process_memory", ctypes.c_size_t),
                ("peak_job_memory", ctypes.c_size_t),
            ]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel.CreateJobObjectW.restype = wintypes.HANDLE
        kernel.SetInformationJobObject.argtypes = [
            wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD
        ]
        kernel.SetInformationJobObject.restype = wintypes.BOOL
        kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        self._kernel = kernel
        self._job = kernel.CreateJobObjectW(None, None)
        if not self._job:
            raise ctypes.WinError(ctypes.get_last_error())
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel.SetInformationJobObject(
            self._job, 9, ctypes.byref(limits), ctypes.sizeof(limits)
        ):
            error = ctypes.WinError(ctypes.get_last_error())
            self.close()
            raise error

    def attach(self, process: subprocess.Popen[bytes]) -> None:
        if self._job is not None:
            # Popen owns this process handle; the job never closes that handle.
            if not self._kernel.AssignProcessToJobObject(self._job, int(process._handle)):
                raise ctypes.WinError(ctypes.get_last_error())

    def terminate(self, process: subprocess.Popen[bytes]) -> None:
        try:
            if os.name == "nt":
                self.close()
            else:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass
        finally:
            self.kill(process)

    def kill(self, process: subprocess.Popen[bytes]) -> None:
        """Escalate even if graceful termination or group cleanup failed."""
        try:
            if os.name == "nt":
                self.close()
            if os.name != "nt":
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        finally:
            if process.poll() is None:
                process.kill()
            process.wait(timeout=2)

    def close(self) -> None:
        if self._job is not None:
            self._kernel.CloseHandle(self._job)
            self._job = None
