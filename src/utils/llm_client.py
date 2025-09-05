from __future__ import annotations

import os
from typing import Optional, List, Dict
import requests


class LLMClient:
    def __init__(self, provider: str = "openrouter", model: Optional[str] = None) -> None:
        self.provider = provider
        self.model = model or os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini")
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY")

    def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None, temperature: float = 0.3, max_tokens: int = 400) -> str:
        model_id = model or self.model
        if self.provider != "openrouter":
            raise RuntimeError("Only openrouter provider is supported in minimal version")
        if not self.openrouter_key:
            raise RuntimeError("OPENROUTER_API_KEY not set")
        headers = {
            "Authorization": f"Bearer {self.openrouter_key}",
            "HTTP-Referer": "https://agentic-safety-minimal/",
            "X-Title": "agentic-safety-minimal",
        }
        data = {"model": model_id, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
        r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=60)
        r.raise_for_status()
        j = r.json()
        content = j["choices"][0]["message"]["content"]
        if not content:
            raise RuntimeError(f"Empty response from model {model_id}")
        return content
