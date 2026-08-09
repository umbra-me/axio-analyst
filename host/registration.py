"""Binary Ninja command registration."""

from binaryninja import BinaryView, Function, PluginCommand
from binaryninja.interaction import get_text_line_input, show_plain_text_report
from binaryninja.log import log_error, log_info, log_warn

from ..core.prompts import DEFAULT_QUESTION
from ..core.version import VERSION
from .settings import get_runtime_config, register_settings
from .task import AnalyzeFunctionTask


def _start(bv: BinaryView, function: Function, question: str) -> None:
    AnalyzeFunctionTask(bv, function, question, get_runtime_config()).start()


def _explain(bv: BinaryView, function: Function) -> None:
    _start(bv, function, DEFAULT_QUESTION)


def _ask(bv: BinaryView, function: Function) -> None:
    question = get_text_line_input(
        "What do you want to know about the current function?",
        "Axio Analyst",
    )
    if question is None or not question.strip():
        return
    _start(bv, function, question)


def _open_sidebar(_bv: BinaryView) -> None:
    try:
        from ..ui.sidebar import open_sidebar

        if not open_sidebar():
            log_warn("Axio Analyst: no active sidebar context.")
    except Exception as exc:
        log_error(f"Axio Analyst: could not open sidebar: {exc}")


def _about(_bv: BinaryView) -> None:
    show_plain_text_report(
        "About Axio Analyst",
        f"Axio Analyst v{VERSION}\n\n"
        "Provider-neutral, read-only AI analysis for Binary Ninja.\n\n"
        "https://github.com/umbra-me/axio-analyst",
    )


def register_plugin() -> None:
    register_settings()

    PluginCommand.register_for_function(
        "Axio Analyst\\Explain current function",
        "Send the current function's HLIL to the configured analysis backend.",
        _explain,
    )
    PluginCommand.register_for_function(
        "Axio Analyst\\Ask about current function...",
        "Ask the configured analysis backend a question about the current function.",
        _ask,
    )
    PluginCommand.register(
        "Axio Analyst\\Open sidebar",
        "Open the Axio Analyst conversation sidebar.",
        _open_sidebar,
    )
    PluginCommand.register(
        "Axio Analyst\\About Axio Analyst",
        "Show the installed Axio Analyst version.",
        _about,
    )

    try:
        from ..ui.sidebar import register_sidebar

        register_sidebar()
    except ImportError as exc:
        log_error(f"Axio Analyst: sidebar unavailable: {exc}")
    except Exception as exc:
        log_error(f"Axio Analyst: sidebar registration failed: {exc}")

    log_info(f"Axio Analyst v{VERSION}: plugin registration complete.")
