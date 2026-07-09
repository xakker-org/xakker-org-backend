from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from adminapi.permissions import IsStaffUser

from .serializers import AdminMeSerializer, AdminTokenObtainPairSerializer


class AdminLoginThrottle(AnonRateThrottle):
    scope = "admin_login"


class AdminTokenObtainPairView(TokenObtainPairView):
    serializer_class = AdminTokenObtainPairSerializer
    throttle_classes = [AdminLoginThrottle]


class AdminMeView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        profile = request.user.profile
        return Response(AdminMeSerializer(profile).data)
