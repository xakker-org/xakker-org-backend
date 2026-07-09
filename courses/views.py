from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import Activity, UserProfile
from accounts.serializers import ActivitySerializer, UserProfileSerializer

from accounts.models import UserProfile

from .models import (
    Category,
    Course,
    Enrollment,
    LearningPlan,
    Lesson,
    LessonQuestion,
    LessonQuestionAttempt,
    LessonQuestionChoice,
    Mission,
    MissionExam,
    MissionExamAnswer,
    MissionExamAttempt,
    MissionPass,
    MissionPassCompletion,
    MissionProgress,
    Question,
    QuestionAttempt,
    QuestionTypeChoices,
    Room,
    RoomTag,
    Task,
    TaskQuestion,
    UserLessonProgress,
)
from .serializers import (
    CabinetSummarySerializer,
    CategorySerializer,
    CourseDetailSerializer,
    CourseListSerializer,
    EnrollmentSerializer,
    LearningPlanSerializer,
    LessonQuestionChoiceFullSerializer,
    LessonQuestionSubmitSerializer,
    LessonSerializer,
    MissionDetailSerializer,
    MissionExamAttemptResultSerializer,
    MissionExamSerializer,
    MissionExamSubmitSerializer,
    MissionListSerializer,
    MissionPassDetailSerializer,
    RoomDetailSerializer,
    RoomListSerializer,
    RoomTagSerializer,
    QuestionAnswerSubmitSerializer,
    QuestionAttemptSerializer,
    QuestionDetailSerializer,
    QuestionListSerializer,
    TaskAnswerResultSerializer,
    TaskAnswerSubmitSerializer,
    TaskDetailSerializer,
    UserProgressSerializer,
)
from .services import get_user_question_progress, submit_question_answer, submit_task_answer


def _normalize_exam_text(value):
    return " ".join((value or "").split()).casefold()


def _normalize_exam_answers(value):
    parts = [part.strip() for part in (value or "").replace("|", "\n").splitlines()]
    return {_normalize_exam_text(part) for part in parts if part}


# ----- Categories / tags -----

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class RoomTagListView(generics.ListAPIView):
    queryset = RoomTag.objects.all()
    serializer_class = RoomTagSerializer


# ----- Courses (legacy) -----

class CourseListView(generics.ListAPIView):
    queryset = (
        Course.objects.filter(is_published=True)
        .select_related("category")
        .annotate(
            room_count=Count("rooms", distinct=True),
            lesson_count=Count("lessons", distinct=True),
        )
    )
    serializer_class = CourseListSerializer


class CourseDetailView(generics.RetrieveAPIView):
    queryset = Course.objects.filter(is_published=True).prefetch_related(
        "lessons",
        "rooms",
        "rooms__tags",
        "learning_plans",
        "learning_plans__learningplancourse_set__course",
    )
    serializer_class = CourseDetailSerializer
    lookup_field = "slug"


# ----- Self-study questions -----

class QuestionListView(generics.ListAPIView):
    serializer_class = QuestionListSerializer

    def get_queryset(self):
        queryset = Question.objects.filter(course__is_published=True).select_related("course", "course__category")
        params = self.request.query_params

        if params.get("level"):
            queryset = queryset.filter(level=params["level"])

        if params.get("question_type"):
            queryset = queryset.filter(question_type=params["question_type"])

        course_filter = params.get("course")
        if course_filter:
            queryset = queryset.filter(Q(course__slug=course_filter) | Q(course_id=course_filter))

        if params.get("search"):
            search = params["search"]
            queryset = queryset.filter(Q(title__icontains=search) | Q(prompt__icontains=search))

        return queryset.order_by("order", "id").distinct()


class QuestionDetailView(generics.RetrieveAPIView):
    serializer_class = QuestionDetailSerializer
    queryset = Question.objects.filter(course__is_published=True).select_related("course", "course__category").prefetch_related("choices")
    lookup_field = "id"

    def retrieve(self, request, *args, **kwargs):
        question = self.get_object()
        data = self.get_serializer(question).data
        if request.user.is_authenticated:
            attempts = QuestionAttempt.objects.filter(user=request.user, question=question).order_by("-attempted_at")
            data["attempts"] = QuestionAttemptSerializer(attempts, many=True).data
            data["has_answered"] = attempts.exists()
            if attempts.exists():
                data["correct_choice_ids"] = list(
                    question.choices.filter(is_correct=True).values_list("id", flat=True)
                )
                data["expected_answer"] = question.expected_answer or ""
            else:
                data["correct_choice_ids"] = []
                data["expected_answer"] = ""
        else:
            data["attempts"] = []
            data["has_answered"] = False
            data["correct_choice_ids"] = []
            data["expected_answer"] = ""
        return Response(data)


