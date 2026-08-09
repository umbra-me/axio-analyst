"""Conversation state and rendering for the sidebar transcript."""

from dataclasses import dataclass
from typing import Optional

from PySide6 import QtGui, QtWidgets

from .markdown import restored_scroll_value, safe_markdown


@dataclass
class ChatMessage:
    role: str
    body: str
    meta: str = ""


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

    def append(self, role: str, body: str, meta: str = "") -> int:
        self.messages.append(ChatMessage(role, body, meta))
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

    def complete(self, body: str, meta: str) -> None:
        if self.active_index is None:
            self.active_index = self.append("Axio Analyst", body)
        else:
            message = self.messages[self.active_index]
            message.body = body
            message.meta = meta
            self.render(force_bottom=True)
        self.active_index = None

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

    def render(self, force_bottom: bool = False) -> None:
        scrollbar = self.browser.verticalScrollBar()
        previous_value = scrollbar.value()
        previous_maximum = scrollbar.maximum()
        self.browser.clear()
        cursor = self.browser.textCursor()
        palette = self.browser.palette()
        header = QtGui.QTextCharFormat()
        header.setFontWeight(QtGui.QFont.Weight.DemiBold)
        header.setForeground(palette.color(QtGui.QPalette.ColorRole.Link))
        meta_format = QtGui.QTextCharFormat()
        meta_format.setForeground(
            palette.color(QtGui.QPalette.ColorRole.PlaceholderText)
        )

        for index, message in enumerate(self.messages):
            if index:
                separator = QtGui.QTextBlockFormat()
                separator.setTopMargin(8)
                cursor.insertBlock(separator)
            cursor.insertText(message.role, header)
            if message.meta:
                cursor.insertText(f"  ·  {message.meta}", meta_format)
            cursor.insertBlock()
            body = message.body or "_Receiving response..._"
            cursor.insertMarkdown(safe_markdown(body.strip()))
            cursor.insertBlock()

        self.browser.setTextCursor(cursor)
        scrollbar.setValue(
            restored_scroll_value(
                previous_value,
                previous_maximum,
                scrollbar.maximum(),
                force_bottom,
            )
        )
