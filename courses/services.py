from django.utils import timezone
from django.db import transaction

from accounts.models import Activity, UserProfile

from .models import (
    Question,
    QuestionAttempt,
    Room,
    Task,
    TaskAnswerKind,
    TaskQuestion,
    TaskQuestionChoice,
    UserQuestionAttempt,
    UserTaskProgress,
)


def _normalize_text(value):
    return (value or "").strip().casefold()


def _get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def _touch_streak(profile):
    now = timezone.now()
    if profile.last_activity:
        delta = (now.date() - profile.last_activity.date()).days
        if delta == 0:
            return
        if delta == 1:
            profile.streak_days = profile.streak_days + 1
        else:
            profile.streak_days = 1
    else:
        profile.streak_days = 1
    if profile.streak_days > profile.best_streak:
        profile.best_streak = profile.streak_days
    profile.last_activity = now


def _award_xp_for_question(user, points):
    if points <= 0:
        return
    profile = _get_or_create_profile(user)
    profile.xp = profile.xp + points
    _touch_streak(profile)
    profile.recompute_rank()
    profile.save()


def validate_question_answer(*, question: Question, answer_text="", selected_choice_id=None, selected_choice_ids=None):
    selected_ids = []
    if selected_choice_id is not None:
        selected_ids.append(int(selected_choice_id))
    if selected_choice_ids:
        selected_ids.extend(int(item) for item in selected_choice_ids)

    selected_ids = sorted(set(selected_ids))

    if question.question_type == "closed":
        correct_ids = sorted(
            question.choices.filter(is_correct=True).values_list("id", flat=True)
        )
        is_correct = bool(correct_ids) and selected_ids == correct_ids
        submitted_answer = ",".join(str(item) for item in selected_ids)
        return is_correct, submitted_answer

    normalized_answer = _normalize_text(answer_text)
    raw_expected = (question.expected_answer or "").strip()
    expected_values = [_normalize_text(item) for item in raw_expected.splitlines() if _normalize_text(item)]
    if not expected_values and raw_expected:
        expected_values = [_normalize_text(raw_expected)]
    is_correct = bool(expected_values) and normalized_answer in expected_values
    return is_correct, (answer_text or "").strip()


def calculate_question_points(*, base_points, attempt_number, is_correct):
    if not is_correct:
        return 0
    safe_attempt = max(1, int(attempt_number or 1))
    raw_points = base_points / safe_attempt
    return max(1, round(raw_points))


@transaction.atomic
def submit_question_answer(*, user, question: Question, answer_text="", selected_choice_id=None, selected_choice_ids=None, hint_used=False):
    previous_attempts = QuestionAttempt.objects.filter(user=user, question=question)
    previous_count = previous_attempts.count()
    attempt_number = previous_count + 1

    # Backend guard: points only on the FIRST ever correct answer
    has_previous_correct = previous_attempts.filter(is_correct=True).exists()

    is_correct, submitted_answer = validate_question_answer(
        question=question,
        answer_text=answer_text,
        selected_choice_id=selected_choice_id,
        selected_choice_ids=selected_choice_ids,
    )

    if is_correct and not has_previous_correct:
        points_awarded = question.points
        _award_xp_for_question(user, points_awarded)
    else:
        points_awarded = 0

    attempt = QuestionAttempt.objects.create(
        user=user,
        question=question,
        submitted_answer=submitted_answer,
        is_correct=is_correct,
        points_awarded=points_awarded,
        attempt_number=attempt_number,
        hint_used=hint_used,
    )

    return {
        "attempt": attempt,
        "is_correct": is_correct,
        "points_awarded": points_awarded,
        "attempt_number": attempt_number,
        "explanation": question.explanation or "",
        "already_had_correct": has_previous_correct,
    }


def get_user_question_progress(user):
    attempts = QuestionAttempt.objects.filter(user=user)
    total_questions = Question.objects.count()
    answered_questions = attempts.values("question_id").distinct().count()
    correct_answers = attempts.filter(is_correct=True).values("question_id").distinct().count()
    total_attempts = attempts.count()
    total_points_earned = sum(attempts.values_list("points_awarded", flat=True))
    accuracy_percent = round((correct_answers / answered_questions) * 100, 2) if answered_questions else 0.0

    return {
        "total_questions": total_questions,
        "answered_questions": answered_questions,
        "correct_answers": correct_answers,
        "total_attempts": total_attempts,
        "total_points_earned": total_points_earned,
        "accuracy_percent": accuracy_percent,
    }


