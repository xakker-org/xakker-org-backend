from django.contrib import admin
from django.utils.html import format_html
from django import forms

from .choices import sync_choices
from .models import (
    Category,
    Course,
    Enrollment,
    LearningPlan,
    LearningPlanCourse,
    Lesson,
    LessonQuestion,
    LessonQuestionAttempt,
    LessonQuestionChoice,
    Mission,
    MissionExam,
    MissionExamAnswer,
    MissionExamAttempt,
    MissionExamChoice,
    MissionExamQuestion,
    MissionExamQuestionTypeChoices,
    MissionPass,
    MissionPassCompletion,
    MissionProgress,
    Room,
    RoomTag,
    Task,
    TaskQuestion,
    TaskQuestionChoice,
    UserLessonProgress,
    UserQuestionAttempt,
    UserTaskProgress,
)
from django.utils import timezone


class ReadOnlyAdminMixin:
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# ─── Category ─────────────────────────────────────────────────────────────────

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ("name", "slug", "icon", "color", "description")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}


# ─── Lesson / Course ──────────────────────────────────────────────────────────

class LessonQuestionChoiceInline(admin.TabularInline):
    model  = LessonQuestionChoice
    extra  = 4
    fields = ("text", "is_correct", "order")


class LessonQuestionInline(admin.StackedInline):
    model  = LessonQuestion
    extra  = 1
    fields = ("text", "explanation", "at_seconds", "points", "order")
    show_change_link = True


@admin.register(LessonQuestion)
class LessonQuestionAdmin(admin.ModelAdmin):
    list_display  = ("__str__", "lesson", "at_seconds", "points", "order")
    list_filter   = ("lesson__course",)
    search_fields = ("text", "lesson__title", "lesson__course__title")
    inlines       = [LessonQuestionChoiceInline]
    fieldsets = (
        (None, {"fields": ("lesson", "text", "explanation", "points", "order")}),
        ("Video zaman damgası", {
            "fields": ("at_seconds",),
            "description": "Video suallar üçün saniyə cinsindən vaxt (məs. 120 = 2:00). Boş buraxın adi suallar üçün.",
        }),
    )


class LessonInline(admin.StackedInline):
    model  = Lesson
    extra  = 1
    fields = ("title", "video_url", "content", "order")
    show_change_link = True


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display  = ("title", "course", "order", "has_video", "question_count")
    list_filter   = ("course",)
    search_fields = ("title", "course__title")
    inlines       = [LessonQuestionInline]
    fieldsets = (
        (None, {"fields": ("course", "title", "order")}),
        ("Məzmun", {"fields": ("content",)}),
        ("Video", {
            "fields": ("video_url",),
            "description": "YouTube URL (https://youtu.be/...) və ya birbaşa video faylı (.mp4).",
        }),
    )

    @admin.display(boolean=True, description="Video var?")
    def has_video(self, obj):
        return bool(obj.video_url)

    @admin.display(description="Suallar")
    def question_count(self, obj):
        return obj.lesson_questions.count()


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display  = ("title", "slug", "category", "icon", "is_published", "lesson_count", "room_count")
    list_filter   = ("is_published", "category")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_published",)
    inlines = [LessonInline]
    fieldsets = (
        ("Əsas məlumatlar", {"fields": ("title", "slug", "category", "icon", "cover_color", "is_published")}),
        ("Məzmun", {"fields": ("description",)}),
    )

    @admin.display(description="Dərslər")
    def lesson_count(self, obj):
        return obj.lessons.count()

    @admin.display(description="Otaqlar")
    def room_count(self, obj):
        return obj.rooms.count()


@admin.register(LessonQuestionAttempt)
class LessonQuestionAttemptAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display    = ("user", "question", "is_correct", "points_awarded", "attempted_at")
    list_filter     = ("is_correct",)
    search_fields   = ("user__username",)
    readonly_fields = ("user", "question", "selected_choice", "is_correct", "points_awarded", "attempted_at")
    date_hierarchy  = "attempted_at"

@admin.register(UserLessonProgress)
class UserLessonProgressAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display    = ("user", "lesson", "is_completed", "completed_at")
    list_filter     = ("is_completed",)
    search_fields   = ("user__username", "lesson__title")
    readonly_fields = ("user", "lesson", "is_completed", "completed_at")

# ─── Room / Task ──────────────────────────────────────────────────────────────

