"""Prompt construction with no Binary Ninja dependency."""

from .models import FunctionContext


DEFAULT_QUESTION = (
    "Explain what this function does, its inputs and outputs, important control "
    "flow, external effects, and anything security-relevant or uncertain."
)


def build_prompt(context: FunctionContext, question: str = "") -> str:
    user_question = question.strip() or DEFAULT_QUESTION
    truncation = "yes" if context.truncated else "no"

    return f"""You are assisting with reverse engineering in Binary Ninja.

Answer only from the supplied context. Separate observed facts from inference.
Cite relevant HLIL addresses in the form 0x1234 for important claims. Say when
the available context is insufficient. Do not invent symbol names, types, or
behavior. Do not provide edits or renames unless the question asks for them.

Question:
{user_question}

Binary: {context.binary_name}
Architecture: {context.architecture}
Platform: {context.platform}
Function: {context.function_name} at 0x{context.function_start:x}
Type: {context.function_type}
HLIL truncated: {truncation}

High Level IL:
```c
{context.hlil}
```
"""
