from django.db import transaction
from django.utils import timezone

from accounts.models import Activity, UserProfile

from .models import CtfUserMissionStatusChoices, UserMissionProgress


def _get_or_create_progress(user, mission):
    progress, _ = UserMissionProgress.objects.get_or_create(user=user, mission=mission)
    return progress


@transaction.atomic
def submit_flag(*, user, mission, flag):
    """Validate a submitted flag, update progress, and award XP once on first solve."""
    progress = _get_or_create_progress(user, mission)

    already_solved = progress.status == CtfUserMissionStatusChoices.SOLVED
    progress.flag_attempts += 1

    correct = mission.check_flag(flag)

    if not correct:
        if progress.status == CtfUserMissionStatusChoices.NOT_STARTED:
            progress.status = CtfUserMissionStatusChoices.ATTEMPTED
        progress.save()
        return {
            "correct": False,
            "user_status": progress.status,
            "flag_attempts": progress.flag_attempts,
        }

    if already_solved:
        progress.save()
        return {
            "correct": True,
            "user_status": progress.status,
            "flag_attempts": progress.flag_attempts,
            "points_awarded": 0,
            "already_solved": True,
        }

    progress.status = CtfUserMissionStatusChoices.SOLVED
    progress.solved_at = timezone.now()
    progress.save()

    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.award_xp(mission.points)

    Activity.objects.create(
        user=user,
        kind=Activity.Kind.TASK_COMPLETE,
        title=f"Solved CTF mission: {mission.title}",
        detail=mission.short_description,
        xp_delta=mission.points,
        target_slug=mission.slug,
    )

    return {
        "correct": True,
        "user_status": progress.status,
        "flag_attempts": progress.flag_attempts,
        "points_awarded": mission.points,
        "already_solved": False,
    }


@transaction.atomic
def unlock_writeup(*, user, mission):
    """Idempotently unlock the writeup for a user. Returns (writeup, progress) or (None, None)."""
    writeup = getattr(mission, "writeup", None)
    if writeup is None:
        return None, None

    progress = _get_or_create_progress(user, mission)
    if progress.writeup_unlocked_at is None:
        progress.writeup_unlocked_at = timezone.now()
        progress.save(update_fields=["writeup_unlocked_at"])

    return writeup, progress
