from __future__ import annotations
from typing import AsyncIterator

from openai import AsyncOpenAI

from .config import get_api_key, get_model


async def stream_chat(messages: list[dict]) -> AsyncIterator[str]:
    """Stream a chat completion from OpenAI."""
    client = AsyncOpenAI(api_key=get_api_key())
    stream = await client.chat.completions.create(
        model=get_model(),
        messages=messages,
        stream=True,
    )
    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
