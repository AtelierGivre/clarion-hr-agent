"""Provider-agnostic access to chat models.

The rest of the app asks for a LangChain chat model through ``get_llm`` so the
same LangGraph nodes and guardrails work with Gemini, Claude, or OpenAI.
"""

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from app import config


class ProviderError(ValueError):
    """Raised when a provider is unknown or missing its API key."""


def resolve_provider(provider: str | None = None) -> str:
    """Return a normalized provider name, defaulting to ``LLM_PROVIDER``."""
    name = (provider or config.LLM_PROVIDER or "gemini").strip().lower()
    if name not in config.PROVIDERS:
        raise ProviderError(
            f"Unknown provider {name!r}. Choose from: {', '.join(config.PROVIDERS)}."
        )
    return name


def api_key_for(provider: str) -> str:
    """Return the configured key for a provider, with a clear error if absent."""
    keys = {
        "gemini": config.GEMINI_API_KEY,
        "anthropic": config.ANTHROPIC_API_KEY,
        "openai": config.OPENAI_API_KEY,
    }
    key = keys[provider]
    if not key:
        raise ProviderError(
            f"No API key configured for {provider!r}. "
            f"Set {provider.upper()}_API_KEY (or GEMINI_API_KEY for gemini)."
        )
    return key


def model_for(provider: str) -> str:
    """Return the configured model id for a provider."""
    return {
        "gemini": config.GEMINI_MODEL,
        "anthropic": config.ANTHROPIC_MODEL,
        "openai": config.OPENAI_MODEL,
    }[provider]


def get_llm(
    temperature: float = 0.2,
    provider: str | None = None,
    model: str | None = None,
) -> BaseChatModel:
    """Build a LangChain chat model for the requested provider.

    The first positional argument stays ``temperature`` for backwards
    compatibility with existing callers such as ``get_llm(0)``.
    """
    name = resolve_provider(provider)
    key = api_key_for(name)
    model_id = model or model_for(name)

    if name == "gemini":
        return ChatGoogleGenerativeAI(
            model=model_id, api_key=key, temperature=temperature, timeout=45
        )
    if name == "anthropic":
        return ChatAnthropic(
            model=model_id,
            api_key=key,
            temperature=temperature,
            timeout=45,
            max_tokens=1024,
        )
    return ChatOpenAI(
        model=model_id,
        api_key=key,
        temperature=temperature,
        timeout=45,
        max_retries=2,
    )
