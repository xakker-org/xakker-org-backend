from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Activity, UserProfile
from courses.models import (
    Course,
    Lesson,
    Mission,
    MissionExamAttempt,
    Question,
    QuestionAttempt,
    Room,
    UserTaskProgress,
)

from adminapi.permissions import IsStaffUser


class AnalyticsOverviewView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        now = timezone.now()
        d7 = now - timedelta(days=7)
        d30 = now - timedelta(days=30)

        return Response({
            "users": {
                "total": User.objects.count(),
                "new_7d": User.objects.filter(date_joined__gte=d7).count(),
                "new_30d": User.objects.filter(date_joined__gte=d30).count(),
                "active_7d": UserProfile.objects.filter(last_activity__gte=d7).count(),
            },
            "xp": {
                "total_awarded": UserProfile.objects.aggregate(total=Sum("xp"))["total"] or 0,
            },
            "content": {
                "courses": Course.objects.count(),
                "rooms": Room.objects.count(),
                "missions": Mission.objects.count(),
                "questions": Question.objects.count(),
                "lessons": Lesson.objects.count(),
            },
        })


class AnalyticsContentView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        top_questions = list(
            QuestionAttempt.objects.values("question__title")
            .annotate(attempts=Count("id"))
            .order_by("-attempts")[:10]
        )
        rooms_by_completed_tasks = list(
            UserTaskProgress.objects.filter(completed=True)
            .values("task__room__title")
            .annotate(completed=Count("id"))
            .order_by("-completed")[:10]
        )
        exam_stats = MissionExamAttempt.objects.aggregate(
            avg_score=Avg("score"),
            passed_count=Count("id", filter=Q(passed=True)),
            failed_count=Count("id", filter=Q(passed=False)),
        )

        return Response({
            "top_questions": top_questions,
            "rooms_by_completed_tasks": rooms_by_completed_tasks,
            "exam_stats": exam_stats,
        })


class AnalyticsActivityView(APIView):
    permission_classes = [IsAuthenticated, IsStaffUser]

    def get(self, request):
        try:
            days = int(request.query_params.get("days", 30))
        except ValueError:
            days = 30
        days = max(1, min(days, 365))
        cutoff = timezone.now() - timedelta(days=days)

        signups = list(
            User.objects.filter(date_joined__gte=cutoff)
            .annotate(d=TruncDate("date_joined"))
            .values("d")
            .annotate(count=Count("id"))
            .order_by("d")
        )
        activity = list(
            Activity.objects.filter(created_at__gte=cutoff)
            .annotate(d=TruncDate("created_at"))
            .values("d")
            .annotate(count=Count("id"))
            .order_by("d")
        )

        return Response({"days": days, "signups": signups, "activity": activity})
