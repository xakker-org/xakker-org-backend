from rest_framework import serializers

from courses.models import Category, Course, Room, RoomTag

from .base import AutoSlugMixin


class CategoryAdminSerializer(AutoSlugMixin, serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class RoomTagAdminSerializer(AutoSlugMixin, serializers.ModelSerializer):
    class Meta:
        model = RoomTag
        fields = "__all__"


class CourseAdminSerializer(AutoSlugMixin, serializers.ModelSerializer):
    slug_source_field = "title"
    category_name = serializers.SerializerMethodField()
    lesson_count = serializers.SerializerMethodField()
    room_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = "__all__"

    def get_category_name(self, obj):
        return obj.category.name if obj.category_id else None

    def get_lesson_count(self, obj):
        return obj.lessons.count()

    def get_room_count(self, obj):
        return obj.rooms.count()


class RoomAdminSerializer(AutoSlugMixin, serializers.ModelSerializer):
    slug_source_field = "title"
    course_title = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = "__all__"

    def get_course_title(self, obj):
        return obj.course.title if obj.course_id else None

    def get_task_count(self, obj):
        return obj.tasks.count()
