from django.db import transaction
from rest_framework import serializers

from ctf.models import Mission, MissionCategory, MissionTag, UserMissionProgress, Writeup

from .base import AutoSlugMixin


class MissionCategoryAdminSerializer(AutoSlugMixin, serializers.ModelSerializer):
    slug_source_field = "name"

    class Meta:
        model = MissionCategory
        fields = "__all__"


class MissionTagAdminSerializer(AutoSlugMixin, serializers.ModelSerializer):
    slug_source_field = "name"

    class Meta:
        model = MissionTag
        fields = "__all__"


class WriteupNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Writeup
        fields = ["content", "is_locked_by_default"]


class CtfMissionAdminSerializer(AutoSlugMixin, serializers.ModelSerializer):
    slug_source_field = "title"

    tags = serializers.PrimaryKeyRelatedField(queryset=MissionTag.objects.all(), many=True, required=False)
    writeup = WriteupNestedSerializer(required=False, allow_null=True)
    flag = serializers.CharField(write_only=True, required=False, allow_blank=True)
    has_flag = serializers.SerializerMethodField()

    class Meta:
        model = Mission
        fields = [
            "id", "title", "slug", "difficulty", "category", "tags",
            "short_description", "description", "connection_info",
            "points", "estimated_time", "status", "created_at", "updated_at",
            "writeup", "flag", "has_flag",
        ]

    def get_has_flag(self, obj):
        return obj.has_flag

    def _extract(self, validated_data):
        flag = validated_data.pop("flag", None)
        writeup_data = validated_data.pop("writeup", None)
        return flag, writeup_data

    def _upsert_writeup(self, mission, writeup_data):
        if writeup_data is None:
            return
        Writeup.objects.update_or_create(mission=mission, defaults=writeup_data)
        # The viewset's queryset uses select_related("writeup"), which caches
        # the reverse one-to-one on the instance at fetch time (before this
        # upsert runs). Clear that cache so to_representation() re-fetches
        # the just-written row instead of serializing stale data.
        mission._state.fields_cache.pop("writeup", None)

    @transaction.atomic
    def create(self, validated_data):
        flag, writeup_data = self._extract(validated_data)
        instance = super().create(validated_data)
        if flag:
            instance.set_flag(flag)
            instance.save(update_fields=["flag_hash"])
        self._upsert_writeup(instance, writeup_data)
        return instance

    @transaction.atomic
    def update(self, instance, validated_data):
        flag, writeup_data = self._extract(validated_data)
        instance = super().update(instance, validated_data)
        if flag:
            instance.set_flag(flag)
            instance.save(update_fields=["flag_hash"])
        self._upsert_writeup(instance, writeup_data)
        return instance


class CtfMissionProgressAdminSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    mission_title = serializers.CharField(source="mission.title", read_only=True)

    class Meta:
        model = UserMissionProgress
        fields = ["id", "username", "mission_title", "status", "flag_attempts", "solved_at", "writeup_unlocked_at"]
