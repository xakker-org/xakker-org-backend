"""Shared option-lettering logic for A–E multiple-choice authoring.

Used by both the Django admin forms (courses/admin.py) and the admin REST
API (adminapi/serializers/base.py) so the two management surfaces can never
diverge in how `option_a..option_e` + `correct_option` map onto choice rows.
"""

OPTION_LETTERS = ["A", "B", "C", "D", "E"]


def sync_choices(question, *, options, correct_letter, choice_model, text_field):
    """Replace `question`'s choice rows with the given lettered options.

    `options` is an ordered iterable of (letter, text) pairs (usually A..E).
    Blank text entries are skipped. The choice whose letter matches
    `correct_letter` is flagged `is_correct=True`.
    """
    question.choices.all().delete()
    order = 1
    for letter, text in options:
        text = (text or "").strip()
        if not text:
            continue
        choice_model.objects.create(
            question=question,
            is_correct=(letter == correct_letter),
            order=order,
            **{text_field: text},
        )
        order += 1
