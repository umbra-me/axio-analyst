"""Prompt construction with no Binary Ninja dependency."""

from .models import ContextBundle, ContextItem, FunctionContext


DEFAULT_QUESTION = (
    "Explain what this function does, its inputs and outputs, important control "
    "flow, external effects, and anything security-relevant or uncertain."
)


def _legacy_bundle(context: FunctionContext) -> ContextBundle:
    return ContextBundle(
        primary=context,
        items=(
            ContextItem(
                kind="current-function",
                label=f"Current function {context.function_name}",
                text=context.hlil,
                start_address=context.function_start,
                truncated=context.truncated,
            ),
        ),
        max_chars=len(context.hlil),
        truncated=context.truncated,
    )


def render_context(bundle: ContextBundle) -> str:
    sections: list[str] = []
    for item in bundle.items:
        address = (
            f" at 0x{item.start_address:x}" if item.start_address is not None else ""
        )
        truncated = " (truncated)" if item.truncated else ""
        sections.append(
            f"## {item.label}{address}{truncated}\n"
            f"Kind: {item.kind}\n"
            f"Characters: {item.char_count}\n\n"
            f"{item.text}"
        )
    return "\n\n".join(sections)


def build_prompt(context: FunctionContext | ContextBundle, question: str = "") -> str:
    bundle = context if isinstance(context, ContextBundle) else _legacy_bundle(context)
    primary = bundle.primary
    user_question = question.strip() or DEFAULT_QUESTION
    truncation = "yes" if bundle.truncated else "no"

    return f"""You are assisting with reverse engineering in Binary Ninja.

Answer only from the supplied context. Separate observed facts from inference.
Cite relevant HLIL addresses in the form 0x1234 for important claims. Say when
the available context is insufficient. Do not invent symbol names, types, or
behavior. Do not provide edits or renames unless the question asks for them.

Question:
{user_question}

Binary: {primary.binary_name}
Architecture: {primary.architecture}
Platform: {primary.platform}
Primary function: {primary.function_name} at 0x{primary.function_start:x}
Type: {primary.function_type}
Context items: {len(bundle.items)}
Context characters: {bundle.total_chars}
Context truncated: {truncation}

Context snapshot:
{render_context(bundle)}
"""
