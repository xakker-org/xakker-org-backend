from django.db import transaction
from rest_framework import serializers

from courses.models import Task, TaskQuestion, TaskQuestionChoice

from .base import AutoSlugMixin, NestedWritableMixin


class TaskQuestionChoiceAdminSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)

    class Meta:
        model = TaskQuestionChoice
        fields = ["id", "text", "is_correct", "order"]


class TaskQuestionAdminSerializer(NestedWritableMixin, serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    choices = TaskQuestionChoiceAdminSerializer(many=True, required=False)

    class Meta:
        model = TaskQuestion
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
                    child_serializer_class=TaskQuestionChoiceAdminSerializer,
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
                    child_serializer_class=TaskQuestionChoiceAdminSerializer,
                    parent_field="question",
                )
        return instance


class TaskAdminSerializer(AutoSlugMixin, serializers.ModelSerializer):
    slug_source_field = "title"
    room_title = serializers.SerializerMethodField()
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = "__all__"

    def get_room_title(self, obj):
        return obj.room.title if obj.room_id else None

    def get_question_count(self, obj):
        return obj.questions.count()
