"""
Thin wrapper around the Anthropic Claude API used by the agents.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

import google.generativeai as genai
from anthropic import AsyncAnthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings

logger = logging.getLogger(__name__)

_claude_client: AsyncAnthropic | None = None
_gemini_configured: bool = False


def get_claude_client() -> AsyncAnthropic:
    global _claude_client
    if _claude_client is None:
        settings = get_settings()
        _claude_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _claude_client


def configure_gemini() -> None:
    global _gemini_configured
    if not _gemini_configured:
        settings = get_settings()
        genai.configure(api_key=settings.gemini_api_key)
        _gemini_configured = True


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
async def call_claude(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 2000,
    temperature: float = 0.2,
) -> str:
    """Call LLM (Claude or Gemini) and return the raw text response."""
    settings = get_settings()
    if settings.llm_provider.lower() == "gemini":
        configure_gemini()
        model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            system_instruction=system_prompt,
        )
        response = await model.generate_content_async(
            user_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                response_mime_type="application/json",
            )
        )
        return response.text
    else:
        client = get_claude_client()
        response = await client.messages.create(
            model=settings.claude_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        parts = []
        for block in response.content:
            if block.type == "text":
                parts.append(block.text)
        return "".join(parts)


def extract_json(text: str) -> Any:
    """Extract a JSON object/array from a Claude response that may include extra prose."""
    text = text.strip()
    # Strip markdown code fences if present
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fallback: find first balanced JSON object/array in the text
    for open_ch, close_ch in (("{", "}"), ("[", "]")):
        start = text.find(open_ch)
        if start == -1:
            continue
        depth = 0
        for i in range(start, len(text)):
            if text[i] == open_ch:
                depth += 1
            elif text[i] == close_ch:
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break
    logger.error("Failed to extract JSON from Claude response: %s", text[:500])
    raise ValueError("Could not parse JSON from Claude response")
