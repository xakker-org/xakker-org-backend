from django.contrib import admin

from .models import (
    AssistantPromptNote,
    AssistantPromptSettings,
    ChatbotKnowledge,
    Conversation,
    Message,
)


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    fields = ("role", "content", "created_at")
    readonly_fields = ("role", "content", "created_at")
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "created_at", "updated_at", "message_count")
    list_filter = ("created_at",)
    search_fields = ("title", "user__username")
    readonly_fields = ("created_at", "updated_at")
    inlines = [MessageInline]
    date_hierarchy = "created_at"

    @admin.display(description="Mesajlar")
    def message_count(self, obj):
        return obj.messages.count()


@admin.register(AssistantPromptSettings)
class AssistantPromptSettingsAdmin(admin.ModelAdmin):
    readonly_fields = ("updated_at",)
    fieldsets = (
        ("Azərbaycan", {"fields": ("base_prompt_az",)}),
        ("English", {"fields": ("base_prompt_en",)}),
        ("Məlumat", {"fields": ("updated_at",)}),
    )

    def has_add_permission(self, request):
        return not AssistantPromptSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        for field_name in ("base_prompt_az", "base_prompt_en"):
            if field_name in form.base_fields:
                form.base_fields[field_name].widget.attrs.update({"rows": 20, "style": "font-family: monospace;"})
        return form


@admin.register(AssistantPromptNote)
class AssistantPromptNoteAdmin(admin.ModelAdmin):
    list_display = ("title", "lang", "is_active", "order")
    list_filter = ("lang", "is_active")
    search_fields = ("title", "content")
    list_editable = ("is_active", "order")
    fieldsets = (
        ("Əsas məlumatlar", {"fields": ("title", "lang", "is_active", "order")}),
        ("Məzmun", {
            "fields": ("content",),
            "description": "Bu mətn AI Köməkçinin sistem promptuna əlavə təlimat kimi əlavə olunur.",
        }),
    )


@admin.register(ChatbotKnowledge)
class ChatbotKnowledgeAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_active", "updated_at")
    list_filter = ("category", "is_active")
    search_fields = ("title", "content", "category")
    list_editable = ("is_active",)
    fieldsets = (
        ("Əsas məlumatlar", {"fields": ("title", "category", "is_active")}),
        ("Məzmun", {
            "fields": ("content",),
            "description": "Bu mətn AI Köməkçinin sistem promptuna əlavə olunur — kod dəyişikliyi tələb etmir.",
        }),
    )
