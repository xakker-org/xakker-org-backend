import logging
import secrets
from calendar import monthrange
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import generics
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

logger = logging.getLogger(__name__)


class LoginThrottle(AnonRateThrottle):
    scope = "login"


class RegisterThrottle(AnonRateThrottle):
    scope = "register"


class PasswordResetThrottle(AnonRateThrottle):
    scope = "password_reset"

from .models import Activity, PasswordResetCode, UserProfile
from .serializers import (
    ActivitySerializer,
    ClientTokenObtainPairSerializer,
    LeaderboardEntrySerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PasswordResetVerifySerializer,
    RegisterSerializer,
    UserProfileSerializer,
)


def _check_reset_code(email, submitted_code):
    """Validate a reset code without consuming it. Increments attempts on mismatch.
    Returns (user, reset_code) on success, otherwise (None, None)."""
    user = User.objects.filter(email__iexact=email, is_staff=False, is_superuser=False).first()
    if not user:
        return None, None

    reset_code = PasswordResetCode.objects.filter(user=user, used=False).order_by("-created_at").first()
    if not reset_code or not reset_code.is_valid():
        return None, None

    if not secrets.compare_digest(reset_code.code, submitted_code):
        reset_code.attempts += 1
        reset_code.save(update_fields=["attempts"])
        return None, None

    return user, reset_code


class ClientTokenObtainPairView(TokenObtainPairView):
    serializer_class = ClientTokenObtainPairSerializer
    throttle_classes = [LoginThrottle]


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    throttle_classes = [RegisterThrottle]


