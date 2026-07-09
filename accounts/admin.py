from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import Activity, UserProfile

User = get_user_model()

admin.site.unregister(User)


@admin.register(User)
class StaffUserAdmin(BaseUserAdmin):
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=True)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.is_staff = True
        super().save_model(request, obj, form, change)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Regular registered users only — staff/superuser accounts have their own
    section under Authentication and Authorization → Users (see StaffUserAdmin)."""

    list_display  = ("user", "xp_display", "rank", "streak_days", "tasks_completed", "rooms_completed", "best_streak")
    list_filter   = ("rank",)
    search_fields = ("user__username", "user__email")
    readonly_fields = ("user", "xp", "rank", "streak_days", "best_streak", "tasks_completed", "rooms_completed", "last_activity")
    ordering      = ("-xp",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(user__is_staff=False, user__is_superuser=False)
    fieldsets = (
        ("İstifadəçi", {"fields": ("user",)}),
        ("Gamification", {"fields": ("xp", "rank", "streak_days", "best_streak")}),
        ("Statistika", {"fields": ("tasks_completed", "rooms_completed", "last_activity")}),
    )

    def delete_model(self, request, obj):
        obj.user.delete()

    def delete_queryset(self, request, queryset):
        user_ids = list(queryset.values_list("user_id", flat=True))
        User.objects.filter(id__in=user_ids).delete()

    @admin.display(description="XP", ordering="xp")
    def xp_display(self, obj):
        return format_html('<strong style="color:#ff8099">★ {}</strong>', obj.xp)


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    """Regular registered users' activity only — see UserProfileAdmin note above."""

    list_display  = ("user", "kind_badge", "title", "xp_delta_display", "created_at")
    list_filter   = ("kind",)
    search_fields = ("user__username", "title")
    readonly_fields = ("user", "kind", "title", "detail", "xp_delta", "created_at")
    date_hierarchy  = "created_at"
    ordering        = ("-created_at",)

    def get_queryset(self, request):
        return super().get_queryset(request).filter(user__is_staff=False, user__is_superuser=False)

    def has_add_permission(self, _request): return False
    def has_change_permission(self, _request, _obj=None): return False

    @admin.display(description="Tip")
    def kind_badge(self, obj):
        colors = {
            "task_complete": "#4ce0a5",
            "room_complete": "#5b8bff",
            "badge_earned":  "#ffb86b",
            "rank_up":       "#ff5672",
            "exam_submit":   "#9d7bff",
        }
        color = colors.get(obj.kind, "#8690a8")
        return format_html('<span style="color:{};font-weight:700">{}</span>', color, obj.kind)

    @admin.display(description="XP")
    def xp_delta_display(self, obj):
        if obj.xp_delta > 0:
            return format_html('<span style="color:#4ce0a5;font-weight:700">+{}</span>', obj.xp_delta)
        if obj.xp_delta < 0:
            return format_html('<span style="color:#ff5672">{}</span>', obj.xp_delta)
        return "—"
