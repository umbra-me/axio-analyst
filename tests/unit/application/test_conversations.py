"""Machine-local conversation persistence tests."""

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from tests import package_loader  # noqa: F401

from axio_analyst.application.conversations import (
    ConversationMessage,
    ConversationStore,
    MAX_MESSAGE_CHARS,
    new_record,
    render_conversation_markdown,
)


class TestConversationStore(unittest.TestCase):
    def setUp(self):
        self.binary_id = "a" * 64
        self.record = new_record(
            self.binary_id,
            "sample.exe",
            (
                ConversationMessage("You", "What happens?", "main"),
                ConversationMessage(
                    "Axio Analyst",
                    "Returns at 0x1000.",
                    "Codex",
                    (0x1000,),
                ),
            ),
        )

    def test_round_trip_export_and_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ConversationStore(Path(directory))
            store.save(self.record)

            loaded = store.load(self.binary_id)
            exported = Path(directory) / "conversation.md"
            store.export_markdown(self.record, exported)
            deleted = store.delete(self.binary_id)

            self.assertEqual(loaded, self.record)
            self.assertIn("Evidence: 0x1000", exported.read_text(encoding="utf-8"))
            self.assertTrue(deleted)
            self.assertIsNone(store.load(self.binary_id))

    def test_rejects_path_traversal_identifier(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ConversationStore(Path(directory))
            with self.assertRaises(ValueError):
                store.load("../outside")

    def test_rejects_unknown_schema(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / f"{self.binary_id}.json"
            path.write_text(
                json.dumps({"schema_version": 99}),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                ConversationStore(Path(directory)).load(self.binary_id)

    def test_markdown_does_not_include_binary_identifier(self):
        markdown = render_conversation_markdown(self.record)

        self.assertNotIn(self.binary_id, markdown)
        self.assertIn("sample.exe", markdown)

    def test_rejects_oversized_message_before_writing(self):
        with self.assertRaises(ValueError):
            new_record(
                self.binary_id,
                "sample.exe",
                (ConversationMessage("Axio Analyst", "x" * (MAX_MESSAGE_CHARS + 1)),),
            )

    def test_rejects_unknown_schema_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            store = ConversationStore(Path(directory))
            with self.assertRaises(ValueError):
                store.save(replace(self.record, schema_version=99))
