"""One function, two providers. OpenRouter first, Anthropic second, None means extractive mode."""

from __future__ import annotations

import json
import logging
import re

import httpx

from .config import Settings, settings as default_settings

log = logging.getLogger("brain.llm")


class LLMError(RuntimeError):
    pass


def available(settings: Settings | None = None) -> bool:
    settings = settings or default_settings
    return bool(settings.openrouter_api_key or settings.anthropic_api_key)


async def complete(system: str, user: str, settings: Settings | None = None, max_tokens: int = 1200) -> str | None:
    """Returns the model's text, or None when no provider is configured."""
    settings = settings or default_settings
    if settings.openrouter_api_key:
        return await _openrouter(system, user, settings, max_tokens)
    if settings.anthropic_api_key:
        return await _anthropic(system, user, settings, max_tokens)
    return None


async def _openrouter(system: str, user: str, settings: Settings, max_tokens: int) -> str:
    async with httpx.AsyncClient(timeout=settings.llm_timeout_s) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "authorization": f"Bearer {settings.openrouter_api_key}",
                "content-type": "application/json",
                "x-title": "Company Brain",
            },
            json={
                "model": settings.openrouter_model,
                "max_tokens": max_tokens,
                "temperature": 0.2,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            },
        )
    if response.status_code != 200:
        raise LLMError(f"openrouter {response.status_code}: {response.text[:300]}")
    data = response.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMError(f"openrouter reply unreadable: {exc}") from exc


async def _anthropic(system: str, user: str, settings: Settings, max_tokens: int) -> str:
    async with httpx.AsyncClient(timeout=settings.llm_timeout_s) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": settings.anthropic_model,
                "max_tokens": max_tokens,
                "temperature": 0.2,
                "system": system,
                "messages": [{"role": "user", "content": user}],
            },
        )
    if response.status_code != 200:
        raise LLMError(f"anthropic {response.status_code}: {response.text[:300]}")
    data = response.json()
    parts = [block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"]
    if not parts:
        raise LLMError("anthropic reply had no text")
    return "".join(parts)


def extract_json(text: str) -> dict | None:
    """Finds the first JSON object in a model reply, tolerating code fences and prose around it."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidates = [fence.group(1)] if fence else []
    start = text.find("{")
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    candidates.append(text[start:i + 1])
                    break
    for candidate in candidates:
        try:
            data = json.loads(candidate)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            continue
    return None
