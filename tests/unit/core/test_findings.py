import json
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path
from tests import package_loader  # noqa: F401
from axio_analyst.core.findings import build_findings, finding_from_json
from axio_analyst.core.models import FunctionContext, ContextBundle, ContextItem
from axio_analyst.application.conversations import ConversationMessage, ConversationStore, new_record, record_from_json, render_conversation_markdown

class TestFindings(unittest.TestCase):
    def setUp(self):
        self.context = ContextBundle(FunctionContext("fixture", "main", 0x1000, "x86_64", "test", "int()", "0x1000: return 0"), (ContextItem("function", "main", "0x1000: return 0", 0x1000),), 4096)

    def test_exact_context_provenance_and_staleness(self):
        finding, = build_findings("Returns zero at 0x1000.", self.context, "0.9.0", "fixture", "fake")
        self.assertEqual(finding.addresses, (0x1000,))
        self.assertEqual(finding.context_excerpt, "0x1000: return 0")
        self.assertEqual(finding.status, "unverified")
        self.assertFalse(finding.stale(self.context))
        self.assertTrue(finding.stale(replace(self.context, primary=replace(self.context.primary, hlil="0x1000: return 1"))))

    def test_invented_address_has_no_fabricated_context(self):
        finding, = build_findings("Writes at 0xdead.", self.context, "0.9.0", "fixture", "fake")
        self.assertEqual(finding.context_excerpt, "")
        payload = json.loads(json.dumps(asdict(finding)))
        payload["status"] = "verified"
        with self.assertRaises(ValueError): finding_from_json(payload)

    def test_persistence_export_clear_and_v1_migration(self):
        findings = build_findings("Returns at 0x1000.", self.context, "0.9.0", "fixture", "fake")
        record = new_record("a" * 64, "fixture", (ConversationMessage("Axio Analyst", "Returns at 0x1000.", findings=findings),))
        with tempfile.TemporaryDirectory() as directory:
            store = ConversationStore(Path(directory))
            store.save(record)
            restored = store.load(record.binary_id)
            self.assertEqual(restored.messages[0].findings, findings)
            self.assertIn(findings[0].context_sha256, render_conversation_markdown(restored))
            self.assertTrue(store.delete(record.binary_id))
            self.assertIsNone(store.load(record.binary_id))
        legacy = json.loads(json.dumps(asdict(record)))
        legacy["schema_version"] = 1
        legacy["messages"][0].pop("findings")
        self.assertEqual(record_from_json(legacy).messages[0].findings, ())
