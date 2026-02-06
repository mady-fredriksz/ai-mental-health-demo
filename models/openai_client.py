from __future__ import annotations

from collections.abc import Generator

import openai
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config import OPENAI

_openai_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception_type(
        (openai.RateLimitError, openai.InternalServerError, openai.APIConnectionError),
    ),
    reraise=True,
)


@_openai_retry
def _create_stream(client: openai.OpenAI, messages: list[dict[str, str]]):
    return client.chat.completions.create(
        model=OPENAI.model,
        messages=messages,
        max_completion_tokens=OPENAI.max_tokens,
        stream=True,
    )


def stream_openai_response(
    prompt: str,
    system_prompt: str,
) -> Generator[str, None, None]:
    """Stream a chat response from OpenAI GPT, yielding tokens."""
    if OPENAI.api_key is None:
        raise openai.AuthenticationError(
            message="OPENAI_API_KEY is not set",
            response=None,
            body=None,
        )

    client = openai.OpenAI(
        api_key=OPENAI.api_key.get_secret_value(),
        timeout=OPENAI.timeout,
    )

    messages: list[dict[str, str]] = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    response = _create_stream(client, messages)

    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
