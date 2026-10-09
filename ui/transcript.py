"""Conversation state and rendering for the sidebar transcript."""

from dataclasses import dataclass
from typing import Optional

from PySide6 import QtGui, QtWidgets

from ..application.conversations import ConversationMessage
from ..core.findings import Finding
from .markdown import restored_scroll_value, sanitize_markdown

#: Raw provider HTML is neutralised here rather than by escaping the source, so
#: fenced code blocks keep their literal ``<``, ``>``, and ``&`` characters.
MARKDOWN_FEATURES = (
    QtGui.QTextDocument.MarkdownFeature.MarkdownDialectGitHub
    | QtGui.QTextDocument.MarkdownFeature.MarkdownNoHTML
)

ASSISTANT_ROLE = "Axio Analyst"
MAX_LIVE_RESPONSE_CHARS = 64_000


@dataclass
class ChatMessage:
    role: str
    body: str
    meta: str = ""
    evidence: tuple[int, ...] = ()
    unresolved_evidence: tuple[int, ...] = ()
    findings: tuple[Finding, ...] = ()


class Transcript:
    def __init__(self, browser: QtWidgets.QTextBrowser):
        self.browser = browser
        self.messages: list[ChatMessage] = []
        self.active_index: Optional[int] = None
        self._stream_range: Optional[tuple[int, int]] = None
        self._stream_chunks: list[str] = []
        self._live_chars = 0
        self._live_capped = False

    def reset(self) -> None:
        """Leave the conversation genuinely empty.

        The sidebar shows a suggestion panel while there are no messages, so a
        greeting message here would only be a fake first turn to scroll past.
        """
        self.messages = []
        self.active_index = None
        self._stream_chunks.clear()
        self.render(force_bottom=True)

    def append(
        self,
        role: str,
        body: str,
        meta: str = "",
        evidence: tuple[int, ...] = (),
        unresolved_evidence: tuple[int, ...] = (),
        findings: tuple[Finding, ...] = (),
    ) -> int:
        self.messages.append(
            ChatMessage(role, body, meta, evidence, unresolved_evidence, findings)
        )
        self.render(force_bottom=True)
        return len(self.messages) - 1

    def start_response(self, meta: str) -> None:
        self._stream_chunks.clear()
        self._live_chars = 0
        self._live_capped = False
        self.active_index = len(self.messages)
        self.append("Axio Analyst", "", meta)

    def stream(self, chunk: str) -> bool:
        if self.active_index is None or not chunk:
            return False
        if self.active_index >= len(self.messages):
            return False
        first_chunk = not self._stream_chunks
        self._stream_chunks.append(chunk)
        available = max(0, MAX_LIVE_RESPONSE_CHARS - self._live_chars)
        preview = sanitize_markdown(chunk[:available])
        self._live_chars += min(len(chunk), available)
        if len(chunk) > available and not self._live_capped:
            preview += f"\n\n[Live preview limited to {MAX_LIVE_RESPONSE_CHARS:,} characters; full text retained.]"
            self._live_capped = True
        if self._stream_range is not None and (preview or first_chunk):
            scrollbar = self.browser.verticalScrollBar()
            previous_value, previous_maximum = scrollbar.value(), scrollbar.maximum()
            start, end = self._stream_range
            cursor = QtGui.QTextCursor(self.browser.document())
            cursor.setPosition(start if first_chunk else end)
            if first_chunk:
                cursor.setPosition(end, QtGui.QTextCursor.MoveMode.KeepAnchor)
                cursor.removeSelectedText()
            # Partial Markdown is literal text; parse it once on completion.
            cursor.insertText(preview, QtGui.QTextCharFormat())
            self._stream_range = (start, cursor.position())
            scrollbar.setValue(restored_scroll_value(
                previous_value, previous_maximum, scrollbar.maximum(), False,
            ))
        return True

    def complete(
        self,
        body: str,
        meta: str,
        evidence: tuple[int, ...] = (),
        unresolved_evidence: tuple[int, ...] = (),
        findings: tuple[Finding, ...] = (),
    ) -> None:
        completed_index: Optional[int] = None
        if self.active_index is None:
            self.messages.append(ChatMessage(
                "Axio Analyst", body, meta, evidence, unresolved_evidence, findings,
            ))
        else:
            completed_index = self.active_index
            message = self.messages[self.active_index]
            message.body = body
            message.meta = meta
            message.evidence = evidence
            message.unresolved_evidence = unresolved_evidence
            message.findings = findings
        self.active_index = None
        self._stream_chunks.clear()
        self.render(focus_index=completed_index)

    def load(self, messages: tuple[ConversationMessage, ...]) -> None:
        self.messages = [
            ChatMessage(
                message.role,
                message.body,
                message.meta,
                message.evidence,
                message.unresolved_evidence,
                message.findings,
            )
            for message in messages
        ]
        self.active_index = None
        self._stream_chunks.clear()
        self.render(force_bottom=True)

    def snapshot(self) -> tuple[ConversationMessage, ...]:
        return tuple(
            ConversationMessage(
                role=message.role,
                body="".join(self._stream_chunks) if index == self.active_index else message.body,
                meta=message.meta,
                evidence=message.evidence,
                unresolved_evidence=message.unresolved_evidence,
                findings=message.findings,
            )
            for index, message in enumerate(self.messages)
        )

    def fail(self, detail: str) -> None:
        if self.active_index is not None:
            active = self.messages[self.active_index]
            active.body = "".join(self._stream_chunks)
            if active.body:
                active.body += f"\n\n---\n\n**Request failed:** {detail}"
            else:
                active.role = "Request failed"
                active.body = detail
        else:
            self.messages.append(ChatMessage("Request failed", detail))
        self.active_index = None
        self._stream_chunks.clear()
        self.render(force_bottom=True)

    def cancel(self) -> None:
        if self.active_index is not None:
            active = self.messages[self.active_index]
            active.body = "".join(self._stream_chunks)
            if not active.body:
                active.body = "_Request cancelled before a response was received._"
            else:
                active.body += "\n\n_Request cancelled._"
        self.active_index = None
        self._stream_chunks.clear()
        self.render(force_bottom=True)

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

    @staticmethod
    def _insert_footer(
        cursor: QtGui.QTextCursor,
        message: ChatMessage,
        meta_format: QtGui.QTextCharFormat,
        evidence_format: QtGui.QTextCharFormat,
    ) -> None:
        """Collect evidence, unresolved citations, and usage onto one line.

        These used to occupy up to three separate lines under every answer,
        which crowded the conversation at realistic dock widths.
        """
        if not (message.evidence or message.unresolved_evidence or message.meta):
            return
        footer = QtGui.QTextBlockFormat()
        footer.setTopMargin(2.0)
        cursor.insertBlock(footer)
        leading = False
        for address in message.evidence:
            if leading:
                cursor.insertText("  ", meta_format)
            link_format = QtGui.QTextCharFormat(evidence_format)
            link_format.setAnchorHref(f"axio://address/{address:x}")
            cursor.insertText(f"0x{address:x}", link_format)
            leading = True
        if message.unresolved_evidence:
            addresses = ", ".join(
                f"0x{address:x}" for address in message.unresolved_evidence
            )
            count = len(message.unresolved_evidence)
            separator = "   ·   " if leading else ""
            cursor.insertText(
                f"{separator}{count} unresolved ({addresses})",
                meta_format,
            )
            leading = True
        if message.meta:
            separator = "   ·   " if leading else ""
            cursor.insertText(f"{separator}{message.meta}", meta_format)

    def render(
        self,
        force_bottom: bool = False,
        focus_index: Optional[int] = None,
    ) -> None:
        self._stream_range = None
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
            cursor.insertBlock()
            body = (
                "".join(self._stream_chunks)
                if index == self.active_index else message.body
            ) or "_Receiving response..._"
            body_start = cursor.position()
            cursor.insertMarkdown(
                sanitize_markdown(body.strip()), MARKDOWN_FEATURES
            )
            if index == self.active_index:
                self._stream_range = (body_start, cursor.position())
            self._relax_code_blocks(body_start, cursor.position(), palette)
            self._insert_footer(cursor, message, meta_format, evidence_format)

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
