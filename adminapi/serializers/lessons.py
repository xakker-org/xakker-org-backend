from django.db import transaction
from rest_framework import serializers

from courses.models import Lesson, LessonQuestion, LessonQuestionChoice

from .base import NestedWritableMixin


class LessonQuestionChoiceAdminSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = LessonQuestionChoice
        fields = ["id", "text", "is_correct", "order"]


class LessonQuestionAdminSerializer(NestedWritableMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    choices = LessonQuestionChoiceAdminSerializer(many=True, required=False)

    class Meta:
        model = LessonQuestion
        fields = "__all__"

    def create(self, validated_data):
        choices_data = validated_data.pop("choices", None)
        with transaction.atomic():
            instance = super().create(validated_data)
            if choices_data is not None:
                self.upsert_nested(
                    parent=instance,
                    related_name="choices",
                    items=choices_data,
                    child_serializer_class=LessonQuestionChoiceAdminSerializer,
                    parent_field="question",
                )
        return instance

    def update(self, instance, validated_data):
        choices_data = validated_data.pop("choices", None)
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if choices_data is not None:
                self.upsert_nested(
                    parent=instance,
                    related_name="choices",
                    items=choices_data,
                    child_serializer_class=LessonQuestionChoiceAdminSerializer,
                    parent_field="question",
                )
        return instance


class LessonAdminSerializer(serializers.ModelSerializer):
    course_title = serializers.SerializerMethodField()
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = "__all__"

    def get_course_title(self, obj):
        return obj.course.title if obj.course_id else None

    def get_question_count(self, obj):
        return obj.lesson_questions.count()
