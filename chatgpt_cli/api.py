from __future__ import annotations
from typing import AsyncIterator

from openai import AsyncOpenAI

from .config import get_api_key, get_model


async def stream_chat(
    messages: list[dict],
    system_prompt: str = "",
    usage_out: list | None = None,
) -> AsyncIterator[str]:
    """Stream a chat completion from OpenAI."""
    client = AsyncOpenAI(api_key=get_api_key())
    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    stream = await client.chat.completions.create(
        model=get_model(),
        messages=full_messages,
        stream=True,
        stream_options={"include_usage": True},
    )
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
        if chunk.usage and usage_out is not None:
            usage_out.append(chunk.usage)
