from __future__ import annotations

import json
from collections.abc import Generator

import requests
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from config import OLLAMA


def _is_retryable_ollama_error(exc: BaseException) -> bool:
    if isinstance(exc, requests.ConnectionError):
        return True
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return exc.response.status_code >= 500
    return False


_ollama_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception(_is_retryable_ollama_error),
    reraise=True,
)


def check_ollama_status() -> tuple[bool, str]:
    """Check if Ollama is running and the configured model is available.

    Returns (is_ready, error_message). If is_ready is True, error_message is empty.
    """
    try:
        resp = requests.get(f"{OLLAMA.host}/api/tags", timeout=OLLAMA.timeout)
        resp.raise_for_status()
    except requests.ConnectionError:
        return False, (
            "⚠️ Ollama is not running. Start it with `ollama serve` in your"
            " terminal, then refresh this page."
        )
    except requests.RequestException as exc:
        return False, f"⚠️ Could not reach Ollama: {exc}"

    models = [m["name"] for m in resp.json().get("models", [])]
    # Ollama may list models with or without the `:latest` tag
    model_found = any(
        name == OLLAMA.model or name.startswith(f"{OLLAMA.model}:")
        for name in models
    )
    if not model_found:
        return False, (
            f"⚠️ Model `{OLLAMA.model}` not found. Pull it with"
            f" `ollama pull {OLLAMA.model}`"
        )

    return True, ""


@_ollama_retry
def _post_chat(payload: dict) -> requests.Response:
    resp = requests.post(
        f"{OLLAMA.host}/api/chat",
        json=payload,
        stream=True,
        timeout=OLLAMA.timeout,
    )
    resp.raise_for_status()
    return resp


def stream_ollama_response(
    prompt: str,
    system_prompt: str | None = None,
) -> Generator[str, None, None]:
    """Stream a chat response from Ollama, yielding tokens as they arrive."""
    messages: list[dict[str, str]] = []
    if system_prompt is not None:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": OLLAMA.model,
        "messages": messages,
        "stream": True,
        "options": {"num_predict": OLLAMA.num_predict},
    }

    resp = _post_chat(payload)

    for line in resp.iter_lines(decode_unicode=True):
        if not line:
            continue
        chunk = json.loads(line)
        token = chunk.get("message", {}).get("content", "")
        if token:
            yield token
        if chunk.get("done", False):
            break
