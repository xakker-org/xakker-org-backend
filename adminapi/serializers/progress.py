from rest_framework import serializers

from courses.models import (
    Enrollment,
    MissionExamAttempt,
    MissionProgress,
    UserLessonProgress,
    UserQuestionAttempt,
    UserTaskProgress,
)


class UserTaskProgressAdminSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    task_title = serializers.CharField(source="task.title", read_only=True)
    room_title = serializers.CharField(source="task.room.title", read_only=True)

    class Meta:
        model = UserTaskProgress
        fields = "__all__"


class UserQuestionAttemptAdminSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    question_prompt = serializers.CharField(source="question.prompt", read_only=True)

    class Meta:
        model = UserQuestionAttempt
        fields = "__all__"


class UserLessonProgressAdminSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)

    class Meta:
        model = UserLessonProgress
        fields = "__all__"


class MissionProgressAdminSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    mission_title = serializers.CharField(source="mission.title", read_only=True)

    class Meta:
        model = MissionProgress
        fields = "__all__"


class MissionExamAttemptAdminSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    exam_title = serializers.CharField(source="exam.title", read_only=True)

    class Meta:
        model = MissionExamAttempt
        fields = "__all__"


class EnrollmentAdminSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = Enrollment
        fields = "__all__"
