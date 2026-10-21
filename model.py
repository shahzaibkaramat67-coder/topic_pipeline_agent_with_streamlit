from contextlib import asynccontextmanager
from contextvars import ContextVar
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()


@dataclass(frozen=True)
class ModelSettings:
    base_url: str
    model: str
    api_key: str = field(repr=False)


_active_model: ContextVar[tuple[AsyncOpenAI, str] | None] = ContextVar(
    "active_model", default=None
)


def validate_settings(settings: ModelSettings) -> None:
    if not settings.base_url.strip():
        raise ValueError("Enter an API base URL.")
    if not settings.model.strip():
        raise ValueError("Enter a model name.")
    if not settings.api_key.strip():
        raise ValueError("Enter an API key.")


async def _complete(client: AsyncOpenAI, model: str, prompt: str) -> str:
    response = await client.chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}]
    )
    content = response.choices[0].message.content
    if content is None:
        raise ValueError("The model returned an empty response.")
    return content


@asynccontextmanager
async def model_session(settings: ModelSettings) -> AsyncIterator[None]:
    validate_settings(settings)
    async with AsyncOpenAI(
        base_url=settings.base_url, api_key=settings.api_key
    ) as client:
        token = _active_model.set((client, settings.model))
        try:
            yield
        finally:
            _active_model.reset(token)


async def test_api_connection(settings: ModelSettings) -> str:
    validate_settings(settings)
    async with AsyncOpenAI(
        base_url=settings.base_url, api_key=settings.api_key
    ) as client:
        return await _complete(
            client, settings.model, "Reply with only the word OK."
        )


async def llm(prompt: str) -> str:
    active_model = _active_model.get()
    if active_model is not None:
        client, model = active_model
        return await _complete(client, model, prompt)

    settings = ModelSettings(
        base_url=os.getenv("FREELLMAPI_BASE_URL", ""),
        model=os.getenv("FREELLMAPI_MODEL", ""),
        api_key=os.getenv("FREELLMAPI_API_KEY", ""),
    )
    validate_settings(settings)
    async with AsyncOpenAI(
        base_url=settings.base_url, api_key=settings.api_key
    ) as client:
        return await _complete(client, settings.model, prompt)
