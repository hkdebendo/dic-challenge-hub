from django.db.models import Max

from .models import ChallengeClosure, HintUnlock, Submission, TeamMembership


def user_team_for_event(user, event):
    if not user.is_authenticated or user.is_staff:
        return None
    membership = (
        TeamMembership.objects.select_related("team", "team__captain")
        .filter(user=user, team__event=event)
        .first()
    )
    return membership.team if membership else None


def solved_challenge_ids(team):
    if not team:
        return set()
    return set(team.submissions.filter(is_correct=True).values_list("challenge_id", flat=True).distinct())


def attempts_count(team, challenge):
    return Submission.objects.filter(team=team, challenge=challenge).count()


def is_challenge_closed(team, challenge):
    if not team:
        return False
    if ChallengeClosure.objects.filter(team=team, challenge=challenge).exists():
        return True
    return attempts_count(team, challenge) >= challenge.max_attempts and challenge.id not in solved_challenge_ids(team)


def unlocked_hints_count(team, challenge):
    if not team:
        return 0
    return HintUnlock.objects.filter(team=team, hint__challenge=challenge).count()


def points_for_submission(team, challenge):
    if not team:
        return challenge.points
    penalty = sum(
        HintUnlock.objects.filter(team=team, hint__challenge=challenge).values_list(
            "hint__penalty_percent", flat=True
        )
    )
    penalty = min(penalty, 90)
    return max(0, challenge.points - (challenge.points * penalty // 100))


def points_with_hint_ids(challenge, hint_ids):
    penalty = sum(challenge.hints.filter(id__in=hint_ids).values_list("penalty_percent", flat=True))
    penalty = min(penalty, 90)
    return max(0, challenge.points - (challenge.points * penalty // 100))


def leaderboard(event):
    teams = event.teams.select_related("captain").prefetch_related("memberships__user")
    rows = []
    for team in teams:
        if event.is_hackathon:
            hackathon_submission = team.hackathon_submissions.filter(event=event).first()
            solved = []
            bonus = 0
            score = hackathon_submission.total_score if hackathon_submission and hackathon_submission.is_evaluated else 0
        else:
            solved = team.submissions.filter(is_correct=True).values("challenge").annotate(best=Max("points_awarded"))
            bonus = team.bonus_submissions.filter(is_correct=True).aggregate(best=Max("points_awarded"))["best"] or 0
            score = sum(item["best"] or 0 for item in solved) + bonus
        rows.append(
            {
                "team": team,
                "score": score,
                "solves": len(solved),
                "bonus": bonus,
                "members": team.memberships.count(),
                "last_solve": team.submissions.filter(is_correct=True).aggregate(last=Max("created_at"))["last"],
            }
        )
    rows.sort(key=lambda item: (-item["score"], -item["solves"], item["last_solve"] or event.created_at, item["team"].name))
    for index, row in enumerate(rows, start=1):
        row["rank"] = index
    return rows