def evaluate_answer(question: TaskQuestion, submitted_text: str, selected_choice_id=None):
    """Return (is_correct, awarded_points, explanation)"""
    if question.kind == TaskAnswerKind.REVIEW:
        return None, 0, question.explanation or ""

    if question.kind == TaskAnswerKind.CHOICE:
        if not selected_choice_id:
            return False, 0, question.explanation or ""
        choice = TaskQuestionChoice.objects.filter(id=selected_choice_id, question=question).first()
        if not choice:
            return False, 0, question.explanation or ""
        return choice.is_correct, question.points if choice.is_correct else 0, question.explanation or ""

    ok = question.check_answer(submitted_text or "")
    return bool(ok), question.points if ok else 0, question.explanation or ""


def submit_task_answer(*, user, task: Task, question: TaskQuestion, submitted_text="", selected_choice_id=None, use_hint=False):
    """Record the attempt, update progress, award XP & badges. Returns a result dict."""
    profile = _get_or_create_profile(user)

    is_correct, awarded_points, explanation = evaluate_answer(
        question,
        submitted_text=submitted_text,
        selected_choice_id=selected_choice_id,
    )
    effective_points = awarded_points
    if use_hint and question.hint and awarded_points > 0:
        effective_points = max(0, awarded_points - question.hint_cost)

    UserQuestionAttempt.objects.create(
        user=user,
        question=question,
        submitted_answer=submitted_text or "",
        is_correct=bool(is_correct) if is_correct is not None else False,
        awarded_points=effective_points,
        hint_used=use_hint,
    )

    progress, _ = UserTaskProgress.objects.get_or_create(user=user, task=task)
    if progress.first_attempt_at is None:
        progress.first_attempt_at = timezone.now()
    if use_hint:
        progress.hint_used = True

    # Check task completion: all non-review questions correctly answered at least once
    total_q = task.questions.count()
    non_review_qs = task.questions.exclude(kind=TaskAnswerKind.REVIEW)
    correct_ids = set(
        UserQuestionAttempt.objects.filter(
            user=user, question__in=non_review_qs, is_correct=True
        ).values_list("question_id", flat=True)
    )
    non_review_count = non_review_qs.count()
    auto_complete = non_review_count > 0 and len(correct_ids) >= non_review_count
    was_completed_before = progress.completed
    task_completed_now = False

    xp_delta = 0

    if effective_points and is_correct:
        xp_delta += effective_points

    if auto_complete and not progress.completed:
        progress.completed = True
        progress.completed_at = timezone.now()
        earned = 0
        for q in non_review_qs:
            last_correct = (
                UserQuestionAttempt.objects.filter(user=user, question=q, is_correct=True)
                .order_by("-attempted_at")
                .first()
            )
            if last_correct:
                earned += last_correct.awarded_points
        earned += task.points
        progress.earned_points = earned
        xp_delta += task.points
        task_completed_now = True

    progress.save()

    old_rank = profile.rank
    if xp_delta:
        profile.xp = profile.xp + xp_delta

    if task_completed_now:
        profile.tasks_completed = profile.tasks_completed + 1

    # Check room completion
    room = task.room
    room_total = room.tasks.count()
    room_done = UserTaskProgress.objects.filter(user=user, task__room=room, completed=True).count()
    room_completed_now = False
    if room_total and room_done >= room_total:
        # only count "newly" once
        already_counted_key = f"room_complete:{room.slug}"
        already = Activity.objects.filter(user=user, kind=Activity.Kind.ROOM_COMPLETE, target_slug=room.slug).exists()
        if not already:
            room_completed_now = True
            profile.rooms_completed = profile.rooms_completed + 1
            xp_bonus = room.points
            profile.xp = profile.xp + xp_bonus
            xp_delta += xp_bonus
            Activity.objects.create(
                user=user,
                kind=Activity.Kind.ROOM_COMPLETE,
                title=f"Completed room: {room.title}",
                detail=room.summary,
                xp_delta=xp_bonus,
                target_slug=room.slug,
            )

    _touch_streak(profile)
    profile.recompute_rank()
    profile.save()
    new_rank = profile.rank if profile.rank != old_rank else None

    if task_completed_now:
        Activity.objects.create(
            user=user,
            kind=Activity.Kind.TASK_COMPLETE,
            title=f"Completed task: {task.title}",
            detail=task.room.title,
            xp_delta=task.points,
            target_slug=task.slug,
        )

    if new_rank:
        Activity.objects.create(
            user=user,
            kind=Activity.Kind.RANK_UP,
            title=f"Promoted to {profile.get_rank_display()}",
            detail=f"You reached {profile.xp} XP",
            xp_delta=0,
            target_slug=profile.rank,
        )

    return {
        "is_correct": is_correct,
        "awarded_points": effective_points,
        "xp_delta": xp_delta,
        "explanation": explanation,
        "hint": question.hint if use_hint else "",
        "task_completed": task_completed_now or (was_completed_before and auto_complete),
        "room_completed": room_completed_now,
        "badges_earned": [],
        "new_rank": new_rank,
    }
