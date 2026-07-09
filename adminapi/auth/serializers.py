from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from adminapi.permissions import ADMIN_TOKEN_SCOPE


class AdminTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Mirror of accounts.ClientTokenObtainPairSerializer, inverted: only
    staff may obtain an admin-scoped token."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["scope"] = ADMIN_TOKEN_SCOPE
        token["is_staff"] = user.is_staff
        token["is_superuser"] = user.is_superuser
        token["username"] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_staff:
            raise serializers.ValidationError("Bu hesabın admin panelinə girişi yoxdur.")
        data["is_staff"] = self.user.is_staff
        data["is_superuser"] = self.user.is_superuser
        data["username"] = self.user.username
        return data


class AdminMeSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="user.id")
    username = serializers.CharField(source="user.username")
    email = serializers.CharField(source="user.email")
    is_staff = serializers.BooleanField(source="user.is_staff")
    is_superuser = serializers.BooleanField(source="user.is_superuser")
    full_name = serializers.CharField()
    avatar_hue = serializers.IntegerField()
    xp = serializers.IntegerField()
    rank = serializers.CharField()
