"""Load actual host modules with small unavailable-host substitutes for unit tests."""

import importlib.util
import sys
import types
from unittest.mock import patch

from tests.package_loader import REPO_ROOT


def module(name, **attributes):
    value = types.ModuleType(name)
    value.__dict__.update(attributes)
    return value


class BackgroundTask:
    def __init__(self, *_args, **_kwargs):
        self.cancelled = False

    def cancel(self):
        self.cancelled = True

    def start(self):
        pass


class Signal:
    def __init__(self, *_args):
        self.values = []

    def emit(self, *args):
        self.values.append(args)

    def connect(self, *_args):
        pass


class QObject:
    def __init__(self, *_args):
        pass


def load_host_module(relative, extra=None):
    stubs = {
        "binaryninja": module("binaryninja", BinaryView=object, Function=object,
                             BackgroundTaskThread=BackgroundTask, user_directory=lambda: ""),
        "binaryninja.mainthread": module("binaryninja.mainthread", execute_on_main_thread=lambda fn: fn()),
        "binaryninja.log": module("binaryninja.log", log_info=lambda *_: None,
                                 log_warn=lambda *_: None, log_error=lambda *_: None),
        "binaryninja.interaction": module("binaryninja.interaction", show_plain_text_report=lambda *_: None),
    }
    if extra:
        stubs.update(extra)
    name = f"axio_analyst.{relative}"
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / (relative.replace(".", "/") + ".py"))
    loaded = importlib.util.module_from_spec(spec)
    stubs[name] = loaded
    with patch.dict(sys.modules, stubs):
        spec.loader.exec_module(loaded)
    return loaded
