from rest_framework import serializers

from courses.models import Question, QuestionChoice, QuestionTypeChoices

from .base import OptionLetteringSerializerMixin


class QuestionAdminSerializer(OptionLetteringSerializerMixin, serializers.ModelSerializer):
    closed_type_value = QuestionTypeChoices.CLOSED
    choice_model = QuestionChoice
    choice_text_field = "text"
    type_field = "question_type"
    answer_field = "expected_answer"

    course_title = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = "__all__"

    def get_course_title(self, obj):
        return obj.course.title if obj.course_id else None
