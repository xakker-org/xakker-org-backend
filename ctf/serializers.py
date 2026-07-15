from rest_framework import serializers

from .models import CtfUserMissionStatusChoices, Mission, MissionCategory, MissionTag


class MissionCategoryMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = MissionCategory
        fields = ["name", "slug"]


class MissionTagMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = MissionTag
        fields = ["name", "slug"]


class _UserContextMixin:
    def _progress_for(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None
        return obj.user_progress.filter(user=user).first()


class MissionListSerializer(_UserContextMixin, serializers.ModelSerializer):
    category = MissionCategoryMiniSerializer(read_only=True)
    tags = MissionTagMiniSerializer(many=True, read_only=True)
    solved_count = serializers.SerializerMethodField()
    user_status = serializers.SerializerMethodField()
    writeup_available = serializers.SerializerMethodField()

    class Meta:
        model = Mission
        fields = [
            "id", "title", "slug", "difficulty", "category", "tags",
            "short_description", "points", "estimated_time",
            "solved_count", "user_status", "writeup_available",
        ]

    def get_solved_count(self, obj):
        return obj.user_progress.filter(status=CtfUserMissionStatusChoices.SOLVED).count()

    def get_user_status(self, obj):
        progress = self._progress_for(obj)
        return progress.status if progress else CtfUserMissionStatusChoices.NOT_STARTED

    def get_writeup_available(self, obj):
        return getattr(obj, "writeup", None) is not None


class WriteupInlineSerializer(serializers.Serializer):
    exists = serializers.BooleanField()
    is_locked_by_default = serializers.BooleanField()
    unlocked = serializers.BooleanField()
    content = serializers.CharField(allow_null=True)


class MissionDetailSerializer(_UserContextMixin, serializers.ModelSerializer):
    category = MissionCategoryMiniSerializer(read_only=True)
    tags = MissionTagMiniSerializer(many=True, read_only=True)
    solved_count = serializers.SerializerMethodField()
    user_status = serializers.SerializerMethodField()
    flag_attempts = serializers.SerializerMethodField()
    solved_at = serializers.SerializerMethodField()
    writeup = serializers.SerializerMethodField()

    class Meta:
        model = Mission
        fields = [
            "id", "title", "slug", "difficulty", "category", "tags",
            "short_description", "description", "connection_info",
            "points", "estimated_time", "solved_count",
            "user_status", "flag_attempts", "solved_at", "writeup",
        ]

    def get_solved_count(self, obj):
        return obj.user_progress.filter(status=CtfUserMissionStatusChoices.SOLVED).count()

    def get_user_status(self, obj):
        progress = self._progress_for(obj)
        return progress.status if progress else CtfUserMissionStatusChoices.NOT_STARTED

    def get_flag_attempts(self, obj):
        progress = self._progress_for(obj)
        return progress.flag_attempts if progress else 0

    def get_solved_at(self, obj):
        progress = self._progress_for(obj)
        return progress.solved_at if progress else None

    def get_writeup(self, obj):
        writeup = getattr(obj, "writeup", None)
        if writeup is None:
            return {"exists": False, "is_locked_by_default": True, "unlocked": False, "content": None}

        progress = self._progress_for(obj)
        unlocked = False
        if progress is not None:
            unlocked = progress.writeup_unlocked
        elif not writeup.is_locked_by_default:
            unlocked = True

        return {
            "exists": True,
            "is_locked_by_default": writeup.is_locked_by_default,
            "unlocked": unlocked,
            "content": writeup.content if unlocked else None,
        }


class FlagSubmitSerializer(serializers.Serializer):
    flag = serializers.CharField(allow_blank=False, trim_whitespace=False)
