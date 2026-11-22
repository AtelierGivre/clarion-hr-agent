import asyncio
import unittest
from unittest.mock import patch

from google.adk.agents import LlmAgent

from app import config
from app.adk_agent import (
    ALLOWED_TOOLS,
    adk_model,
    before_tool,
    build_adk_agent,
)


class _Tool:
    name = "get_leave_balance"


class _Context:
    def __init__(self, state):
        self.state = state


class ADKAgentTests(unittest.TestCase):
    def test_native_gemini_model_is_a_model_name(self):
        with patch.object(config, "GEMINI_API_KEY", "test-gemini"):
            self.assertEqual(adk_model("gemini"), config.GEMINI_MODEL)

    def test_claude_and_openai_use_litellm(self):
        with (
            patch.object(config, "ANTHROPIC_API_KEY", "test-anthropic"),
            patch.object(config, "OPENAI_API_KEY", "test-openai"),
        ):
            self.assertEqual(type(adk_model("anthropic")).__name__, "LiteLlm")
            self.assertEqual(type(adk_model("openai")).__name__, "LiteLlm")

    def test_agent_is_built_with_both_mcp_tools_and_callbacks(self):
        with patch.object(config, "GEMINI_API_KEY", "test-gemini"):
            agent = build_adk_agent("gemini")
        self.assertIsInstance(agent, LlmAgent)
        names = {
            getattr(tool, "name", None) or getattr(tool, "__name__", None)
            for tool in agent.tools
        }
        self.assertTrue(ALLOWED_TOOLS.issubset(names))
        self.assertIsNotNone(agent.before_model_callback)
        self.assertIsNotNone(agent.after_model_callback)
        self.assertIsNotNone(agent.before_tool_callback)

    def test_tool_callback_blocks_cross_employee_reads(self):
        state = {"employee_id": "E102", "tool_calls": [], "events": []}
        args = {"employee_id": "E103"}
        result = asyncio.run(before_tool(_Tool(), args, _Context(state)))
        self.assertEqual(result["error"], "access_denied")
        self.assertEqual(state["tool_calls"][0]["status"], "denied")
        self.assertIn("tool_access_denied:E103", state["events"])

    def test_tool_callback_pins_the_signed_in_employee(self):
        state = {"employee_id": "E102", "tool_calls": [], "events": []}
        args = {"employee_id": "E102"}
        result = asyncio.run(before_tool(_Tool(), args, _Context(state)))
        self.assertIsNone(result)
        self.assertEqual(args["employee_id"], "E102")


if __name__ == "__main__":
    unittest.main()
