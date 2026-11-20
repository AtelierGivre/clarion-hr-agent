from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import GEMINI_API_KEY, GEMINI_MODEL


def get_llm(temperature: float = 0.2) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        api_key=GEMINI_API_KEY,
        temperature=temperature,
        timeout=45,
    )
