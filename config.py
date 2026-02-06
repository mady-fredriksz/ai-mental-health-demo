from __future__ import annotations

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class OllamaConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OLLAMA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = "http://localhost:11434"
    model: str = "mistral:7b-instruct"
    num_predict: int = 400
    timeout: int = 60


class AnthropicConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ANTHROPIC_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: SecretStr | None = None
    model: str = "claude-sonnet-4-5-20250929"
    max_tokens: int = 400
    timeout: int = 30


class OpenAIConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="OPENAI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: SecretStr | None = None
    model: str = "gpt-5.2"
    max_tokens: int = 400
    timeout: int = 30


OLLAMA = OllamaConfig()
ANTHROPIC = AnthropicConfig()
OPENAI = OpenAIConfig()
