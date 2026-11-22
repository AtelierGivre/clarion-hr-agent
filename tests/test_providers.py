import unittest
from unittest.mock import patch

from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app import config, llm


class ProviderTests(unittest.TestCase):
    def test_resolve_provider_normalizes_and_defaults(self):
        with patch.object(config, "LLM_PROVIDER", " Gemini "):
            self.assertEqual(llm.resolve_provider(), "gemini")
        self.assertEqual(llm.resolve_provider("OPENAI"), "openai")

    def test_unknown_provider_is_rejected(self):
        with self.assertRaises(llm.ProviderError):
            llm.resolve_provider("mistral")

    def test_missing_api_key_has_a_clear_error(self):
        with patch.object(config, "ANTHROPIC_API_KEY", ""):
            with self.assertRaisesRegex(llm.ProviderError, "ANTHROPIC_API_KEY"):
                llm.get_llm(provider="anthropic")

    def test_each_provider_builds_its_langchain_model(self):
        with (
            patch.object(config, "GEMINI_API_KEY", "test-gemini"),
            patch.object(config, "ANTHROPIC_API_KEY", "test-anthropic"),
            patch.object(config, "OPENAI_API_KEY", "test-openai"),
        ):
            self.assertIsInstance(
                llm.get_llm(provider="gemini"), ChatGoogleGenerativeAI
            )
            self.assertIsInstance(
                llm.get_llm(provider="anthropic"), ChatAnthropic
            )
            self.assertIsInstance(llm.get_llm(provider="openai"), ChatOpenAI)

    def test_model_for_uses_provider_configuration(self):
        with patch.object(config, "OPENAI_MODEL", "gpt-4.1-mini"):
            self.assertEqual(llm.model_for("openai"), "gpt-4.1-mini")


if __name__ == "__main__":
    unittest.main()
