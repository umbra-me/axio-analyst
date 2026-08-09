"""Provider usage presentation tests."""

import unittest

from tests import package_loader  # noqa: F401

from axio_analyst.core.models import ProviderUsage
from axio_analyst.core.usage import format_usage


class TestUsageFormatting(unittest.TestCase):
    def test_prefers_token_and_cost_metadata_when_available(self):
        rendered = format_usage(
            ProviderUsage(
                input_chars=100,
                output_chars=20,
                input_tokens=25,
                output_tokens=5,
                cached_input_tokens=10,
                cost_usd=0.0123,
                duration_seconds=1.25,
            )
        )

        self.assertIn("25 in / 5 out tokens", rendered)
        self.assertIn("10 cached", rendered)
        self.assertIn("$0.0123", rendered)

    def test_falls_back_to_character_counts(self):
        rendered = format_usage(
            ProviderUsage(input_chars=100, output_chars=20, duration_seconds=0.5)
        )

        self.assertIn("100 in / 20 out chars", rendered)
