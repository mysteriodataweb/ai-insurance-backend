import json
import logging

from openai import AsyncOpenAI, OpenAIError

from app.config import settings
from app.errors import LLMError

logger = logging.getLogger(__name__)

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if not settings.GROQ_API_KEY:
        raise LLMError("AI provider is not configured (GROQ_API_KEY is missing).")
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL,
            timeout=settings.LLM_TIMEOUT_SECONDS,
            max_retries=2,
        )
    return _client


def parse_json_content(content: str | None) -> dict:
    text = (content or "").strip()
    # Reasoning models may prepend a <think>...</think> block.
    if "</think>" in text:
        text = text.split("</think>", 1)[1].strip()
    if text.startswith("```"):
        text = text.strip("`").removeprefix("json").strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMError("AI provider returned invalid JSON.") from exc
    if not isinstance(data, dict):
        raise LLMError("AI provider returned an unexpected JSON shape.")
    return data


async def complete_json(system_prompt: str, user_content: str, temperature: float = 0.1) -> dict:
    client = _get_client()
    try:
        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
        )
    except OpenAIError as exc:
        logger.warning("LLM request failed: %s", exc)
        raise LLMError(f"AI provider request failed ({exc.__class__.__name__}).") from exc
    return parse_json_content(response.choices[0].message.content)
