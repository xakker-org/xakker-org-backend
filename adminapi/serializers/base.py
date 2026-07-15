from django.db import transaction
from django.utils.text import slugify
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from courses.choices import OPTION_LETTERS, sync_choices


class AutoSlugMixin:
    """Fills a blank `slug` from `slug_source_field` on create, mirroring the
    Django admin's `prepopulated_fields` convenience. Forces `slug` to be
    optional at the serializer level regardless of the model field's
    `blank` setting, and appends `-2`, `-3`, … on collision.

    Models like Task declare `unique_together = (parent, "slug")`, which
    makes DRF auto-attach a UniqueTogetherValidator that demands `slug` be
    present in the payload *before* our validate() below gets a chance to
    fill it in. Since the collision loop here already guarantees a globally
    unique slug (a strictly stronger guarantee than any per-parent
    constraint), that auto-validator is redundant and actively wrong for a
    blank/omitted slug — so we drop it.
    """

    slug_source_field = "name"

    def get_fields(self):
        fields = super().get_fields()
        if "slug" in fields:
            fields["slug"].required = False
            fields["slug"].allow_blank = True
        return fields

    def get_validators(self):
        validators = super().get_validators()
        return [
            v for v in validators
            if not (isinstance(v, UniqueTogetherValidator) and "slug" in v.fields)
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        source = attrs.get(self.slug_source_field) or getattr(self.instance, self.slug_source_field, "")
        base = (attrs.get("slug") or "").strip() or slugify(source) or "item"
        model = self.Meta.model
        slug = base
        suffix = 2
        while model.objects.filter(slug=slug).exclude(
            pk=self.instance.pk if self.instance else None
        ).exists():
            slug = f"{base}-{suffix}"
            suffix += 1
        attrs["slug"] = slug
        return attrs


class OptionLetteringSerializerMixin(serializers.Serializer):
    """Shared by TaskQuestionAdminSerializer, LessonQuestionAdminSerializer, and MissionExamQuestionAdminSerializer.

    Inherits from serializers.Serializer (not a plain mixin) so that
    SerializerMetaclass picks up the option_a../correct_option/choices
    fields declared below via `_declared_fields` — a bare mixin's Field
    attributes are silently dropped by DRF, since the metaclass only merges
    `_declared_fields` from bases that are themselves Serializer subclasses.

    Mirrors the option_a..option_e + correct_option convenience fields from
    the Django admin forms (courses/admin.py) so authoring behaves
    identically whether done through /admin/ or this API. Subclasses set:

      - closed_type_value: the type value that means "multiple choice"
      - choice_model: the related Choice model (QuestionChoice / MissionExamChoice)
      - choice_text_field: "text" or "choice_text" on that model
      - type_field: name of the field holding the question type
      - answer_field: name of the free-text answer field, or None if n/a
    """

    closed_type_value = None
    choice_model = None
    choice_text_field = "text"
    type_field = "question_type"
    answer_field = "expected_answer"

    option_a = serializers.CharField(required=False, allow_blank=True, write_only=True)
    option_b = serializers.CharField(required=False, allow_blank=True, write_only=True)
    option_c = serializers.CharField(required=False, allow_blank=True, write_only=True)
    option_d = serializers.CharField(required=False, allow_blank=True, write_only=True)
    option_e = serializers.CharField(required=False, allow_blank=True, write_only=True)
    correct_option = serializers.ChoiceField(
        choices=[(letter, letter) for letter in OPTION_LETTERS],
        required=False,
        allow_blank=True,
        write_only=True,
    )
    choices = serializers.SerializerMethodField(read_only=True)

    def get_choices(self, obj):
        text_field = self.choice_text_field
        return [
            {"id": c.id, "text": getattr(c, text_field), "is_correct": c.is_correct, "order": c.order}
            for c in obj.choices.all()
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        q_type = attrs.get(self.type_field, getattr(self.instance, self.type_field, None))

        opt_map = {
            letter: (attrs.pop(f"option_{letter.lower()}", "") or "").strip()
            for letter in OPTION_LETTERS
        }
        correct = (attrs.pop("correct_option", "") or "").strip() or None
        filled = {letter: text for letter, text in opt_map.items() if text}

        if self.closed_type_value is not None and q_type == self.closed_type_value:
            if len(filled) < 2:
                raise serializers.ValidationError("Closed sual üçün minimum 2 variant doldurulmalıdır.")
            if not correct:
                raise serializers.ValidationError("Düzgün variantı seçin.")
            if correct not in filled:
                raise serializers.ValidationError(f"Düzgün variant {correct} seçildi, lakin mətni boşdur.")
            if self.answer_field:
                attrs[self.answer_field] = ""
        else:
            if self.answer_field:
                expected = (
                    attrs.get(self.answer_field)
                    or getattr(self.instance, self.answer_field, "")
                    or ""
                ).strip()
                if not expected:
                    raise serializers.ValidationError(f"Bu sual tipi üçün cavab sahəsi doldurulmalıdır.")
            if filled or correct:
                raise serializers.ValidationError("Bu sual tipi üçün variant sahələri boş olmalıdır.")

        self._pending_options = [(letter, opt_map[letter]) for letter in OPTION_LETTERS]
        self._pending_correct = correct
        return attrs

    def _sync(self, instance):
        sync_choices(
            instance,
            options=self._pending_options,
            correct_letter=self._pending_correct,
            choice_model=self.choice_model,
            text_field=self.choice_text_field,
        )

    def create(self, validated_data):
        with transaction.atomic():
            instance = super().create(validated_data)
            self._sync(instance)
        return instance

    def update(self, instance, validated_data):
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            self._sync(instance)
        return instance


class NestedWritableMixin:
    """Upserts a nested list-of-dicts field by `id`: existing rows are
    updated, rows without an `id` are created, and rows present on the
    instance but missing from the payload are deleted. Wrap the caller in
    `transaction.atomic()`.

    The parent FK is passed via `save(**{parent_field: parent})` rather than
    stuffed into the payload dict, since child serializers generally don't
    (and shouldn't have to) declare that FK as a writable field.
    """

    def upsert_nested(self, *, parent, related_name, items, child_serializer_class, parent_field):
        manager = getattr(parent, related_name)
        existing = {obj.id: obj for obj in manager.all()}
        seen_ids = set()

        for index, raw_item in enumerate(items):
            item = dict(raw_item)
            item_id = item.pop("id", None)
            item.setdefault("order", index + 1)
            if item_id and item_id in existing:
                child = child_serializer_class(existing[item_id], data=item, partial=True)
                child.is_valid(raise_exception=True)
                child.save(**{parent_field: parent})
                seen_ids.add(item_id)
            else:
                child = child_serializer_class(data=item)
                child.is_valid(raise_exception=True)
                created = child.save(**{parent_field: parent})
                seen_ids.add(created.id)

        for obj_id, obj in existing.items():
            if obj_id not in seen_ids:
                obj.delete()
