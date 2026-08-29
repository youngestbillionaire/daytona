import json
import logging
import re
from typing import Any, Dict, Optional
import httpx
from orchestrator.config import settings

logger = logging.getLogger("founder0.fallback_llm")

def clean_json_response(raw_text: str) -> Dict[str, Any]:
    """Clean markdown code fences and extract valid JSON."""
    cleaned = raw_text.strip()
    # Remove markdown code blocks like ```json ... ```
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"```\s*$", "", cleaned, flags=re.MULTILINE)
    cleaned = cleaned.strip()
    return json.loads(cleaned)

class FallbackLLMClient:
    """
    Fallback LLM provider supporting Anthropic, OpenAI, or Ollama
    when Nosana is unavailable or times out.
    """

    def __init__(self):
        self.provider = settings.FALLBACK_LLM_PROVIDER.lower()
        self.api_key = settings.FALLBACK_LLM_API_KEY
        self.model = settings.FALLBACK_LLM_MODEL
        self.mock_mode = settings.MOCK_MODE or not self.api_key

    async def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Generate structured JSON completion via fallback provider."""
        if self.mock_mode:
            logger.info("Using mock generation for fallback LLM")
            return {"status": "mock", "prompt": prompt[:50]}

        if self.provider == "anthropic":
            return await self._generate_anthropic(prompt, system_prompt)
        else:
            return await self._generate_openai(prompt, system_prompt)

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a raw text completion via fallback provider (no JSON parsing)."""
        if self.mock_mode:
            logger.info("Using mock generation for fallback LLM (text mode)")
            return prompt[:50]

        if self.provider == "anthropic":
            return await self._generate_anthropic(prompt, system_prompt, as_json=False)
        else:
            return await self._generate_openai(prompt, system_prompt, as_json=False)

    async def _generate_openai(self, prompt: str, system_prompt: Optional[str] = None, as_json: bool = True):
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model or "gpt-4o",
            "messages": messages,
            "temperature": 0.3
        }
        if as_json:
            payload["response_format"] = {"type": "json_object"}

        async with httpx.AsyncClient(timeout=45.0) as client:
            res = await client.post(url, headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()
            content = data["choices"][0]["message"]["content"]
            return clean_json_response(content) if as_json else content

    async def _generate_anthropic(self, prompt: str, system_prompt: Optional[str] = None, as_json: bool = True):
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key or "",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": self.model or "claude-3-5-sonnet-20241022",
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=45.0) as client:
            res = await client.post(url, headers=headers, json=payload)
            res.raise_for_status()
            data = res.json()
            content = data["content"][0]["text"]
            return clean_json_response(content) if as_json else content

fallback_llm_client = FallbackLLMClient()