class QuestionSubmitAnswerView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        question = get_object_or_404(Question.objects.prefetch_related("choices"), id=id)
        serializer = QuestionAnswerSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        if question.question_type == QuestionTypeChoices.CLOSED and payload.get("selected_choice_id") is None:
            return Response({"detail": "Bu sual ucun variant secmelisiniz."}, status=status.HTTP_400_BAD_REQUEST)
        if question.question_type in {QuestionTypeChoices.OPEN, QuestionTypeChoices.TERMINAL} and not (payload.get("answer_text") or "").strip():
            return Response({"detail": "Bu sual ucun yazili cavab daxil etmelisiniz."}, status=status.HTTP_400_BAD_REQUEST)

        result = submit_question_answer(
            user=request.user,
            question=question,
            answer_text=payload.get("answer_text", "") or "",
            selected_choice_id=payload.get("selected_choice_id"),
            selected_choice_ids=payload.get("selected_choice_ids") or [],
            hint_used=payload.get("hint_used", False),
        )

        attempts = QuestionAttempt.objects.filter(user=request.user, question=question).order_by("-attempted_at")
        correct_choice_ids = list(question.choices.filter(is_correct=True).values_list("id", flat=True))
        return Response(
            {
                "question_id": question.id,
                "is_correct": result["is_correct"],
                "points_awarded": result["points_awarded"],
                "attempt_number": result["attempt_number"],
                "explanation": result["explanation"],
                "already_had_correct": result.get("already_had_correct", False),
                "correct_choice_ids": correct_choice_ids,
                "expected_answer": question.expected_answer or "",
                "attempts": QuestionAttemptSerializer(attempts, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


class UserQuestionProgressView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        payload = get_user_question_progress(request.user)
        serializer = UserProgressSerializer(payload)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ----- Rooms -----

class RoomListView(generics.ListAPIView):
    serializer_class = RoomListSerializer

    def get_queryset(self):
        qs = (
            Room.objects.filter(is_published=True)
            .select_related("course", "course__category")
            .prefetch_related("tags", "tasks")
        )
        params = self.request.query_params
        if params.get("level"):
            qs = qs.filter(level=params["level"])
        if params.get("tag"):
            qs = qs.filter(tags__slug=params["tag"])
        if params.get("category"):
            qs = qs.filter(course__category__slug=params["category"])
        if params.get("search"):
            s = params["search"]
            qs = qs.filter(Q(title__icontains=s) | Q(summary__icontains=s) | Q(description__icontains=s))
        return qs.distinct()


class RoomDetailView(generics.RetrieveAPIView):
    serializer_class = RoomDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return (
            Room.objects.filter(is_published=True)
            .select_related("course", "course__category")
            .prefetch_related("tags", "tasks__questions__choices")
        )


class TaskDetailView(generics.RetrieveAPIView):
    serializer_class = TaskDetailSerializer

    def get_queryset(self):
        return Task.objects.select_related("room").prefetch_related("questions__choices")

    def get_object(self):
        room_slug = self.kwargs["room_slug"]
        task_slug = self.kwargs["task_slug"]
        return self.get_queryset().get(room__slug=room_slug, slug=task_slug)


class TaskAnswerSubmitView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_slug, task_slug):
        try:
            task = Task.objects.select_related("room").get(room__slug=room_slug, slug=task_slug)
        except Task.DoesNotExist:
            return Response({"detail": "Task not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = TaskAnswerSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        try:
            question = TaskQuestion.objects.get(id=payload["question_id"], task=task)
        except TaskQuestion.DoesNotExist:
            return Response({"detail": "Question not found for this task."}, status=status.HTTP_404_NOT_FOUND)

        result = submit_task_answer(
            user=request.user,
            task=task,
            question=question,
            submitted_text=payload.get("answer", "") or "",
            selected_choice_id=payload.get("selected_choice"),
            use_hint=payload.get("use_hint", False),
        )
        result_serializer = TaskAnswerResultSerializer(result)
        return Response(result_serializer.data, status=status.HTTP_200_OK)


class TaskHintView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, room_slug, task_slug, question_id):
        try:
            question = TaskQuestion.objects.get(id=question_id, task__room__slug=room_slug, task__slug=task_slug)
        except TaskQuestion.DoesNotExist:
            return Response({"detail": "Question not found."}, status=status.HTTP_404_NOT_FOUND)

        if not question.hint:
            return Response({"detail": "No hint available."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "hint": question.hint,
            "cost": question.hint_cost,
        })


# ----- Plans -----

class LearningPlanListView(generics.ListAPIView):
    queryset = LearningPlan.objects.filter(is_published=True).prefetch_related(
        "learningplancourse_set__course",
        "learningplancourse_set__course__category",
    )
    serializer_class = LearningPlanSerializer


class LearningPlanDetailView(generics.RetrieveAPIView):
    queryset = LearningPlan.objects.filter(is_published=True).prefetch_related(
        "learningplancourse_set__course",
        "learningplancourse_set__course__category",
        "learningplancourse_set__course__rooms",
        "learningplancourse_set__course__rooms__tags",
    )
    serializer_class = LearningPlanSerializer
    lookup_field = "slug"


# ----- Dashboard / cabinet -----

class CabinetView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CabinetSummarySerializer

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()

        enrollments = (
            Enrollment.objects.filter(user=user)
            .select_related("course", "course__category")
            .order_by("-created_at")
        )
        enrolled_courses = [enrollment.course for enrollment in enrollments]

        plans = LearningPlan.objects.filter(is_published=True).prefetch_related(
            "learningplancourse_set__course",
            "learningplancourse_set__course__category",
        )

        rooms_qs = Room.objects.filter(is_published=True).select_related("course").prefetch_related("tags", "tasks")
        if enrolled_courses:
            active_rooms = rooms_qs.filter(course__in=enrolled_courses)
        else:
            active_rooms = rooms_qs[:6]

        recommended = (
            rooms_qs.exclude(course__in=enrolled_courses)
            .annotate(num_tasks=Count("tasks"))
            .order_by("-num_tasks", "-id")[:6]
        )

        profile, _ = UserProfile.objects.get_or_create(user=user)
        recent_activity = Activity.objects.filter(user=user)[:10]

        stats = {
            "active_courses": len(enrolled_courses),
            "active_plans": plans.count(),
            "available_rooms": active_rooms.count(),
            "tasks_completed": profile.tasks_completed,
            "rooms_completed": profile.rooms_completed,
            "xp": profile.xp,
            "rank": profile.rank,
            "streak": profile.streak_days,
        }

        payload = {
            "username": user.username,
            "email": user.email or "",
            "account_type": "admin" if user.is_staff or user.is_superuser else "client",
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
            "enrolled_courses": enrolled_courses,
            "plans": plans,
            "rooms": active_rooms[:8],
            "recommended_rooms": recommended,
            "profile": UserProfileSerializer(profile).data,
            "recent_activity": ActivitySerializer(recent_activity, many=True).data,
            "stats": stats,
        }
        serializer = self.get_serializer(payload, context={"request": request})
        return Response(serializer.data)


# ----- Lesson detail & lesson question submit -----

class LessonDetailView(generics.RetrieveAPIView):
    serializer_class = LessonSerializer

    def get_queryset(self):
        return Lesson.objects.select_related("course").prefetch_related(
            "lesson_questions__choices"
        )

    def get_object(self):
        return get_object_or_404(
            self.get_queryset(),
            id=self.kwargs["lesson_id"],
            course__slug=self.kwargs["slug"],
            course__is_published=True,
        )

    def retrieve(self, request, *args, **kwargs):
        lesson = self.get_object()
        data = self.get_serializer(lesson, context={"request": request}).data
        return Response(data)


class LessonQuestionSubmitView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug, lesson_id, question_id):
        lesson = get_object_or_404(
            Lesson, id=lesson_id, course__slug=slug, course__is_published=True
        )
        question = get_object_or_404(
            LessonQuestion.objects.prefetch_related("choices"),
            id=question_id,
            lesson=lesson,
        )

        existing = LessonQuestionAttempt.objects.filter(
            user=request.user, question=question
        ).first()

        correct_ids = list(question.choices.filter(is_correct=True).values_list("id", flat=True))

        if existing:
            return Response({
                "already_answered": True,
                "is_correct": existing.is_correct,
                "points_awarded": existing.points_awarded,
                "correct_choice_ids": correct_ids,
                "explanation": question.explanation or "",
                "selected_choice_id": existing.selected_choice_id,
            }, status=status.HTTP_200_OK)

        serializer = LessonQuestionSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        selected_choice_id = serializer.validated_data["selected_choice_id"]

        choice = get_object_or_404(LessonQuestionChoice, id=selected_choice_id, question=question)
        is_correct = choice.is_correct
        points_awarded = question.points if is_correct else 0

        LessonQuestionAttempt.objects.create(
            user=request.user,
            question=question,
            selected_choice=choice,
            is_correct=is_correct,
            points_awarded=points_awarded,
        )

        if points_awarded > 0:
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            profile.xp = profile.xp + points_awarded
            profile.recompute_rank()
            profile.save()

        # Auto-complete lesson when all questions have been attempted
        total_qs = lesson.lesson_questions.count()
        answered_qs = LessonQuestionAttempt.objects.filter(
            user=request.user, question__lesson=lesson
        ).count()
        lesson_now_complete = total_qs > 0 and answered_qs >= total_qs
        if lesson_now_complete:
            UserLessonProgress.objects.update_or_create(
                user=request.user,
                lesson=lesson,
                defaults={"is_completed": True, "completed_at": timezone.now()},
            )

        return Response({
            "already_answered": False,
            "is_correct": is_correct,
            "points_awarded": points_awarded,
            "correct_choice_ids": correct_ids,
            "explanation": question.explanation or "",
            "selected_choice_id": selected_choice_id,
            "lesson_completed": lesson_now_complete,
        }, status=status.HTTP_200_OK)


class LessonCompleteView(APIView):
    """Explicitly mark a lesson as complete (for lessons with no questions)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug, lesson_id):
        lesson = get_object_or_404(
            Lesson, id=lesson_id, course__slug=slug, course__is_published=True
        )
        progress, created = UserLessonProgress.objects.update_or_create(
            user=request.user,
            lesson=lesson,
            defaults={"is_completed": True, "completed_at": timezone.now()},
        )
        return Response({"lesson_completed": True, "created": created}, status=status.HTTP_200_OK)


class EnrollmentCreateView(generics.CreateAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        enrollment, created = Enrollment.objects.get_or_create(
            user=request.user,
            course=serializer.validated_data["course"],
        )
        payload = EnrollmentSerializer(enrollment).data
        if created:
            Activity.objects.create(
                user=request.user,
                kind=Activity.Kind.ENROLL,
                title=f"Enrolled in {enrollment.course.title}",
                detail=enrollment.course.description[:120],
                target_slug=enrollment.course.slug,
            )
            return Response(payload, status=status.HTTP_201_CREATED)
        return Response(
            {
                "detail": "User is already enrolled for this course.",
                "enrollment": payload,
            },
            status=status.HTTP_200_OK,
        )


class RoomEnrollView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        try:
            room = Room.objects.select_related("course").get(slug=slug, is_published=True)
        except Room.DoesNotExist:
            return Response({"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND)

        enrollment, created = Enrollment.objects.get_or_create(user=request.user, course=room.course)
        if created:
            Activity.objects.create(
                user=request.user,
                kind=Activity.Kind.ENROLL,
                title=f"Joined {room.course.title}",
                detail=f"via room: {room.title}",
                target_slug=room.slug,
            )
        return Response({
            "enrolled": True,
            "room": room.slug,
            "course": room.course.slug,
            "created": created,
        }, status=status.HTTP_200_OK)


# ═══════════════════════════════════════════════════════════════
#  MISSION VIEWS
# ═══════════════════════════════════════════════════════════════

class MissionListView(generics.ListAPIView):
    """List all published missions with user progress."""
    serializer_class = MissionListSerializer

    def get_queryset(self):
        return (
            Mission.objects.filter(is_published=True)
            .prefetch_related("passes", "mission_exam")
            .order_by("order", "id")
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx


class MissionDetailView(generics.RetrieveAPIView):
    """Mission detail with ordered passes and exam summary."""
    serializer_class = MissionDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Mission.objects.filter(is_published=True).prefetch_related(
            "passes", "mission_exam"
        )

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx


class MissionStartView(APIView):
    """Create or return a MissionProgress record (start the mission)."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        mission = get_object_or_404(Mission, slug=slug, is_published=True)
        progress, created = MissionProgress.objects.get_or_create(
            user=request.user, mission=mission
        )
        return Response(
            {"started": True, "created": created, "mission_slug": slug},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class MissionPassDetailView(generics.RetrieveAPIView):
    """Return a single Pass's full content."""
    serializer_class = MissionPassDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        mission = get_object_or_404(Mission, slug=self.kwargs["slug"], is_published=True)
        return get_object_or_404(
            MissionPass,
            id=self.kwargs["pass_id"],
            mission=mission,
            is_published=True,
        )

    def retrieve(self, request, *args, **kwargs):
        pass_obj = self.get_object()
        data = self.get_serializer(pass_obj).data
        # Attach completion state
        data["is_completed"] = MissionPassCompletion.objects.filter(
            user=request.user, mission_pass=pass_obj
        ).exists()
        return Response(data)


class MissionPassCompleteView(APIView):
    """Mark a Pass as completed for the current user."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug, pass_id):
        mission = get_object_or_404(Mission, slug=slug, is_published=True)
        pass_obj = get_object_or_404(
            MissionPass, id=pass_id, mission=mission, is_published=True
        )

        # Ensure mission progress exists
        MissionProgress.objects.get_or_create(user=request.user, mission=mission)

        completion, created = MissionPassCompletion.objects.get_or_create(
            user=request.user, mission_pass=pass_obj
        )

        # Check if all passes are now complete (for missions without exam)
        all_passes = mission.passes.filter(is_published=True)
        completed_count = MissionPassCompletion.objects.filter(
            user=request.user, mission_pass__in=all_passes
        ).count()
        all_done = completed_count >= all_passes.count()

        # If no exam, mark mission complete
        if all_done and not (hasattr(mission, "mission_exam") and mission.mission_exam.is_published):
            MissionProgress.objects.filter(user=request.user, mission=mission).update(
                is_completed=True, completed_at=timezone.now()
            )

        return Response(
            {
                "pass_completed": True,
                "created": created,
                "completed_passes": completed_count,
                "total_passes": all_passes.count(),
                "all_passes_done": all_done,
            },
            status=status.HTTP_200_OK,
        )


class MissionExamDetailView(generics.RetrieveAPIView):
    """Return the exam with questions (choices without is_correct)."""
    serializer_class = MissionExamSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        mission = get_object_or_404(Mission, slug=self.kwargs["slug"], is_published=True)
        return get_object_or_404(MissionExam, mission=mission, is_published=True)

    def retrieve(self, request, *args, **kwargs):
        exam = self.get_object()
        mission = exam.mission

        # Verify all passes are completed before showing exam questions
        all_passes = mission.passes.filter(is_published=True)
        completed_count = MissionPassCompletion.objects.filter(
            user=request.user, mission_pass__in=all_passes
        ).count()
        passes_done = completed_count >= all_passes.count() or all_passes.count() == 0

        data = self.get_serializer(exam).data
        data["passes_completed"] = passes_done

        # Attach attempt history
        attempts = MissionExamAttempt.objects.filter(
            user=request.user, exam=exam
        ).order_by("-started_at")
        data["attempts_used"] = attempts.count()
        data["best_score"] = attempts.order_by("-score").values_list("score", flat=True).first()
        data["can_attempt"] = (
            passes_done
            and (exam.max_attempts == 0 or attempts.count() < exam.max_attempts)
        )

        # If questions should be hidden until passes are done
        if not passes_done:
            data["questions"] = []

        return Response(data)


class MissionExamStartView(APIView):
    """Create a new exam attempt."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug):
        mission = get_object_or_404(Mission, slug=slug, is_published=True)
        exam = get_object_or_404(MissionExam, mission=mission, is_published=True)

        # Guard: all passes must be complete
        all_passes = mission.passes.filter(is_published=True)
        completed_count = MissionPassCompletion.objects.filter(
            user=request.user, mission_pass__in=all_passes
        ).count()
        if completed_count < all_passes.count():
            return Response(
                {"detail": "Complete all passes before taking the exam."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Guard: max attempts
        existing = MissionExamAttempt.objects.filter(user=request.user, exam=exam)
        if exam.max_attempts > 0 and existing.count() >= exam.max_attempts:
            return Response(
                {"detail": "Maximum attempts reached."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        attempt_number = existing.count() + 1
        attempt = MissionExamAttempt.objects.create(
            user=request.user, exam=exam, attempt_number=attempt_number
        )
        return Response(
            {"attempt_id": attempt.id, "attempt_number": attempt_number},
            status=status.HTTP_201_CREATED,
        )


class MissionExamSubmitView(APIView):
    """Submit exam answers, grade, and update mission progress."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, slug, attempt_id):
        mission = get_object_or_404(Mission, slug=slug, is_published=True)
        exam = get_object_or_404(MissionExam, mission=mission, is_published=True)
        attempt = get_object_or_404(
            MissionExamAttempt,
            id=attempt_id,
            user=request.user,
            exam=exam,
            submitted_at__isnull=True,
        )

        serializer = MissionExamSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answers_data = serializer.validated_data["answers"]

        questions = exam.questions.prefetch_related("choices").all()
        answers_by_question = {
            int(a["question_id"]): a
            for a in answers_data
            if "question_id" in a
        }

        with transaction.atomic():
            correct_count = 0
            total_count = questions.count()

            for q in questions:
                ans_obj, _ = MissionExamAnswer.objects.get_or_create(
                    attempt=attempt, question=q
                )
                payload = answers_by_question.get(q.id, {})

                if q.question_type == "open":
                    submitted_answer = (payload.get("answer_text") or "").strip()
                    ans_obj.submitted_answer = submitted_answer
                    ans_obj.save(update_fields=["submitted_answer"])
                    ans_obj.selected_choices.clear()

                    expected_answers = _normalize_exam_answers(q.expected_answer)
                    if expected_answers and _normalize_exam_text(submitted_answer) in expected_answers:
                        correct_count += 1
                    continue

                selected_ids = payload.get("choice_ids", [])
                correct_ids = set(q.choices.filter(is_correct=True).values_list("id", flat=True))
                selected_set = set(selected_ids)

                ans_obj.submitted_answer = ""
                ans_obj.save(update_fields=["submitted_answer"])
                ans_obj.selected_choices.set(q.choices.filter(id__in=selected_ids))

                if selected_set == correct_ids:
                    correct_count += 1

            score = (correct_count / total_count * 100) if total_count else 0
            passed = score >= exam.passing_score

            attempt.score = round(score, 2)
            attempt.passed = passed
            attempt.submitted_at = timezone.now()
            attempt.save(update_fields=["score", "passed", "submitted_at"])

            # Update mission progress
            progress, _ = MissionProgress.objects.get_or_create(
                user=request.user, mission=mission
            )
            if passed and not progress.exam_passed:
                progress.exam_passed = True
                progress.is_completed = True
                progress.completed_at = timezone.now()
                progress.save(update_fields=["exam_passed", "is_completed", "completed_at"])

                # Mark all published passes as completed when final exam is passed.
                published_pass_ids = list(
                    mission.passes.filter(is_published=True).values_list("id", flat=True)
                )
                if published_pass_ids:
                    completed_pass_ids = set(
                        MissionPassCompletion.objects.filter(
                            user=request.user,
                            mission_pass_id__in=published_pass_ids,
                        ).values_list("mission_pass_id", flat=True)
                    )
                    to_create = [
                        MissionPassCompletion(
                            user=request.user,
                            mission_pass_id=pass_id,
                        )
                        for pass_id in published_pass_ids
                        if pass_id not in completed_pass_ids
                    ]
                    if to_create:
                        MissionPassCompletion.objects.bulk_create(to_create, ignore_conflicts=True)

                # Award XP
                profile, _ = UserProfile.objects.get_or_create(user=request.user)
                xp_gain = exam.xp_reward + mission.xp_reward
                profile.xp += xp_gain
                profile.recompute_rank()
                profile.save(update_fields=["xp", "rank"])

                Activity.objects.create(
                    user=request.user,
                    kind=Activity.Kind.EXAM_SUBMIT,
                    title=f"Completed mission: {mission.title}",
                    detail=f"Score {score:.1f}% — +{xp_gain} XP",
                    target_slug=mission.slug,
                )

        result_serializer = MissionExamAttemptResultSerializer(attempt)
        return Response(
            {
                **result_serializer.data,
                "mission_completed": passed,
            },
            status=status.HTTP_200_OK,
        )


class MyMissionProgressView(generics.ListAPIView):
    """List the current user's mission progress records."""
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        missions = Mission.objects.filter(is_published=True).order_by("order", "id")
        result = []
        for m in missions:
            try:
                prog = MissionProgress.objects.get(user=request.user, mission=m)
            except MissionProgress.DoesNotExist:
                prog = None

            all_passes = m.passes.filter(is_published=True)
            completed_count = MissionPassCompletion.objects.filter(
                user=request.user, mission_pass__in=all_passes
            ).count()

            result.append({
                "mission_id": m.id,
                "mission_slug": m.slug,
                "mission_title": m.title,
                "is_started": prog is not None,
                "is_completed": prog.is_completed if prog else False,
                "exam_passed": prog.exam_passed if prog else False,
                "completed_passes": completed_count,
                "total_passes": all_passes.count(),
            })
        return Response(result)
