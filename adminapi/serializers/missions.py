from rest_framework import serializers

from courses.models import (
    Mission,
    MissionExam,
    MissionExamChoice,
    MissionExamQuestion,
    MissionExamQuestionTypeChoices,
    MissionPass,
)

from .base import AutoSlugMixin, OptionLetteringSerializerMixin


class MissionAdminSerializer(AutoSlugMixin, serializers.ModelSerializer):
    slug_source_field = "title"
    pass_count = serializers.ReadOnlyField()
    has_exam = serializers.ReadOnlyField()

    class Meta:
        model = Mission
        fields = "__all__"


class MissionExamAdminSerializer(serializers.ModelSerializer):
    mission_title = serializers.SerializerMethodField()
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = MissionExam
        fields = "__all__"

    def get_mission_title(self, obj):
        return obj.mission.title if obj.mission_id else None

    def get_question_count(self, obj):
        return obj.questions.count()


class MissionPassAdminSerializer(serializers.ModelSerializer):
    mission_title = serializers.SerializerMethodField()

    class Meta:
        model = MissionPass
        fields = "__all__"

    def get_mission_title(self, obj):
        return obj.mission.title if obj.mission_id else None


class MissionExamQuestionAdminSerializer(OptionLetteringSerializerMixin, serializers.ModelSerializer):
    closed_type_value = MissionExamQuestionTypeChoices.CLOSED
    choice_model = MissionExamChoice
    choice_text_field = "choice_text"
    type_field = "question_type"
    answer_field = "expected_answer"

    exam_title = serializers.SerializerMethodField()

    class Meta:
        model = MissionExamQuestion
        fields = "__all__"

    def get_exam_title(self, obj):
        return obj.exam.title if obj.exam_id else None
