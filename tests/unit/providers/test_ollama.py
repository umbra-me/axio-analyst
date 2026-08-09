"""Ollama Cloud adapter and catalog tests."""

import unittest
from unittest.mock import patch

from tests import package_loader  # noqa: F401

from axio_analyst.core.models import ProviderConfig, ProviderError
from axio_analyst.providers import OllamaCloudProvider
from axio_analyst.providers.ollama import (
    fetch_ollama_cloud_catalog,
    parse_ollama_cloud_catalog,
    parse_ollama_cloud_models,
)


class TestOllamaCloudProvider(unittest.TestCase):
    def test_command_uses_model_stdin_and_thinking_level(self):
        config = ProviderConfig(
            backend="ollama-cloud",
            executable="ollama",
            model="gpt-oss:120b-cloud",
            timeout_seconds=30,
            reasoning_effort="high",
        )

        command = OllamaCloudProvider(config).command()

        self.assertEqual(command[:3], ["ollama", "run", "gpt-oss:120b-cloud"])
        self.assertIn("--nowordwrap", command)
        self.assertIn("--hidethinking", command)
        self.assertIn("--think=high", command)
        self.assertNotIn("sensitive decompiler text", command)

    def test_parse_cloud_models_filters_local_models_and_deduplicates(self):
        models = parse_ollama_cloud_models(
            "NAME                  ID              SIZE    MODIFIED\n"
            "kimi-k3:cloud         630e737485bd    -       7 days ago\n"
            "qwen3.5:9b            abcdef123456    6 GB    2 days ago\n"
            "gpt-oss:120b-cloud    ac7f7a1e7785    -       7 days ago\n"
            "kimi-k3:cloud         630e737485bd    -       7 days ago\n"
        )

        self.assertEqual(models, ["kimi-k3:cloud", "gpt-oss:120b-cloud"])

    def test_parse_cloud_models_accepts_empty_list(self):
        self.assertEqual(parse_ollama_cloud_models("NAME ID SIZE MODIFIED\n"), [])

    def test_parse_remote_catalog_normalizes_cli_cloud_tags(self):
        models = parse_ollama_cloud_catalog(
            '{"models":['
            '{"name":"glm-5.1"},'
            '{"name":"gpt-oss:120b"},'
            '{"name":"deepseek-v4-flash:preview"},'
            '{"name":"already:cloud"},'
            '{"model":"qwen3.5:397b"}'
            "]}"
        )

        self.assertEqual(
            models,
            [
                "glm-5.1:cloud",
                "gpt-oss:120b-cloud",
                "deepseek-v4-flash:preview-cloud",
                "already:cloud",
                "qwen3.5:397b-cloud",
            ],
        )

    def test_parse_remote_catalog_rejects_invalid_shape(self):
        with self.assertRaises(ProviderError):
            parse_ollama_cloud_catalog('{"items":[]}')

    def test_fetch_remote_catalog_uses_bounded_public_request(self):
        payload = b'{"models":[{"name":"glm-5.1"}]}'
        with patch(
            "axio_analyst.providers.ollama.urllib.request.urlopen"
        ) as open_url:
            response = open_url.return_value.__enter__.return_value
            response.read.return_value = payload

            models = fetch_ollama_cloud_catalog(timeout_seconds=7)

        request = open_url.call_args.args[0]
        self.assertEqual(request.full_url, "https://ollama.com/api/tags")
        self.assertEqual(open_url.call_args.kwargs["timeout"], 7)
        response.read.assert_called_once_with(1_000_001)
        self.assertEqual(models, ["glm-5.1:cloud"])
