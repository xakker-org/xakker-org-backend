from django.db import transaction
from rest_framework import serializers

from courses.models import LearningPlan, LearningPlanCourse

from .base import AutoSlugMixin, NestedWritableMixin


class LearningPlanCourseAdminSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    course_title = serializers.SerializerMethodField()

    class Meta:
        model = LearningPlanCourse
        fields = ["id", "course", "course_title", "order"]

    def get_course_title(self, obj):
        return obj.course.title if obj.course_id else None


class LearningPlanAdminSerializer(AutoSlugMixin, NestedWritableMixin, serializers.ModelSerializer):
    slug_source_field = "title"
    # read_only: rendered from learningplancourse_set on GET. Writes are
    # read from self.initial_data instead (see _write_plan_courses) because
    # the child serializer's `course` FK would otherwise get validated
    # twice — once here (int -> Course instance) and once inside
    # upsert_nested (Course instance -> error, PrimaryKeyRelatedField
    # rejects an already-resolved instance as input).
    plan_courses = LearningPlanCourseAdminSerializer(
        many=True, read_only=True, source="learningplancourse_set"
    )
    course_count = serializers.SerializerMethodField()

    class Meta:
        model = LearningPlan
        fields = "__all__"

    def get_course_count(self, obj):
        return obj.courses.count()

    def _write_plan_courses(self, instance):
        raw_items = self.initial_data.get("plan_courses")
        if raw_items is None:
            return
        self.upsert_nested(
            parent=instance,
            related_name="learningplancourse_set",
            items=raw_items,
            child_serializer_class=LearningPlanCourseAdminSerializer,
            parent_field="plan",
        )

    def create(self, validated_data):
        with transaction.atomic():
            instance = super().create(validated_data)
            self._write_plan_courses(instance)
        return instance

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            self._write_plan_courses(instance)
        return instance
