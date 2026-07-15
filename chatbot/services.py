from .models import Message, MessageRole
from .prompt import build_system_prompt
from .providers.factory import get_provider

HISTORY_LIMIT = 20  # most recent messages to feed back as context


def generate_reply(conversation, lang: str) -> str:
    """Build the message list (system prompt + recent history) and call the
    configured AI provider. Raises ProviderError on failure (caller -> 503).
    """
    provider = get_provider()

    system_prompt = build_system_prompt(lang)
    history = list(
        conversation.messages.order_by("-created_at")[:HISTORY_LIMIT]
    )[::-1]

    messages = [{"role": "system", "content": system_prompt}]
    messages += [
        {"role": m.role, "content": m.content}
        for m in history
        if m.role in (MessageRole.USER, MessageRole.ASSISTANT)
    ]

    return provider.chat(messages, lang)
