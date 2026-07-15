import httpx
from decouple import config

from .base import BaseAIProvider, ProviderError

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


class GroqProvider(BaseAIProvider):
    def __init__(self):
        self.api_key = config("GROQ_API_KEY", default="")

    def chat(self, messages: list[dict], lang: str) -> str:
        if not self.api_key:
            raise ProviderError("AI provider is not configured (missing GROQ_API_KEY).")

        try:
            response = httpx.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "temperature": 0.4,
                    "max_tokens": 1024,
                },
                timeout=30.0,
            )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise ProviderError("AI provider timed out. Please try again.") from exc
        except httpx.HTTPStatusError as exc:
            raise ProviderError("AI provider returned an error. Please try again later.") from exc
        except httpx.HTTPError as exc:
            raise ProviderError("Could not reach the AI provider. Please try again later.") from exc

        try:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, ValueError) as exc:
            raise ProviderError("AI provider returned an unexpected response.") from exc