class TaskQuestionChoiceInline(admin.TabularInline):
    model  = TaskQuestionChoice
    extra  = 4
    fields = ("text", "is_correct", "order")


class TaskQuestionInline(admin.StackedInline):
    model  = TaskQuestion
    extra  = 1
    fields = ("prompt", "kind", "answer", "hint", "hint_cost", "points", "order", "case_sensitive")
    show_change_link = True


class TaskInline(admin.StackedInline):
    model  = Task
    extra  = 1
    fields = ("title", "slug", "content", "order", "points")
    show_change_link = True
    prepopulated_fields = {"slug": ("title",)}


@admin.register(RoomTag)
class RoomTagAdmin(admin.ModelAdmin):
    list_display  = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display   = (
        "title", "course", "env_badge", "level_badge", "target_ip",
        "task_count", "points", "is_published", "is_premium", "order",
    )
    list_filter    = ("level", "env", "is_published", "is_premium", "course__category")
    search_fields  = ("title", "summary", "description", "target_ip")
    prepopulated_fields = {"slug": ("title",)}
    list_editable  = ("is_published", "is_premium", "order")
    filter_horizontal = ("tags",)
    inlines        = [TaskInline]
    save_on_top    = True

    fieldsets = (
        ("Əsas məlumatlar", {
            "fields": ("course", "title", "slug", "summary", "description"),
        }),
        ("Lab mühiti", {
            "fields": ("env", "target_ip", "icon", "cover_color"),
            "description": (
                "Lab-ın texniki parametrləri. "
                "<b>Target IP</b> terminalda tələbəyə göstərilir."
            ),
        }),
        ("Çətinlik / Ballar", {
            "fields": ("level", "estimated_minutes", "points", "order"),
        }),
        ("Yayım", {
            "fields": ("is_published", "is_premium"),
        }),
        ("Teqlər", {
            "fields": ("tags",),
        }),
    )

    @admin.display(description="Tasklar", ordering="tasks__count")
    def task_count(self, obj):
        n = obj.tasks.count()
        color = "#19c37d" if n > 0 else "#888"
        return format_html(
            '<span style="font-weight:700; color:{}">{} task</span>',
            color, n,
        )

    @admin.display(description="Mühit")
    def env_badge(self, obj):
        COLORS = {
            "docker":  ("#6effd6", "#0a2b24"),
            "vm":      ("#ffb86b", "#2a1a00"),
            "linux":   ("#adbac7", "#15202b"),
            "windows": ("#79c0ff", "#0a1a2b"),
            "web":     ("#ff7a8a", "#2b0a0e"),
            "cloud":   ("#c084fc", "#1a0a2b"),
        }
        bg, fg = COLORS.get(obj.env or "docker", ("#888", "#fff"))
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:5px;'
            'font-family:monospace;font-size:11px;font-weight:700">{}</span>',
            bg, fg, (obj.env or "docker").upper(),
        )

    @admin.display(description="Çətinlik")
    def level_badge(self, obj):
        COLORS = {
            "beginner":     "#6effd6",
            "intermediate": "#ffb86b",
            "advanced":     "#ff7a8a",
        }
        color = COLORS.get(obj.level, "#888")
        LABELS = {"beginner": "Asan", "intermediate": "Orta", "advanced": "Çətin"}
        label = LABELS.get(obj.level, obj.level)
        return format_html(
            '<span style="color:{};font-weight:700">{}</span>',
            color, label,
        )

    actions = ["make_published", "make_unpublished", "make_free", "make_premium"]

    @admin.action(description="✓ Seçilmişləri yayımla")
    def make_published(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f"{updated} lab yayımlandı.")

    @admin.action(description="✗ Seçilmişləri gizlə")
    def make_unpublished(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f"{updated} lab gizlədildi.")

    @admin.action(description="🔓 Pulsuz et")
    def make_free(self, request, queryset):
        updated = queryset.update(is_premium=False)
        self.message_user(request, f"{updated} lab pulsuz edildi.")

    @admin.action(description="🔒 Premium et")
    def make_premium(self, request, queryset):
        updated = queryset.update(is_premium=True)
        self.message_user(request, f"{updated} lab premium edildi.")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display  = ("title", "room_link", "order", "points", "question_count", "flag_count")
    list_filter   = ("room__course", "room__level", "room__env")
    search_fields = ("title", "room__title", "room__course__title")
    inlines       = [TaskQuestionInline]
    save_on_top   = True
    fieldsets = (
        ("Əsas", {"fields": ("room", "title", "slug", "order", "points")}),
        ("Məzmun (Markdown)", {
            "fields": ("content",),
            "classes": ("wide",),
            "description": "Markdown dəstəklənir. ```bash...``` bloklarından istifadə edin.",
        }),
    )

    @admin.display(description="Lab")
    def room_link(self, obj):
        url = f"/admin/courses/room/{obj.room_id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.room.title)

    @admin.display(description="Suallar")
    def question_count(self, obj):
        return obj.questions.count()

    @admin.display(description="Flaglar")
    def flag_count(self, obj):
        from .models import TaskAnswerKind
        n = obj.questions.filter(kind=TaskAnswerKind.FLAG).count()
        if n:
            return format_html(
                '<span style="color:#ff3b3b;font-weight:700">🚩 {}</span>', n
            )
        return "—"


