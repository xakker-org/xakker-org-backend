class ProviderError(Exception):
    """Raised when the AI provider is misconfigured or the upstream call fails.

    Views must catch this and return a 503 with a friendly `detail` — never
    let it bubble up into a 500 stacktrace.
    """


class BaseAIProvider:
    """Common interface all AI provider adapters must implement."""

    def chat(self, messages: list[dict], lang: str) -> str:
        """
        messages: list of {"role": "system"|"user"|"assistant", "content": str}
        lang: "az" | "en" — informational, the system prompt already encodes it.
        Returns the assistant's reply text.
        Raises ProviderError on misconfiguration or upstream failure.
        """
        raise NotImplementedError
