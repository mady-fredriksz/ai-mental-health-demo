from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass

from config import ANTHROPIC, OPENAI
from constants import Tier3Model
from models.anthropic_client import stream_anthropic_response
from models.ollama_client import check_ollama_status, stream_ollama_response
from models.openai_client import stream_openai_response
from prompts import TIER_1_SYSTEM_PROMPT, TIER_2_SYSTEM_PROMPT, TIER_3_SYSTEM_PROMPT


def has_api_key(provider: Tier3Model) -> bool:
    """Return whether an API key is configured for the given provider."""
    if provider == "claude":
        return ANTHROPIC.api_key is not None
    return OPENAI.api_key is not None


def stream_tier_response(
    tier_num: int,
    prompt: str,
    tier3_model: Tier3Model = "claude",
    system_prompt: str | None = None,
) -> Generator[str, None, None]:
    """Single entry point that routes to the correct model client."""
    if tier_num == 1:
        return stream_ollama_response(prompt, TIER_1_SYSTEM_PROMPT)
    if tier_num == 2:
        return stream_ollama_response(
            prompt, system_prompt if system_prompt is not None else TIER_2_SYSTEM_PROMPT,
        )

    # Tier 3
    sp = system_prompt if system_prompt is not None else TIER_3_SYSTEM_PROMPT
    if tier3_model == "claude":
        return stream_anthropic_response(prompt, sp)
    return stream_openai_response(prompt, sp)


@dataclass
class StartupStatus:
    ollama_ready: bool
    ollama_error: str
    has_anthropic_key: bool
    has_openai_key: bool

    @property
    def warnings(self) -> list[str]:
        msgs: list[str] = []
        if not self.ollama_ready and self.ollama_error:
            msgs.append(self.ollama_error)
        if not self.has_anthropic_key:
            msgs.append("ANTHROPIC_API_KEY not found.")
        if not self.has_openai_key:
            msgs.append("OPENAI_API_KEY not found.")
        return msgs


def validate_startup() -> StartupStatus:
    """Check Ollama status and API key availability."""
    ollama_ready, ollama_error = check_ollama_status()
    return StartupStatus(
        ollama_ready=ollama_ready,
        ollama_error=ollama_error,
        has_anthropic_key=has_api_key("claude"),
        has_openai_key=has_api_key("gpt"),
    )
