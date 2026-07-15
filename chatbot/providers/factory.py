from decouple import config

from .base import ProviderError


def get_provider():
    """Return the configured AI provider adapter.

    Reads AI_PROVIDER from .env (default "groq"). Adding a new provider
    (openai/anthropic/...) = new adapter file in this package + a branch
    here — no call-site changes needed.
    """
    provider_name = config("AI_PROVIDER", default="groq").strip().lower()

    if provider_name == "groq":
        from .groq_provider import GroqProvider
        return GroqProvider()

    raise ProviderError(f"Unknown AI_PROVIDER '{provider_name}'.")
