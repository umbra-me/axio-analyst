"""Exercise actual context packing with lazy harmless BinaryView fixtures."""

import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from tests import package_loader  # noqa: F401
from tests.host_fakes import load_host_module
from axio_analyst.core.models import ContextOptions, ProviderCancelled, ProviderError
from axio_analyst.core.policy import truncate_text


class Instruction:
    def __init__(self, address, text, counter):
        self.address, self.text, self.counter = address, text, counter

    def __str__(self):
        self.counter.append(self.address)
        return self.text


def function(name, start, count=5):
    counter = []
    value = SimpleNamespace(
        name=name, start=start, type=f"int {name}(void)", callees=[],
        instructions=[], call_sites=[], arch=SimpleNamespace(name="x86_64"),
    )
    value.hlil = SimpleNamespace(instructions=[
        Instruction(start + index, f"line_{index}()", counter) for index in range(count)
    ])
    value.rendered = counter
    return value


class TestHostContext(unittest.TestCase):
    def setUp(self):
        self.context = load_host_module("host.context")
        self.primary = function("primary", 0x1000)
        self.bv = SimpleNamespace(
            file=SimpleNamespace(filename="/private/path/base.bin"),
            arch=SimpleNamespace(name="x86_64"), platform=SimpleNamespace(name="test"),
            get_callers=lambda _start: [], get_data_refs_from=lambda _address: [],
            get_string_at=lambda _target: None, get_symbol_at=lambda _target: None,
        )

    def test_primary_stops_formatting_once_budget_is_proven(self):
        self.primary = function("primary", 0x1000, 5000)
        bundle = self.context.render_context_bundle(self.bv, self.primary, 1000)
        original = "\n".join(f"0x{0x1000 + i:x}: line_{i}()" for i in range(5000))
        self.assertEqual(bundle.primary.hlil, truncate_text(original, 1000)[0])
        self.assertTrue(bundle.primary.truncated)
        self.assertEqual(bundle.total_chars, 1000)
        self.assertLess(len(self.primary.rendered), 100)
        self.assertEqual(bundle.primary.binary_name, "base.bin")

    def test_small_primary_is_exact_and_not_truncated(self):
        bundle = self.context.render_context_bundle(self.bv, self.primary, 2000)
        expected = "\n".join(f"0x{0x1000 + i:x}: line_{i}()" for i in range(5))
        self.assertEqual(bundle.primary.hlil, expected)
        self.assertFalse(bundle.truncated)

    def test_late_selection_survives_primary_truncation_and_keeps_half_open_range(self):
        self.primary = function("primary", 0x1000, 5000)
        bundle = self.context.render_context_bundle(
            self.bv, self.primary, 3000, ContextOptions(include_selection=True),
            selection=(0x1000 + 4502, 0x1000 + 4500),
        )
        selection = next(item for item in bundle.items if item.kind == "selection")
        self.assertEqual(selection.text,
                         "0x2194: line_4500()\n0x2195: line_4501()")
        self.assertLess(len(self.primary.rendered), 120)
        self.assertNotIn(0x1000 + 4502, self.primary.rendered)
        self.assertLessEqual(bundle.total_chars, 3000)

    def test_cancel_stops_collection_before_dispatch(self):
        self.primary = function("primary", 0x1000, 5000)
        with self.assertRaises(ProviderCancelled):
            self.context.render_context_bundle(
                self.bv, self.primary, 60000,
                is_cancelled=lambda: len(self.primary.rendered) >= 4,
            )
        self.assertEqual(len(self.primary.rendered), 4)

    def test_callers_callees_and_types_share_deduplicated_limits(self):
        callers = [function(f"caller_{i}", 0x2000 + i * 0x100) for i in range(10)]
        callees = [function(f"callee_{i}", 0x4000 + i * 0x100) for i in range(8)]
        self.bv.get_callers = lambda _: [
            self.primary, SimpleNamespace(function=callers[0]), callers[0], *callers[1:]
        ]
        self.primary.callees = [self.primary, callees[0], callees[0], *callees[1:]]
        bundle = self.context.render_context_bundle(
            self.bv, self.primary, 60000,
            ContextOptions(include_callers=True, include_callees=True, include_types=True),
        )
        selected_callers = [item.start_address for item in bundle.items if item.kind == "caller"]
        selected_callees = [item.start_address for item in bundle.items if item.kind == "callee"]
        self.assertEqual(selected_callers, [f.start for f in callers[:3]])
        self.assertEqual(selected_callees, [f.start for f in callees[:5]])
        types = next(item.text for item in bundle.items if item.kind == "types")
        self.assertEqual(len(types.splitlines()), 9)
        self.assertNotIn("caller_3", types)
        self.assertNotIn("callee_5", types)
        self.assertTrue(types.startswith("primary at 0x1000:"))
        self.assertFalse(callers[3].rendered)

    def test_types_alone_and_zero_neighbour_limits(self):
        self.bv.get_callers = lambda _: [function("extra", 0x2000)]
        self.primary.callees = [function("callee", 0x3000)]
        for options in (
            ContextOptions(include_types=True),
            ContextOptions(include_types=True, include_callers=True, include_callees=True,
                           max_callers=0, max_callees=0),
        ):
            bundle = self.context.render_context_bundle(self.bv, self.primary, 2000, options)
            self.assertEqual([item.kind for item in bundle.items], ["current-function", "types"])
            self.assertEqual(bundle.items[-1].text, "primary at 0x1000: int primary(void)")

    def test_neighbour_formatting_is_bounded(self):
        caller = function("caller", 0x2000, 5000)
        self.bv.get_callers = lambda _: [caller]
        bundle = self.context.render_context_bundle(
            self.bv, self.primary, 6000, ContextOptions(include_callers=True)
        )
        item = next(item for item in bundle.items if item.kind == "caller")
        self.assertTrue(item.truncated)
        self.assertIn("[Direct caller caller truncated by Axio Analyst]", item.text)
        self.assertLess(len(caller.rendered), 100)

    def test_missing_hlil_and_invalid_budget_keep_errors(self):
        self.primary.hlil = None
        with self.assertRaisesRegex(ProviderError, "could not produce HLIL"):
            self.context.render_context_bundle(self.bv, self.primary, 1000)
        with self.assertRaises(ValueError):
            self.context._bounded_text(["test"], 0, "truncated")

    def test_reference_collection_is_lazy_deduplicated_and_cancellable(self):
        self.primary.instructions = [([], i) for i in range(5000)]
        queried = []
        def references(address):
            queried.append(address)
            return [0x8000, 0x8000, 0x8001]
        self.bv.get_data_refs_from = references
        self.bv.get_string_at = lambda target: SimpleNamespace(value=f"value {target}")
        items = self.context._string_items(self.bv, self.primary, 2, 1000, None)
        self.assertEqual([item.start_address for item in items], [0x8000, 0x8001])
        self.assertEqual(queried, [0])
        with self.assertRaises(ProviderCancelled):
            list(self.context._referenced_data(self.bv, self.primary, lambda: True))

    def test_nonmatching_references_have_a_fixed_search_budget_and_one_lookup(self):
        for method, lookup in (("_string_items", "get_string_at"), ("_import_items", "get_symbol_at")):
            with self.subTest(method=method):
                self.primary.instructions = (([], i) for i in range(10_000))
                self.bv.get_data_refs_from = Mock(return_value=[0x8000])
                setattr(self.bv, lookup, Mock(return_value=None))
                items = getattr(self.context, method)(self.bv, self.primary, 1, 1000, None)
                getattr(self.bv, lookup).assert_called_once_with(0x8000)
                self.assertLessEqual(self.bv.get_data_refs_from.call_count, 4096)
                self.assertEqual(len(items), 1)
                self.assertTrue(items[0].truncated)
                self.assertIn("4,096 candidate steps", items[0].text)

    def test_empty_reference_lists_are_bounded_without_materializing_all_addresses(self):
        self.primary.instructions = (([], i) for i in range(10_000))
        self.bv.get_data_refs_from = Mock(return_value=[])
        items = self.context._string_items(self.bv, self.primary, 20, 1000, None)
        self.assertEqual(self.bv.get_data_refs_from.call_count, 4096)
        self.assertTrue(items[0].truncated)

    def test_import_data_and_code_targets_share_a_budget_and_preserve_order(self):
        self.primary.instructions = [([], 0x1000)]
        self.primary.call_sites = [SimpleNamespace(address=0x1001)]
        self.bv.get_data_refs_from = lambda _: [0x8000, 0x8000]
        self.bv.get_callees = lambda *_: [0x8000, 0x9000]
        self.bv.get_symbol_at = Mock(side_effect=lambda target: SimpleNamespace(type="ImportedFunctionSymbol", name=f"import_{target}"))
        items = self.context._import_items(self.bv, self.primary, 2, 1000, None)
        self.assertEqual([item.start_address for item in items], [0x8000, 0x9000])
        self.assertEqual(self.bv.get_symbol_at.call_count, 2)

    def test_large_nul_filled_values_are_sliced_before_decode_and_marked_partial(self):
        class BytesValue(bytes):
            def decode(self, *_args, **_kwargs):
                raise AssertionError("complete host value must not be decoded")
        self.primary.instructions = [([], 0x1000)]
        self.bv.get_data_refs_from = lambda _: [0x8000]
        for value in (BytesValue(b"\0" * 100_000), "\0" * 100_000):
            with self.subTest(value_type=type(value).__name__):
                self.bv.get_string_at = lambda _: SimpleNamespace(value=value)
                item, = self.context._string_items(self.bv, self.primary, 1, 1000, None)
                self.assertTrue(item.truncated)
                self.assertIn("truncated by Axio Analyst", item.text)
                self.assertLessEqual(len(item.text), 1000)
        self.assertEqual(self.context._bounded_value("a\0🙂b".encode(), 100, "truncated"), ("a🙂b", False))

    def test_duplicate_neighbours_and_empty_callee_sites_stop_with_visible_notices(self):
        self.bv.get_callers = lambda _: (self.primary for _ in range(10_000))
        self.primary.callees = None
        self.primary.call_sites = (SimpleNamespace(address=i) for i in range(10_000))
        self.bv.get_callees = Mock(return_value=[])
        bundle = self.context.render_context_bundle(
            self.bv, self.primary, 6000, ContextOptions(include_callers=True, include_callees=True),
        )
        self.assertTrue(bundle.truncated)
        self.assertEqual(self.bv.get_callees.call_count, 4096)
        self.assertTrue(all(item.truncated for item in bundle.items[1:]))
        self.assertIn("Direct caller search truncated", bundle.items[1].text)

    def test_callee_fallback_uses_the_same_limits_for_hlil_and_types(self):
        callees = [function(f"callee_{i}", 0x4000 + i * 0x100) for i in range(8)]
        self.primary.callees = None
        self.primary.call_sites = [SimpleNamespace(address=0x1000)]
        self.bv.get_callees = lambda *_: (value.start for value in callees)
        self.bv.get_functions_at = lambda address: [next(value for value in callees if value.start == address)]
        bundle = self.context.render_context_bundle(
            self.bv, self.primary, 60000, ContextOptions(include_callees=True, include_types=True),
        )
        self.assertEqual(len([item for item in bundle.items if item.kind == "callee"]), 5)
        self.assertNotIn("callee_5", bundle.items[-1].text)

    def test_selection_scan_ceiling_marks_an_unreached_range_instead_of_claiming_empty(self):
        self.primary = function("primary", 0x1000, 30)
        with patch.object(self.context, "MAX_HLIL_INSTRUCTIONS", 10):
            bundle = self.context.render_context_bundle(
                self.bv, self.primary, 3000, ContextOptions(include_selection=True), (0x1014, 0x1015),
            )
        selection = next(item for item in bundle.items if item.kind == "selection")
        self.assertTrue(selection.truncated)
        self.assertIn("Selection 0x1014-0x1015 truncated", selection.text)
        self.assertNotIn("line_20", selection.text)
