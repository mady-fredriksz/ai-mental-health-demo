from __future__ import annotations

from collections.abc import Generator

import anthropic
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from config import ANTHROPIC

_anthropic_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception_type(
        (anthropic.RateLimitError, anthropic.InternalServerError, anthropic.APIConnectionError),
    ),
    reraise=True,
)


@_anthropic_retry
def _create_stream(client: anthropic.Anthropic, prompt: str, system_prompt: str):
    # Use create(stream=True) instead of .stream() so the HTTP request
    # happens eagerly inside this function, making the retry effective.
    return client.messages.create(
        model=ANTHROPIC.model,
        max_tokens=ANTHROPIC.max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )


def stream_anthropic_response(
    prompt: str,
    system_prompt: str,
) -> Generator[str, None, None]:
    """Stream a chat response from Anthropic Claude, yielding tokens."""
    if ANTHROPIC.api_key is None:
        raise anthropic.AuthenticationError(
            message="ANTHROPIC_API_KEY is not set",
            response=None,
            body=None,
        )

    client = anthropic.Anthropic(
        api_key=ANTHROPIC.api_key.get_secret_value(),
        timeout=ANTHROPIC.timeout,
    )

    with _create_stream(client, prompt, system_prompt) as stream:
        for event in stream:
            if event.type == "content_block_delta" and event.delta.type == "text_delta":
                yield event.delta.text
