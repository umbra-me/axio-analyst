"""Convert Binary Ninja objects into provider-neutral context."""

import os

from binaryninja import BinaryView, Function

from ..core.models import FunctionContext, ProviderError
from ..core.policy import truncate_text


def render_function_context(
    bv: BinaryView,
    function: Function,
    max_context_chars: int,
) -> FunctionContext:
    hlil = function.hlil
    if hlil is None:
        raise ProviderError("Binary Ninja could not produce HLIL for this function.")

    lines = [
        f"0x{instruction.address:x}: {instruction}" for instruction in hlil.instructions
    ]
    rendered, truncated = truncate_text("\n".join(lines), max_context_chars)

    architecture = bv.arch.name if bv.arch is not None else "unknown"
    platform = bv.platform.name if bv.platform is not None else "unknown"
    filename = getattr(bv.file, "filename", "") or "unknown"

    return FunctionContext(
        binary_name=os.path.basename(filename),
        function_name=function.name,
        function_start=function.start,
        architecture=architecture,
        platform=platform,
        function_type=str(function.type),
        hlil=rendered,
        truncated=truncated,
    )
