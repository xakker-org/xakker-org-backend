from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CtfMissionStatusChoices, CtfUserMissionStatusChoices, Mission
from .pagination import CtfMissionPagination
from .serializers import (
    FlagSubmitSerializer,
    MissionDetailSerializer,
    MissionListSerializer,
)
from .services import submit_flag, unlock_writeup


def _visible_missions_qs(user):
    qs = Mission.objects.select_related("category").prefetch_related("tags", "writeup", "user_progress")
    if not (user and user.is_authenticated and user.is_staff):
        qs = qs.filter(status=CtfMissionStatusChoices.PUBLISHED)
    return qs


class MissionListView(generics.ListAPIView):
    serializer_class = MissionListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CtfMissionPagination

    def get_queryset(self):
        qs = _visible_missions_qs(self.request.user)
        params = self.request.query_params

        if params.get("difficulty"):
            qs = qs.filter(difficulty=params["difficulty"])
        if params.get("category"):
            qs = qs.filter(category__slug=params["category"])
        if params.get("tag"):
            qs = qs.filter(tags__slug=params["tag"])
        if params.get("search"):
            s = params["search"]
            qs = qs.filter(Q(title__icontains=s) | Q(short_description__icontains=s))

        solved_param = params.get("solved")
        if solved_param is not None:
            solved = solved_param.strip().lower() == "true"
            solved_mission_ids = set(
                Mission.objects.filter(
                    user_progress__user=self.request.user,
                    user_progress__status=CtfUserMissionStatusChoices.SOLVED,
                ).values_list("id", flat=True)
            )
            qs = qs.filter(id__in=solved_mission_ids) if solved else qs.exclude(id__in=solved_mission_ids)

        ordering = params.get("ordering")
        if ordering:
            qs = qs.order_by(ordering)
        else:
            qs = qs.order_by("-created_at")

        return qs.distinct()

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx


class MissionDetailView(generics.RetrieveAPIView):
    serializer_class = MissionDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "slug"

    def get_queryset(self):
        return _visible_missions_qs(self.request.user)

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx


class SubmitFlagView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        mission = get_object_or_404(_visible_missions_qs(request.user), slug=slug)
        serializer = FlagSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = submit_flag(user=request.user, mission=mission, flag=serializer.validated_data["flag"])
        return Response(result, status=status.HTTP_200_OK)


class UnlockWriteupView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        mission = get_object_or_404(_visible_missions_qs(request.user), slug=slug)
        writeup, progress = unlock_writeup(user=request.user, mission=mission)
        if writeup is None:
            return Response({"detail": "Bu missiya üçün writeup yoxdur."}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "unlocked": True,
                "writeup_unlocked_at": progress.writeup_unlocked_at,
                "content": writeup.content,
            },
            status=status.HTTP_200_OK,
        )