class PasswordResetRequestView(APIView):
    throttle_classes = [PasswordResetThrottle]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.filter(email__iexact=email, is_staff=False, is_superuser=False).first()
        if not user:
            logger.warning("Password reset requested for an email with no matching account: %s", email)
            return Response({"detail": "No account is registered with this email."}, status=404)

        reset_code = PasswordResetCode.issue_for(user)
        try:
            send_mail(
                subject="Xakker — şifrə bərpa kodu / password reset code",
                message=(
                    f"Salam {user.username},\n\n"
                    f"Şifrəni bərpa etmək üçün kodun: {reset_code.code}\n"
                    f"Bu kod {PasswordResetCode.CODE_TTL_MINUTES} dəqiqə etibarlıdır.\n"
                    "Bu sorğunu sən etməmisənsə, bu e-poçtu nəzərə alma.\n\n"
                    "---\n\n"
                    f"Hi {user.username},\n\n"
                    f"Your Xakker password reset code is: {reset_code.code}\n"
                    f"This code expires in {PasswordResetCode.CODE_TTL_MINUTES} minutes.\n"
                    "If you didn't request this, you can safely ignore this email."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            logger.warning("Password reset email sent to user id=%s", user.id)
        except Exception:
            logger.exception("Password reset email failed to send for user id=%s", user.id)
            return Response({"detail": "Couldn't send the email. Please try again shortly."}, status=502)

        return Response({"detail": "A reset code has been sent to your email."})


class PasswordResetVerifyView(APIView):
    """Checks a code without consuming it, so the UI can move to the 'set new password' step."""

    throttle_classes = [PasswordResetThrottle]

    def post(self, request):
        serializer = PasswordResetVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, _ = _check_reset_code(serializer.validated_data["email"], serializer.validated_data["code"])
        if not user:
            return Response({"detail": "Invalid or expired code."}, status=400)
        return Response({"detail": "Code verified."})


class PasswordResetConfirmView(APIView):
    throttle_classes = [PasswordResetThrottle]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, reset_code = _check_reset_code(serializer.validated_data["email"], serializer.validated_data["code"])
        if not user:
            return Response({"detail": "Invalid or expired code."}, status=400)

        reset_code.used = True
        reset_code.save(update_fields=["used"])

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Password has been reset successfully."})


class MeView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return Response(
            {
                "id": request.user.id,
                "username": request.user.username,
                "email": request.user.email,
                "is_staff": request.user.is_staff,
                "is_superuser": request.user.is_superuser,
                "account_type": "admin" if request.user.is_staff or request.user.is_superuser else "client",
                "profile": UserProfileSerializer(profile, context={"request": request}).data,
            }
        )


class MyProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return Response(UserProfileSerializer(profile, context={"request": request}).data)

    def patch(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        payload = request.data.copy() if hasattr(request.data, "copy") else dict(request.data)

        remove_avatar = str(payload.pop("remove_avatar", "")).lower() in {"1", "true", "yes", "on"}
        if remove_avatar and profile.avatar:
            profile.avatar.delete(save=False)
            profile.avatar = None
            profile.save(update_fields=["avatar"])

        email_val = payload.pop("email", None)
        if email_val:
            if isinstance(email_val, list):
                email_val = email_val[0]
            email_val = str(email_val).strip()
            if email_val:
                request.user.email = email_val
                request.user.save(update_fields=["email"])

        serializer = UserProfileSerializer(profile, data=payload, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PublicProfileView(APIView):
    def get(self, request, username):
        try:
            user = User.objects.get(username__iexact=username, is_staff=False, is_superuser=False)
        except User.DoesNotExist:
            return Response({"detail": "Profile not found."}, status=404)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        data = UserProfileSerializer(profile, context={"request": request}).data
        data.pop("email", None)
        activity = Activity.objects.filter(user=user)[:20]
        data["activity"] = ActivitySerializer(activity, many=True).data
        return Response(data)


class MyActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = int(request.query_params.get("limit", 30))
        activity = Activity.objects.filter(user=request.user)[: max(1, min(limit, 100))]
        return Response(ActivitySerializer(activity, many=True).data)


class LeaderboardView(APIView):
    def get(self, request):
        scope = request.query_params.get("scope", "all")
        qs = UserProfile.objects.filter(user__is_staff=False, user__is_superuser=False).select_related("user")
        qs = qs.order_by("-xp")[:50]
        return Response({
            "scope": scope,
            "entries": LeaderboardEntrySerializer(qs, many=True, context={"request": request}).data,
        })


class ProfileDetailStatsView(APIView):
    """Comprehensive profile stats: XP, rank, self-study questions, accuracy, leaderboard position."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        data = UserProfileSerializer(profile, context={"request": request}).data

        leaderboard_rank = (
            UserProfile.objects.filter(
                xp__gt=profile.xp,
                user__is_staff=False,
                user__is_superuser=False,
            ).count()
            + 1
        )

        active_days = 0
        best_day = None

        unique_attempted = 0
        correct_answers = 0
        wrong_answers = unique_attempted - correct_answers
        accuracy = round(correct_answers / unique_attempted * 100, 1) if unique_attempted > 0 else 0.0

        data.update({
            "leaderboard_rank": leaderboard_rank,
            "total_questions_solved": unique_attempted,
            "total_attempts": 0,
            "correct_answers": correct_answers,
            "wrong_answers": max(0, wrong_answers),
            "accuracy_rate": accuracy,
            "total_points_earned": 0,
            "active_days": active_days,
            "best_day_points": best_day["day_points"] if best_day else 0,
            "best_day_date": str(best_day["day"]) if best_day else None,
        })

        return Response(data)


class ActivityGraphView(APIView):
    """Returns daily activity counts for a rolling 365-day window."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from courses.models import LessonQuestionAttempt, UserQuestionAttempt

        user = request.user
        selected_year = request.query_params.get("year")

        # Fetch all user attempts (no date filter yet)
        all_attempts_lqa = LessonQuestionAttempt.objects.filter(user=user).values_list("attempted_at__date", flat=True)
        all_attempts_uqa = UserQuestionAttempt.objects.filter(user=user).values_list("attempted_at__date", flat=True)

        # Combine all dates to find which years have activity
        all_dates = list(all_attempts_lqa) + list(all_attempts_uqa)
        years_with_activity = sorted(set(d.year for d in all_dates if d))

        # If no activity, return empty response
        if not years_with_activity:
            return Response({"days": [], "years": [], "selected_year": selected_year or None})

        # Use selected year or current year, fallback to most recent year with activity
        if selected_year:
            try:
                year = int(selected_year)
                if year not in years_with_activity:
                    year = years_with_activity[-1]
            except (ValueError, TypeError):
                year = years_with_activity[-1]
        else:
            year = years_with_activity[-1]

        # GitHub-like behavior: last 365 days ending on the same month/day within selected year.
        # This avoids showing "future" months for the current year.
        today = timezone.now().date()
        target_month = today.month
        target_day = min(today.day, monthrange(year, target_month)[1])
        end_date = date(year, target_month, target_day)
        start_date = end_date - timedelta(days=364)

        merged = {}

        def add_entries(queryset, points_field):
            for entry in queryset:
                d = str(entry["day"])
                if d not in merged:
                    merged[d] = {"date": d, "questions_solved": 0, "correct_answers": 0, "points_earned": 0}
                merged[d]["questions_solved"] += entry.get("q") or 0
                merged[d]["correct_answers"] += entry.get("c") or 0
                merged[d]["points_earned"] += entry.get(points_field) or 0

        lqa_data = (
            LessonQuestionAttempt.objects.filter(user=user, attempted_at__date__gte=start_date, attempted_at__date__lte=end_date)
            .annotate(day=TruncDate("attempted_at"))
            .values("day")
            .annotate(q=Count("id"), c=Count("id", filter=Q(is_correct=True)), p=Sum("points_awarded"))
        )
        add_entries(lqa_data, "p")

        uqa_data = (
            UserQuestionAttempt.objects.filter(user=user, attempted_at__date__gte=start_date, attempted_at__date__lte=end_date)
            .annotate(day=TruncDate("attempted_at"))
            .values("day")
            .annotate(q=Count("id"), c=Count("id", filter=Q(is_correct=True)), p=Sum("awarded_points"))
        )
        add_entries(uqa_data, "p")

        days = []
        current = start_date
        while current <= end_date:
            d = str(current)
            days.append(merged.get(d) or {"date": d, "questions_solved": 0, "correct_answers": 0, "points_earned": 0})
            current += timedelta(days=1)

        return Response({
            "days": days,
            "years": years_with_activity,
            "selected_year": year,
            "start_date": str(start_date),
            "end_date": str(end_date)
        })


class RecentStudyActivityView(APIView):
    """Latest self-study and course quiz activity for the authenticated user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from courses.models import LessonQuestionAttempt

        user = request.user
        limit = min(int(request.query_params.get("limit", 20)), 50)

        activities = []

        lqa_list = (
            LessonQuestionAttempt.objects.filter(user=user)
            .select_related("question", "question__lesson", "question__lesson__course")
            .order_by("-attempted_at")[:limit]
        )
        for lqa in lqa_list:
            lesson = lqa.question.lesson
            activities.append({
                "id": f"l{lqa.id}",
                "type": "course",
                "question_title": lqa.question.text[:80],
                "question_id": lqa.question.id,
                "course_name": lesson.course.title if lesson and lesson.course_id else "",
                "is_correct": lqa.is_correct,
                "points_earned": lqa.points_awarded,
                "attempted_at": lqa.attempted_at.isoformat(),
                "attempt_number": 1,
            })

        activities.sort(key=lambda x: x["attempted_at"], reverse=True)
        return Response(activities[:limit])
