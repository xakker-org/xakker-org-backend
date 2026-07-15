from django import forms
from django.contrib import admin
from django.utils.html import format_html

from .models import Mission, MissionCategory, MissionTag, UserMissionProgress, Writeup


class ReadOnlyAdminMixin:
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MissionCategory)
class MissionCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(MissionTag)
class MissionTagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


class WriteupInline(admin.StackedInline):
    model = Writeup
    extra = 0
    max_num = 1
    fields = ("content", "is_locked_by_default")


class MissionAdminForm(forms.ModelForm):
    """Adds a write-only `flag` field that hashes into `flag_hash` on save.
    The stored hash is never shown back in the form."""

    flag = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "xkr{...} — yalnız yazmaq üçün, saxlanılan flag göstərilmir"}),
        help_text="Yeni flag daxil edin ki, mövcud flag üzərinə yazılsın. Boş saxlasanız mövcud flag dəyişməz.",
        label="Flag",
    )

    class Meta:
        model = Mission
        exclude = ("flag_hash",)

    def save(self, commit=True):
        instance = super().save(commit=False)
        plaintext = self.cleaned_data.get("flag")
        if plaintext:
            instance.set_flag(plaintext)
        if commit:
            instance.save()
            self.save_m2m()
        return instance


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    form = MissionAdminForm
    list_display = ("title", "difficulty", "category", "status_badge", "points", "has_flag_badge", "estimated_time")
    list_filter = ("difficulty", "status", "category")
    search_fields = ("title", "short_description")
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("tags",)
    inlines = [WriteupInline]
    save_on_top = True
    fieldsets = (
        ("Əsas", {"fields": ("title", "slug", "difficulty", "category", "tags", "status")}),
        ("Təsvir (Markdown)", {"fields": ("short_description", "description", "connection_info")}),
        ("Xal / Vaxt", {"fields": ("points", "estimated_time")}),
        ("Flag", {"fields": ("flag",), "description": "Flag heş formasında saxlanılır, heç vaxt geri göstərilmir."}),
    )

    @admin.display(description="Status")
    def status_badge(self, obj):
        color = "#22c55e" if obj.status == "published" else "#94a3b8"
        return format_html('<span style="color:{};font-weight:700">{}</span>', color, obj.get_status_display())

    @admin.display(description="Flag")
    def has_flag_badge(self, obj):
        if obj.has_flag:
            return format_html('<span style="color:#ff3b3b;font-weight:700">🚩 var</span>')
        return format_html('<span style="color:#94a3b8">yoxdur</span>')


@admin.register(UserMissionProgress)
class UserMissionProgressAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("user", "mission", "status", "flag_attempts", "solved_at", "writeup_unlocked_at")
    list_filter = ("status",)
    search_fields = ("user__username", "mission__title")
