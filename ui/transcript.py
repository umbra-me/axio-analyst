"""Conversation state and rendering for the sidebar transcript."""

from dataclasses import dataclass
from typing import Optional

from PySide6 import QtGui, QtWidgets

from ..application.conversations import ConversationMessage
from .markdown import restored_scroll_value, sanitize_markdown

#: Raw provider HTML is neutralised here rather than by escaping the source, so
#: fenced code blocks keep their literal ``<``, ``>``, and ``&`` characters.
MARKDOWN_FEATURES = (
    QtGui.QTextDocument.MarkdownFeature.MarkdownDialectGitHub
    | QtGui.QTextDocument.MarkdownFeature.MarkdownNoHTML
)

ASSISTANT_ROLE = "Axio Analyst"


@dataclass
class ChatMessage:
    role: str
    body: str
    meta: str = ""
    evidence: tuple[int, ...] = ()
    unresolved_evidence: tuple[int, ...] = ()


class Transcript:
    def __init__(self, browser: QtWidgets.QTextBrowser):
        self.browser = browser
        self.messages: list[ChatMessage] = []
        self.active_index: Optional[int] = None

    def reset(self) -> None:
        self.messages = [
            ChatMessage(
                "Axio Analyst",
                "Select a function, ask a question, or use **Explain** for a quick read.",
            )
        ]
        self.active_index = None
        self.render(force_bottom=True)

    def append(
        self,
        role: str,
        body: str,
        meta: str = "",
        evidence: tuple[int, ...] = (),
        unresolved_evidence: tuple[int, ...] = (),
    ) -> int:
        self.messages.append(
            ChatMessage(role, body, meta, evidence, unresolved_evidence)
        )
        self.render(force_bottom=True)
        return len(self.messages) - 1

    def start_response(self, meta: str) -> None:
        self.active_index = self.append("Axio Analyst", "", meta)

    def stream(self, chunk: str) -> bool:
        if self.active_index is None or not chunk:
            return False
        if self.active_index >= len(self.messages):
            return False
        self.messages[self.active_index].body += chunk
        self.render()
        return True

    def complete(
        self,
        body: str,
        meta: str,
        evidence: tuple[int, ...] = (),
        unresolved_evidence: tuple[int, ...] = (),
    ) -> None:
        completed_index: Optional[int] = None
        if self.active_index is None:
            self.append(
                "Axio Analyst",
                body,
                meta,
                evidence,
                unresolved_evidence,
            )
        else:
            completed_index = self.active_index
            message = self.messages[self.active_index]
            message.body = body
            message.meta = meta
            message.evidence = evidence
            message.unresolved_evidence = unresolved_evidence
            self.render(focus_index=completed_index)
        self.active_index = None

    def load(self, messages: tuple[ConversationMessage, ...]) -> None:
        self.messages = [
            ChatMessage(
                message.role,
                message.body,
                message.meta,
                message.evidence,
                message.unresolved_evidence,
            )
            for message in messages
        ]
        self.active_index = None
        self.render(force_bottom=True)

    def snapshot(self) -> tuple[ConversationMessage, ...]:
        return tuple(
            ConversationMessage(
                role=message.role,
                body=message.body,
                meta=message.meta,
                evidence=message.evidence,
                unresolved_evidence=message.unresolved_evidence,
            )
            for message in self.messages
        )

    def fail(self, detail: str) -> None:
        if self.active_index is not None:
            active = self.messages[self.active_index]
            if active.body:
                active.body += f"\n\n---\n\n**Request failed:** {detail}"
            else:
                active.role = "Request failed"
                active.body = detail
        else:
            self.messages.append(ChatMessage("Request failed", detail))
        self.active_index = None
        self.render(force_bottom=True)

    def cancel(self) -> None:
        if self.active_index is not None:
            active = self.messages[self.active_index]
            if not active.body:
                active.body = "_Request cancelled before a response was received._"
            else:
                active.body += "\n\n_Request cancelled._"
            self.render(force_bottom=True)
        self.active_index = None

    def _relax_code_blocks(
        self,
        start: int,
        end: int,
        palette: QtGui.QPalette,
    ) -> None:
        """Let fenced code wrap and read as a card.

        Qt imports code blocks with non-breakable lines, which forces the whole
        transcript into horizontal scrolling at realistic dock widths.
        """
        document = self.browser.document()
        editor = QtGui.QTextCursor(document)
        background = palette.color(QtGui.QPalette.ColorRole.AlternateBase)
        block = document.findBlock(start)
        while block.isValid() and block.position() <= end:
            block_format = block.blockFormat()
            if block_format.nonBreakableLines():
                block_format.setNonBreakableLines(False)
                block_format.setBackground(background)
                block_format.setLeftMargin(8.0)
                block_format.setRightMargin(8.0)
                editor.setPosition(block.position())
                editor.setBlockFormat(block_format)
            block = block.next()

    def render(
        self,
        force_bottom: bool = False,
        focus_index: Optional[int] = None,
    ) -> None:
        scrollbar = self.browser.verticalScrollBar()
        previous_value = scrollbar.value()
        previous_maximum = scrollbar.maximum()
        self.browser.clear()
        cursor = self.browser.textCursor()
        palette = self.browser.palette()
        header = QtGui.QTextCharFormat()
        header.setFontWeight(QtGui.QFont.Weight.DemiBold)
        header.setForeground(palette.color(QtGui.QPalette.ColorRole.Link))
        speaker_header = QtGui.QTextCharFormat()
        speaker_header.setFontWeight(QtGui.QFont.Weight.DemiBold)
        speaker_header.setForeground(
            palette.color(QtGui.QPalette.ColorRole.Text)
        )
        meta_format = QtGui.QTextCharFormat()
        meta_format.setForeground(
            palette.color(QtGui.QPalette.ColorRole.PlaceholderText)
        )
        evidence_format = QtGui.QTextCharFormat(meta_format)
        evidence_format.setAnchor(True)
        evidence_format.setForeground(palette.color(QtGui.QPalette.ColorRole.Link))
        evidence_format.setFontUnderline(True)

        focus_position: Optional[int] = None
        for index, message in enumerate(self.messages):
            if index:
                separator = QtGui.QTextBlockFormat()
                separator.setTopMargin(8)
                cursor.insertBlock(separator)
            if index == focus_index:
                focus_position = cursor.position()
            cursor.insertText(
                message.role,
                header if message.role == ASSISTANT_ROLE else speaker_header,
            )
            if message.meta:
                cursor.insertText(f"  ·  {message.meta}", meta_format)
            cursor.insertBlock()
            body = message.body or "_Receiving response..._"
            body_start = cursor.position()
            cursor.insertMarkdown(
                sanitize_markdown(body.strip()), MARKDOWN_FEATURES
            )
            self._relax_code_blocks(body_start, cursor.position(), palette)
            cursor.insertBlock()
            if message.evidence:
                cursor.insertText("Evidence: ", meta_format)
                for evidence_index, address in enumerate(message.evidence):
                    if evidence_index:
                        cursor.insertText("  ", meta_format)
                    link_format = QtGui.QTextCharFormat(evidence_format)
                    link_format.setAnchorHref(f"axio://address/{address:x}")
                    cursor.insertText(f"0x{address:x}", link_format)
                cursor.insertBlock()
            if message.unresolved_evidence:
                addresses = ", ".join(
                    f"0x{address:x}" for address in message.unresolved_evidence
                )
                cursor.insertText(
                    f"Unresolved address citations: {addresses}",
                    meta_format,
                )
                cursor.insertBlock()

        self.browser.setTextCursor(cursor)
        if focus_position is not None:
            block = self.browser.document().findBlock(focus_position)
            block_rect = self.browser.document().documentLayout().blockBoundingRect(
                block
            )
            scrollbar.setValue(int(block_rect.top()))
            return
        scrollbar.setValue(
            restored_scroll_value(
                previous_value,
                previous_maximum,
                scrollbar.maximum(),
                force_bottom,
            )
        )
