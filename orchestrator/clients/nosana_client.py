import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union
import httpx
from orchestrator.config import settings
from orchestrator.clients.fallback_llm_client import fallback_llm_client, clean_json_response

logger = logging.getLogger("founder0.nosana")

class NosanaClient:
    """
    Nosana Decentralized GPU LLM Inference Client.
    Provides OpenAI-compatible chat completions with structured JSON parsing,
    prompt retries, and automatic fallback switching.

    IMPORTANT: json_mode controls the *actual* parsing behavior, not just the
    prompt wording. When json_mode=False (e.g. MVP_SELF_HEAL_LOOP asking for a
    raw corrected source file), this returns the model's raw text untouched —
    it never runs it through JSON parsing, and never hands back a dict where a
    caller expects a string.
    """

    def __init__(self):
        self.api_key = settings.NOSANA_API_KEY
        self.base_url = settings.NOSANA_BASE_URL.rstrip('/')
        self.model_id = settings.NOSANA_MODEL_ID
        self.mock_mode = settings.MOCK_MODE or not self.api_key

    async def generate_chat(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_mode: bool = True
    ) -> Tuple[Union[Dict[str, Any], str], str]:
        """
        Execute chat completion on Nosana.
        Returns (parsed_json_dict, provider_name) when json_mode=True, or
        (raw_text, provider_name) when json_mode=False.
        If Nosana fails or times out, falls back to fallback_llm_client.
        """
        if self.mock_mode:
            await asyncio.sleep(0.2)
            # Handled by stage-level mock synthesizers or fallback
            return self._mock_generate(prompt, json_mode), "nosana (mock)"

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        user_content = prompt
        if json_mode:
            user_content += "\n\nIMPORTANT: Return ONLY a valid JSON object matching the requested schema. Do NOT include markdown code fences, headers, or conversational prose."

        messages.append({"role": "user", "content": user_content})

        payload = {
            "model": self.model_id,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 3500
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await asyncio.wait_for(
                    client.post(url, headers=headers, json=payload), timeout=32.0
                )
                if res.status_code == 200:
                    data = res.json()
                    raw_content = data["choices"][0]["message"]["content"]

                    if not json_mode:
                        # Plain-text mode: hand the model's output straight back,
                        # no JSON parsing, no repair-retry (there's nothing to repair).
                        return raw_content, "nosana"

                    try:
                        parsed = clean_json_response(raw_content)
                        return parsed, "nosana"
                    except Exception as json_err:
                        logger.warning(f"Nosana output was not valid JSON, retrying once: {json_err}")
                        # 1-retry with repair prompt
                        retry_messages = messages + [
                            {"role": "assistant", "content": raw_content},
                            {"role": "user", "content": "Your previous response was malformed JSON. Please fix it and return ONLY valid JSON."}
                        ]
                        retry_res = await asyncio.wait_for(
                            client.post(url, headers=headers, json={**payload, "messages": retry_messages}),
                            timeout=32.0
                        )
                        if retry_res.status_code == 200:
                            retry_content = retry_res.json()["choices"][0]["message"]["content"]
                            try:
                                return clean_json_response(retry_content), "nosana"
                            except Exception as retry_json_err:
                                logger.warning(f"Nosana retry still not valid JSON, falling back: {retry_json_err}")

                logger.warning(f"Nosana returned status {res.status_code}, falling back.")
        except asyncio.TimeoutError:
            logger.warning("Nosana request hard-timed-out after 32s (network hang), switching to fallback LLM provider.")
        except Exception as e:
            logger.warning(f"Nosana request failed ({e}), switching to fallback LLM provider.")

        # Fallback to secondary provider
        try:
            if json_mode:
                parsed = await asyncio.wait_for(
                    fallback_llm_client.generate_json(prompt, system_prompt), timeout=47.0
                )
                return parsed, f"fallback ({settings.FALLBACK_LLM_PROVIDER})"
            else:
                text = await asyncio.wait_for(
                    fallback_llm_client.generate_text(prompt, system_prompt), timeout=47.0
                )
                return text, f"fallback ({settings.FALLBACK_LLM_PROVIDER})"
        except asyncio.TimeoutError:
            logger.error("Fallback LLM hard-timed-out after 47s, utilizing internal synthesizer.")
            return self._mock_generate(prompt, json_mode), "internal_synthesizer"
        except Exception as fallback_err:
            logger.error(f"Fallback LLM failed ({fallback_err}), utilizing internal synthesizer.")
            return self._mock_generate(prompt, json_mode), "internal_synthesizer"

    def _mock_generate(self, prompt: str, json_mode: bool = True) -> Union[Dict[str, Any], str]:
        """Internal deterministic synthesizer for offline development and testing."""
        if json_mode:
            return {"status": "success", "synthetic": True}
        # Text mode (e.g. self-heal repair) must return a string, never a dict —
        # a caller writing this straight to a source file needs real text back.
        return ""

nosana_client = NosanaClient()