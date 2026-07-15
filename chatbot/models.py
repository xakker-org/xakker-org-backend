from django.conf import settings
from django.db import models


class Conversation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chatbot_conversations",
    )
    title = models.CharField(max_length=64, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return self.title or f"Conversation #{self.pk}"


class MessageRole(models.TextChoices):
    USER = "user", "User"
    ASSISTANT = "assistant", "Assistant"
    SYSTEM = "system", "System"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=16, choices=MessageRole.choices)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:40]}"


class AssistantPromptSettings(models.Model):
    base_prompt_az = models.TextField(blank=True, default="")
    base_prompt_en = models.TextField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Assistant Prompt Settings"
        verbose_name_plural = "Assistant Prompt Settings"

    def __str__(self):
        return "Xakker AI — Base Prompt"

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class AssistantPromptNoteLang(models.TextChoices):
    AZ = "az", "Azərbaycan"
    EN = "en", "English"
    BOTH = "both", "Both"


class AssistantPromptNote(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    lang = models.CharField(
        max_length=8, choices=AssistantPromptNoteLang.choices, default=AssistantPromptNoteLang.BOTH
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "Assistant Prompt Note"
        verbose_name_plural = "Assistant Prompt Notes"

    def __str__(self):
        return self.title


class ChatbotKnowledge(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.CharField(max_length=100, blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "title"]
        verbose_name = "Chatbot Knowledge"
        verbose_name_plural = "Chatbot Knowledge"

    def __str__(self):
        return self.title
