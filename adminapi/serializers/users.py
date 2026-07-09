from django.contrib.auth.models import User
from rest_framework import serializers


class AdminUserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="profile.full_name", required=False, allow_blank=True)
    bio = serializers.CharField(source="profile.bio", required=False, allow_blank=True)
    country = serializers.CharField(source="profile.country", required=False, allow_blank=True)
    city = serializers.CharField(source="profile.city", required=False, allow_blank=True)
    xp = serializers.IntegerField(source="profile.xp", read_only=True)
    rank = serializers.CharField(source="profile.rank", read_only=True)
    streak_days = serializers.IntegerField(source="profile.streak_days", read_only=True)
    best_streak = serializers.IntegerField(source="profile.best_streak", read_only=True)
    tasks_completed = serializers.IntegerField(source="profile.tasks_completed", read_only=True)
    rooms_completed = serializers.IntegerField(source="profile.rooms_completed", read_only=True)
    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "is_active", "is_staff", "is_superuser", "date_joined",
            "full_name", "bio", "country", "city",
            "xp", "rank", "streak_days", "best_streak", "tasks_completed", "rooms_completed",
            "avatar_url",
        ]
        # is_staff/is_superuser only change through the set_staff action (superuser-gated) —
        # never accept them here, or any staff member could self-escalate via a plain PATCH.
        read_only_fields = ["username", "date_joined", "is_staff", "is_superuser"]

    def get_avatar_url(self, obj):
        avatar = getattr(obj.profile, "avatar", None)
        if not avatar:
            return None
        try:
            url = avatar.url
        except Exception:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})
        instance = super().update(instance, validated_data)
        if profile_data:
            profile = instance.profile
            for key, value in profile_data.items():
                setattr(profile, key, value)
            profile.save(update_fields=list(profile_data.keys()))
        return instance


class ToggleSerializer(serializers.Serializer):
    value = serializers.BooleanField()


class AwardXpSerializer(serializers.Serializer):
    amount = serializers.IntegerField(min_value=1)