@admin.register(TaskQuestion)
class TaskQuestionAdmin(admin.ModelAdmin):
    list_display  = (
        "prompt_short", "task", "kind_badge", "answer_preview",
        "points", "hint_cost", "case_sensitive", "order",
    )
    list_filter   = ("kind", "case_sensitive", "task__room__course", "task__room__level")
    search_fields = ("prompt", "answer", "task__title", "task__room__title")
    inlines       = [TaskQuestionChoiceInline]
    save_on_top   = True
    fieldsets = (
        ("Sual", {
            "fields": ("task", "prompt", "kind", "order", "points"),
        }),
        ("Cavab", {
            "fields": ("answer", "case_sensitive"),
            "description": (
                "<b>FLAG / TEXT / NUMERIC</b> üçün cavab aşağıda yazılır. "
                "Flag formatı üçün adətən <code>xkr{...}</code> şablonu istifadə olunur. "
                "<b>CHOICE</b> üçün aşağıdakı variantları doldurun."
            ),
        }),
        ("İpucu / İzah", {
            "fields": ("hint", "hint_cost", "explanation"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Sual")
    def prompt_short(self, obj):
        return obj.prompt[:70] + ("…" if len(obj.prompt) > 70 else "")

    @admin.display(description="Növ")
    def kind_badge(self, obj):
        STYLES = {
            "flag":    ("🚩", "#ff3b3b", "rgba(255,59,59,0.12)"),
            "text":    ("📝", "#79c0ff", "rgba(121,192,255,0.12)"),
            "numeric": ("🔢", "#ffb86b", "rgba(255,184,107,0.12)"),
            "choice":  ("☑️", "#6effd6", "rgba(110,255,214,0.12)"),
            "review":  ("👁",  "#c084fc", "rgba(192,132,252,0.12)"),
        }
        ico, fg, bg = STYLES.get(obj.kind, ("?", "#888", "transparent"))
        return format_html(
            '<span style="color:{};background:{};padding:2px 8px;border-radius:5px;'
            'font-family:monospace;font-size:11px;font-weight:700">{} {}</span>',
            fg, bg, ico, obj.get_kind_display(),
        )

    @admin.display(description="Cavab (önizləmə)")
    def answer_preview(self, obj):
        if not obj.answer:
            return format_html('<span style="color:#555">—</span>')
        preview = obj.answer[:40] + ("…" if len(obj.answer) > 40 else "")
        return format_html(
            '<code style="color:#ff3b3b;font-size:12px">{}</code>', preview
        )


@admin.register(UserTaskProgress)
class UserTaskProgressAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display    = ("user", "task", "completed", "earned_points", "hint_used", "completed_at")
    list_filter     = ("completed", "hint_used", "task__room")
    search_fields   = ("user__username", "task__title", "task__room__title")
    readonly_fields = (
        "user", "task", "completed", "earned_points",
        "hint_used", "first_attempt_at", "completed_at", "updated_at",
    )
    date_hierarchy  = "completed_at"


@admin.register(UserQuestionAttempt)
class UserQuestionAttemptAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display    = ("user", "question", "submitted_answer", "is_correct", "awarded_points", "hint_used", "attempted_at")
    list_filter     = ("is_correct", "hint_used", "question__task__room")
    search_fields   = ("user__username", "question__prompt", "submitted_answer")
    readonly_fields = (
        "user", "question", "submitted_answer",
        "is_correct", "awarded_points", "hint_used", "attempted_at",
    )
    date_hierarchy  = "attempted_at"

# ─── Learning Plan ────────────────────────────────────────────────────────────

class LearningPlanCourseInline(admin.TabularInline):
    model  = LearningPlanCourse
    extra  = 2
    fields = ("course", "order")


@admin.register(LearningPlan)
class LearningPlanAdmin(admin.ModelAdmin):
    list_display  = ("title", "slug", "level", "is_featured", "is_published", "estimated_hours", "course_count")
    list_filter   = ("level", "is_featured", "is_published")
    search_fields = ("title", "summary", "description")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_featured", "is_published")
    inlines       = [LearningPlanCourseInline]
    fieldsets = (
        ("Əsas məlumatlar", {"fields": ("title", "slug", "level", "icon")}),
        ("Məzmun", {"fields": ("summary", "description")}),
        ("Parametrlər", {"fields": ("estimated_hours", "is_featured", "is_published")}),
    )

    @admin.display(description="Kurslar")
    def course_count(self, obj):
        return obj.courses.count()


# ─── Enrollment ───────────────────────────────────────────────────────────────

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display  = ("user", "course", "created_at")
    list_filter   = ("course",)
    search_fields = ("user__username", "course__title")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"


# ═══════════════════════════════════════════════════════════════
#  MISSION / PASS ADMIN
# ═══════════════════════════════════════════════════════════════

class MissionPassInline(admin.StackedInline):
    model  = MissionPass
    extra  = 1
    fields = ("title", "content", "order", "estimated_minutes", "is_published")
    show_change_link = True
    ordering = ("order",)
    class Media:
        css = {
            "all": (
                "https://cdn.quilljs.com/1.3.6/quill.snow.css",
            )
        }
        js = (
            "https://cdn.quilljs.com/1.3.6/quill.min.js",
            "admin/js/mission_pass_admin.js",
        )


@admin.register(MissionPass)
class MissionPassAdmin(admin.ModelAdmin):
    list_display  = ("title", "mission", "order", "estimated_minutes", "is_published")
    list_filter   = ("is_published", "mission")
    search_fields = ("title", "mission__title")
    list_editable = ("order", "is_published")
    autocomplete_fields = ("mission",)
    fieldsets = (
        ("Əsas məlumatlar", {"fields": ("mission", "title", "order", "estimated_minutes", "is_published")}),
        ("Məzmun (HTML)", {
            "fields": ("content",),
            "description": "Standart HTML dəstəklənir. &lt;h2&gt;, &lt;p&gt;, &lt;ul&gt;, &lt;pre&gt;, &lt;code&gt; və s. istifadə edin.",
        }),
    )
    class Media:
        css = {
            "all": (
                "https://cdn.quilljs.com/1.3.6/quill.snow.css",
            )
        }
        js = (
            "https://cdn.quilljs.com/1.3.6/quill.min.js",
            "admin/js/mission_pass_admin.js",
        )


class MissionPassAdminForm(forms.ModelForm):
    class Meta:
        model = MissionPass
        fields = "__all__"
        widgets = {
            "content": forms.Textarea(attrs={"class": "vLargeTextField", "rows": 20}),
        }

# attach the form to the admin
MissionPassAdmin.form = MissionPassAdminForm


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display  = (
        "title", "slug", "difficulty", "is_published",
        "pass_count_display", "has_exam_display", "xp_reward", "order",
    )
    list_filter   = ("difficulty", "is_published")
    search_fields = ("title", "description")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_published", "order")
    inlines       = [MissionPassInline]
    fieldsets = (
        ("Əsas məlumatlar", {
            "fields": ("title", "slug", "short_description", "description"),
        }),
        ("Görünüş", {
            "fields": ("icon", "cover_color", "difficulty"),
        }),
        ("Parametrlər", {
            "fields": ("estimated_hours", "xp_reward", "order", "is_published"),
        }),
    )

    @admin.display(description="Passes")
    def pass_count_display(self, obj):
        return obj.passes.filter(is_published=True).count()

    @admin.display(boolean=True, description="Has Exam?")
    def has_exam_display(self, obj):
        return hasattr(obj, "mission_exam") and obj.mission_exam.is_published


# ─── Mission Exam ─────────────────────────────────────────────────────────────

class MissionExamQuestionAdminForm(forms.ModelForm):
    option_a = forms.CharField(required=False, label="Variant A", widget=forms.TextInput(attrs={"class": "vTextField"}))
    option_b = forms.CharField(required=False, label="Variant B", widget=forms.TextInput(attrs={"class": "vTextField"}))
    option_c = forms.CharField(required=False, label="Variant C", widget=forms.TextInput(attrs={"class": "vTextField"}))
    option_d = forms.CharField(required=False, label="Variant D", widget=forms.TextInput(attrs={"class": "vTextField"}))
    option_e = forms.CharField(required=False, label="Variant E (könüllü)", widget=forms.TextInput(attrs={"class": "vTextField"}))
    correct_option = forms.ChoiceField(
        required=False,
        label="Düzgün variant",
        choices=[("", "— Seçin —"), ("A", "A"), ("B", "B"), ("C", "C"), ("D", "D"), ("E", "E")],
    )

    class Meta:
        model = MissionExamQuestion
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["question_text"].label = "Sual mətni"
        self.fields["question_type"].label = "Sual tipi"
        self.fields["expected_answer"].label = "Gözlənilən cavab"
        self.fields["expected_answer"].help_text = "Open sual üçün düzgün cavab. Bir neçə qəbul olunan cavab varsa, hərəsini yeni sətirdə yazın."
        self.fields["expected_answer"].widget.attrs.update({"placeholder": "Məs: nmap -sV 10.10.10.10"})

        if not self.instance.pk:
            return

        if self.instance.question_type == MissionExamQuestionTypeChoices.CLOSED:
            choices = list(self.instance.choices.order_by("order", "id")[:5])
            for idx, choice in enumerate(choices):
                letter = ["a", "b", "c", "d", "e"][idx]
                self.fields[f"option_{letter}"].initial = choice.choice_text
                if choice.is_correct:
                    self.fields["correct_option"].initial = letter.upper()
        else:
            self.fields["expected_answer"].initial = self.instance.expected_answer

    def clean(self):
        cleaned = super().clean()
        q_type = cleaned.get("question_type")
        expected = (cleaned.get("expected_answer") or "").strip()
        opt_map = {k: (cleaned.get(f"option_{k.lower()}") or "").strip() for k in "ABCDE"}
        filled = {k: v for k, v in opt_map.items() if v}
        correct = cleaned.get("correct_option")

        if q_type == MissionExamQuestionTypeChoices.CLOSED:
            if len(filled) < 2:
                raise forms.ValidationError("Closed sual üçün minimum 2 variant doldurulmalıdır.")
            if not correct:
                raise forms.ValidationError("Düzgün variantı seçin.")
            if correct not in filled:
                raise forms.ValidationError(f"Düzgün variant {correct} seçildi, lakin mətni boşdur.")
            cleaned["expected_answer"] = ""
        else:
            if not expected:
                raise forms.ValidationError("Open sual üçün gözlənilən cavabı yazın.")
            if filled or correct:
                raise forms.ValidationError("Open sual üçün variant sahələri boş olmalıdır.")
        return cleaned

    def save(self, commit=True):
        question = super().save(commit=False)
        question.save()
        self._sync_choices(question)
        return question

    def _sync_choices(self, question):
        if question.question_type != MissionExamQuestionTypeChoices.CLOSED:
            question.choices.all().delete()
            return

        opt_map = [
            ("A", self.cleaned_data.get("option_a")),
            ("B", self.cleaned_data.get("option_b")),
            ("C", self.cleaned_data.get("option_c")),
            ("D", self.cleaned_data.get("option_d")),
            ("E", self.cleaned_data.get("option_e")),
        ]
        sync_choices(
            question,
            options=opt_map,
            correct_letter=self.cleaned_data.get("correct_option"),
            choice_model=MissionExamChoice,
            text_field="choice_text",
        )

class MissionExamQuestionInline(admin.StackedInline):
    model  = MissionExamQuestion
    extra  = 1
    form = MissionExamQuestionAdminForm
    show_change_link = True
    ordering = ("order",)

    fieldsets = (
        ("Əsas məlumatlar", {"fields": ("question_text", "question_type", "order")} ),
        ("Closed suallar", {
            "classes": ("question-section", "mission-exam-section-closed"),
            "fields": ("option_a", "option_b", "option_c", "option_d", "option_e", "correct_option"),
        }),
        ("Open sualın cavabı", {
            "classes": ("question-section", "mission-exam-section-open"),
            "fields": ("expected_answer",),
        }),
        ("İzah", {"fields": ("explanation",)}),
    )

    class Media:
        js = ("admin/js/mission_exam_question_admin.js",)


@admin.register(MissionExamQuestion)
class MissionExamQuestionAdmin(admin.ModelAdmin):
    form          = MissionExamQuestionAdminForm
    list_display  = ("question_text", "exam", "question_type", "order")
    list_filter   = ("question_type", "exam__mission")
    search_fields = ("question_text", "exam__title")
    save_on_top   = True
    list_per_page = 20
    fieldsets = (
        ("Əsas məlumatlar", {"fields": ("exam", "question_text", "question_type", "order")} ),
        ("Closed suallar", {
            "classes": ("question-section", "mission-exam-section-closed", "collapse"),
            "fields": ("option_a", "option_b", "option_c", "option_d", "option_e", "correct_option"),
        }),
        ("Open sualın cavabı", {
            "classes": ("question-section", "mission-exam-section-open", "collapse"),
            "fields": ("expected_answer",),
        }),
        ("İzah", {"fields": ("explanation",)}),
    )

    class Media:
        js = ("admin/js/mission_exam_question_admin.js",)


@admin.register(MissionExam)
class MissionExamAdmin(admin.ModelAdmin):
    list_display  = (
        "title", "mission", "passing_score", "time_limit_minutes",
        "max_attempts", "xp_reward", "is_published", "question_count",
    )
    list_filter   = ("is_published",)
    search_fields = ("title", "mission__title")
    list_editable = ("is_published",)
    inlines       = [MissionExamQuestionInline]
    save_on_top   = True
    list_per_page = 20
    fieldsets = (
        ("Əsas məlumatlar", {"fields": ("mission", "title", "description")}),
        ("Qaydalar", {
            "classes": ("collapse",),
            "fields": ("passing_score", "time_limit_minutes", "max_attempts", "xp_reward", "is_published"),
            "description": "passing_score faizdir (0-100). limitsiz vaxt üçün time_limit_minutes=0, limitsiz cəhd üçün max_attempts=0 yazın.",
        }),
    )

    @admin.display(description="Questions")
    def question_count(self, obj):
        return obj.questions.count()


# ─── Mission Progress (read-only) ─────────────────────────────────────────────

@admin.register(MissionProgress)
class MissionProgressAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display    = ("user", "mission", "is_completed", "exam_passed", "started_at", "completed_at")
    list_filter     = ("is_completed", "exam_passed", "mission")
    search_fields   = ("user__username", "mission__title")
    readonly_fields = ("user", "mission", "is_completed", "exam_passed", "started_at", "completed_at")
    date_hierarchy  = "started_at"

@admin.register(MissionPassCompletion)
class MissionPassCompletionAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display    = ("user", "mission_pass", "completed_at")
    list_filter     = ("mission_pass__mission",)
    search_fields   = ("user__username", "mission_pass__title")
    readonly_fields = ("user", "mission_pass", "completed_at")

@admin.register(MissionExamAttempt)
class MissionExamAttemptAdmin(admin.ModelAdmin):
    list_display    = ("user", "exam", "attempt_number", "score", "passed", "started_at", "submitted_at")
    list_filter     = ("passed", "exam__mission")
    search_fields   = ("user__username", "exam__title")
    readonly_fields = ("user", "exam", "attempt_number", "started_at")
    date_hierarchy  = "started_at"
    actions = ["mark_passed"]

    def mark_passed(self, request, queryset):
        updated = 0
        for attempt in queryset:
            if not attempt.passed:
                attempt.passed = True
                attempt.score = 100.0
                attempt.submitted_at = attempt.submitted_at or timezone.now()
                attempt.save(update_fields=["passed", "score", "submitted_at"])
                # update mission progress
                prod, _ = MissionProgress.objects.get_or_create(user=attempt.user, mission=attempt.exam.mission)
                if not prod.exam_passed:
                    prod.exam_passed = True
                    prod.save(update_fields=["exam_passed"])
                updated += 1
        self.message_user(request, f"Marked {updated} attempt(s) as passed.")
    mark_passed.short_description = "Mark selected attempts as passed (score=100)"

@admin.register(MissionExamAnswer)
class MissionExamAnswerAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display    = ("attempt", "question", "submitted_answer")
    search_fields   = ("attempt__user__username", "question__question_text", "submitted_answer")
    readonly_fields = ("attempt", "question", "submitted_answer", "selected_choices")

