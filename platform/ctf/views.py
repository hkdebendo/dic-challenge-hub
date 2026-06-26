from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import IntegrityError
from django.http import FileResponse, Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from datetime import timedelta

from cloudinary.exceptions import Error as CloudinaryError


from .forms import (
    BonusSubmissionForm,
    EventStartForm,
    HackathonScoreForm,
    HackathonSubmissionForm,
    JoinTeamForm,
    RegisterForm,
    SMART_INCIDENT_SLUG,
    SubmissionForm,
    TeamCreateForm,
    hackathon_score_max,
)
from .models import (
    BonusSubmission,
    Challenge,
    ChallengeClosure,
    Event,
    HackathonResource,
    HackathonSubmission,
    Hint,
    HintUnlock,
    Submission,
    Team,
    TeamMembership,
)
from .services import (
    attempts_count,
    is_challenge_closed,
    leaderboard,
    points_for_submission,
    points_with_hint_ids,
    solved_challenge_ids,
    user_team_for_event,
)


def staff_required(user):
    return user.is_staff


def participant_users():
    return User.objects.filter(is_staff=False, is_superuser=False).order_by("first_name", "last_name", "email")


def challenge_card_for_team(challenge, team, solved_ids, solved_count):
    unlocked = (not challenge.event.is_running) or solved_count >= challenge.unlock_after_solves
    closed = is_challenge_closed(team, challenge) if team else False
    attempts = attempts_count(team, challenge) if team else 0
    is_solved = challenge.id in solved_ids
    visible_hints = []
    unlocked_hint_ids = set()
    if team:
        visible_hints = list(
            HintUnlock.objects.filter(team=team, hint__challenge=challenge)
            .select_related("hint")
            .order_by("hint__order")
        )
        unlocked_hint_ids = {unlock.hint_id for unlock in visible_hints}
    return {
        "challenge": challenge,
        "unlocked": unlocked,
        "solved": is_solved,
        "closed": closed,
        "attempts": attempts,
        "remaining_attempts": max(0, challenge.max_attempts - attempts),
        "visible_hints": visible_hints,
        "next_hint": challenge.hints.exclude(id__in=unlocked_hint_ids).first() if team else None,
        "points_after_penalty": points_for_submission(team, challenge) if team else challenge.points,
    }


def home(request):
    if request.user.is_authenticated:
        return redirect("events")
    return render(request, "ctf/home.html")


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Compte créé. Bienvenue sur DIC Challenge Hub.")
            return redirect("events")
    else:
        form = RegisterForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def events(request):
    active_events = list(Event.objects.filter(is_active=True))
    categories = [
        {
            "name": "CTF",
            "description": "Challenges de cybersécurité, investigation, logs, crypto et web.",
            "events": [event for event in active_events if event.kind == "ctf"],
        },
        {
            "name": "Hackathon AI",
            "description": "Hackathon data science et machine learning appliqué à la cybersécurité.",
            "events": [event for event in active_events if event.kind == "hackathon"],
        },
    ]
    return render(request, "ctf/events.html", {"events": active_events, "categories": categories})


@login_required
@never_cache
def event_detail(request, slug):
    event = get_object_or_404(Event, slug=slug, is_active=True)
    if event.is_hackathon:
        return hackathon_event_detail(request, event)
    team = user_team_for_event(request.user, event)
    solved_ids = solved_challenge_ids(team)
    solved_count = len(solved_ids)

    teams = event.teams.prefetch_related("memberships")
    bonus_attempt = BonusSubmission.objects.filter(team=team, event=event).first() if team else None
    total_challenges = event.challenges.count()
    return render(
        request,
        "ctf/event_detail.html",
        {
            "event": event,
            "team": team,
            "teams": teams,
            "bonus_form": BonusSubmissionForm(),
            "create_form": TeamCreateForm(),
            "join_form": JoinTeamForm(),
            "leaderboard_rows": leaderboard(event),
            "can_compete": event.is_running and not request.user.is_staff,
            "bonus_available": bool(team and solved_count >= total_challenges),
            "bonus_attempt": bonus_attempt,
            "solved_count": solved_count,
            "total_challenges": total_challenges,
        },
    )


def hackathon_event_detail(request, event):
    team = user_team_for_event(request.user, event)
    teams = event.teams.prefetch_related("memberships")
    submission = HackathonSubmission.objects.filter(event=event, team=team).first() if team else None
    template_name = "ctf/hackathon_smart_incident_detail.html" if event.slug == SMART_INCIDENT_SLUG else "ctf/hackathon_event_detail.html"
    return render(
        request,
        template_name,
        {
            "event": event,
            "team": team,
            "teams": teams,
            "create_form": TeamCreateForm(),
            "join_form": JoinTeamForm(),
            "resources": event.hackathon_resources.all(),
            "submission": submission,
            "submission_form": HackathonSubmissionForm(event=event),
            "leaderboard_rows": leaderboard(event),
            "can_work": event.is_running and not request.user.is_staff,
            "score_max": hackathon_score_max(event),
        },
    )


@login_required
def start_challenges(request, slug):
    event = get_object_or_404(Event, slug=slug, is_active=True)
    if not event.is_running:
        messages.error(request, "Les challenges seront accessibles après le lancement de l'événement.")
        return redirect(event)
    first = event.challenges.order_by("order").first()
    if not first:
        messages.error(request, "Aucun challenge n'est configuré pour cet événement.")
        return redirect(event)
    return redirect("event_challenge", slug=event.slug, order=first.order)


@login_required
@never_cache
def event_challenge(request, slug, order):
    event = get_object_or_404(Event, slug=slug, is_active=True)
    if not event.is_running:
        messages.error(request, "Les challenges seront accessibles après le lancement de l'événement.")
        return redirect(event)
    challenge = get_object_or_404(event.challenges.prefetch_related("hints"), order=order)
    team = user_team_for_event(request.user, event)
    solved_ids = solved_challenge_ids(team)
    solved_count = len(solved_ids)
    item = challenge_card_for_team(challenge, team, solved_ids, solved_count)
    previous_challenge = event.challenges.filter(order__lt=challenge.order).order_by("-order").first()
    next_challenge = event.challenges.filter(order__gt=challenge.order).order_by("order").first()
    total_challenges = event.challenges.count()
    bonus_attempt = BonusSubmission.objects.filter(team=team, event=event).first() if team else None
    fragment_key = f"solved_fragment_{event.id}_{challenge.id}"
    review_key = f"fragment_review_pending_{event.id}_{challenge.id}"
    solved_fragment = request.session.pop(fragment_key, None)
    if solved_fragment is not None:
        request.session.modified = True
    return render(
        request,
        "ctf/event_challenge.html",
        {
            "event": event,
            "team": team,
            "item": item,
            "previous_challenge": previous_challenge,
            "next_challenge": next_challenge,
            "submission_form": SubmissionForm(),
            "bonus_form": BonusSubmissionForm(),
            "leaderboard_rows": leaderboard(event),
            "can_compete": event.is_running and not request.user.is_staff,
            "bonus_available": bool(team and solved_count >= total_challenges),
            "bonus_attempt": bonus_attempt,
            "solved_count": solved_count,
            "total_challenges": total_challenges,
            "solved_fragment": solved_fragment,
            "fragment_review_pending": bool(request.session.get(review_key)),
        },
    )


@login_required
@require_POST
def create_team(request, slug):
    event = get_object_or_404(Event, slug=slug, is_active=True)
    if event.has_started:
        messages.error(request, "Les inscriptions de teams sont fermées pour cet événement.")
        return redirect(event)
    if request.user.is_staff:
        return HttpResponseForbidden("Un administrateur ne peut pas participer.")
    if user_team_for_event(request.user, event):
        messages.info(request, "Tu es déjà inscrit dans une team pour cet événement.")
        return redirect(event)
    form = TeamCreateForm(request.POST)
    if form.is_valid():
        team = form.save(commit=False)
        team.event = event
        team.captain = request.user
        try:
            team.save()
            TeamMembership.objects.create(user=request.user, team=team)
            messages.success(request, "Team créée. Tu es capitaine.")
        except IntegrityError:
            messages.error(request, "Ce nom de team existe déjà pour cet événement.")
    return redirect(event)


@login_required
@require_POST
def join_team(request, slug):
    event = get_object_or_404(Event, slug=slug, is_active=True)
    if event.has_started:
        messages.error(request, "Les inscriptions de teams sont fermées pour cet événement.")
        return redirect(event)
    if request.user.is_staff:
        return HttpResponseForbidden("Un administrateur ne peut pas participer.")
    if user_team_for_event(request.user, event):
        messages.info(request, "Tu es déjà inscrit dans une team pour cet événement.")
        return redirect(event)
    form = JoinTeamForm(request.POST)
    if form.is_valid():
        team = get_object_or_404(Team, id=form.cleaned_data["team_id"], event=event)
        if team.memberships.count() >= event.max_team_size:
            messages.error(request, "Cette team est complète.")
        else:
            TeamMembership.objects.create(user=request.user, team=team)
            messages.success(request, f"Tu as rejoint {team.name}.")
    return redirect(event)


@login_required
@require_POST
def submit_flag(request, challenge_id):
    challenge = get_object_or_404(Challenge, id=challenge_id)
    event = challenge.event
    if request.user.is_staff:
        return HttpResponseForbidden("Un administrateur ne peut pas participer.")
    if not event.is_running:
        messages.error(request, "L'événement n'est pas en cours. Les soumissions sont fermées.")
        return redirect("event_challenge", slug=event.slug, order=challenge.order)
    team = user_team_for_event(request.user, event)
    if not team:
        messages.error(request, "Inscris-toi dans une team avant de soumettre.")
        return redirect("event_challenge", slug=event.slug, order=challenge.order)
    if not team.captain_id or team.captain_id != request.user.id:
        return HttpResponseForbidden("Seul le capitaine peut soumettre un flag.")
    if len(solved_challenge_ids(team)) < challenge.unlock_after_solves:
        messages.error(request, "Ce challenge n'est pas encore débloqué.")
        return redirect("event_challenge", slug=event.slug, order=challenge.order)
    if is_challenge_closed(team, challenge):
        messages.error(request, "Ce challenge est déjà terminé pour ta team.")
        return redirect("event_challenge", slug=event.slug, order=challenge.order)

    form = SubmissionForm(request.POST)
    if form.is_valid():
        value = form.cleaned_data["flag"].strip()
        is_correct = value == challenge.flag
        points = points_for_submission(team, challenge) if is_correct else 0
        Submission.objects.create(
            team=team,
            challenge=challenge,
            submitted_by=request.user,
            value=value,
            is_correct=is_correct,
            points_awarded=points,
        )
        if is_correct:
            request.session[f"solved_fragment_{event.id}_{challenge.id}"] = challenge.fragment
            request.session.modified = True
            messages.success(request, "Challenge validé.")
        else:
            remaining = max(0, challenge.max_attempts - attempts_count(team, challenge))
            if remaining == 0:
                ChallengeClosure.objects.get_or_create(
                    team=team,
                    challenge=challenge,
                    defaults={"closed_by": request.user, "reason": "attempts"},
                )
                messages.error(request, "Flag incorrect. Tentatives épuisées.")
            else:
                messages.error(request, f"Flag incorrect. Tentatives restantes : {remaining}.")
    return redirect("event_challenge", slug=event.slug, order=challenge.order)


@login_required
@require_POST
def review_fragment(request, challenge_id):
    challenge = get_object_or_404(Challenge, id=challenge_id)
    event = challenge.event
    if request.user.is_staff:
        return HttpResponseForbidden("Un administrateur ne peut pas participer.")
    team = user_team_for_event(request.user, event)
    if not team:
        messages.error(request, "Rejoins une team pour revoir un fragment.")
        return redirect("event_challenge", slug=event.slug, order=challenge.order)
    if challenge.id not in solved_challenge_ids(team):
        messages.error(request, "Ce fragment n'est pas disponible.")
        return redirect("event_challenge", slug=event.slug, order=challenge.order)

    review_key = f"fragment_review_pending_{event.id}_{challenge.id}"
    fragment_key = f"solved_fragment_{event.id}_{challenge.id}"

    if request.POST.get("cancel"):
        request.session.pop(review_key, None)
        request.session.modified = True
        return redirect("event_challenge", slug=event.slug, order=challenge.order)

    if request.POST.get("confirm"):
        submission = (
            team.submissions.filter(challenge=challenge, is_correct=True)
            .order_by("-points_awarded", "created_at")
            .first()
        )
        if submission:
            submission.points_awarded = max(0, submission.points_awarded - 10)
            submission.save(update_fields=["points_awarded"])
        request.session[fragment_key] = challenge.fragment
        request.session.pop(review_key, None)
        request.session.modified = True
        messages.info(request, "Fragment réaffiché. 10 points ont été retranchés.")
        return redirect("event_challenge", slug=event.slug, order=challenge.order)

    request.session[review_key] = True
    request.session.modified = True
    return redirect("event_challenge", slug=event.slug, order=challenge.order)


@login_required
@require_POST
def submit_bonus(request, slug):
    event = get_object_or_404(Event, slug=slug, is_active=True)
    if request.user.is_staff:
        return HttpResponseForbidden("Un administrateur ne peut pas participer.")
    if not event.is_running:
        messages.error(request, "L'événement n'est pas en cours. La soumission bonus est fermée.")
        return redirect(event)
    team = user_team_for_event(request.user, event)
    if not team:
        messages.error(request, "Inscris-toi dans une team avant de soumettre le bonus.")
        return redirect(event)
    if not team.captain_id or team.captain_id != request.user.id:
        return HttpResponseForbidden("Seul le capitaine peut soumettre le bonus.")
    if team.submissions.filter(is_correct=True).values("challenge_id").distinct().count() < event.challenges.count():
        messages.error(request, "Le bonus sera disponible après les challenges principaux.")
        return redirect(event)
    if BonusSubmission.objects.filter(team=team, event=event).count() >= event.bonus_max_attempts:
        messages.error(request, "La tentative bonus a déjà été utilisée.")
        return redirect(event)

    form = BonusSubmissionForm(request.POST)
    if form.is_valid():
        value = form.cleaned_data["flag"].strip()
        is_correct = value == event.bonus_flag
        points = event.bonus_points if is_correct else 0
        BonusSubmission.objects.create(
            team=team,
            event=event,
            submitted_by=request.user,
            value=value,
            is_correct=is_correct,
            points_awarded=points,
        )
        if is_correct:
            messages.success(request, f"Bonus valide. {points} points ajoutés.")
        else:
            messages.error(request, "Bonus incorrect. La tentative unique est consommée.")
    return redirect(event)


@login_required
@require_POST
def unlock_hint(request, challenge_id, hint_id):
    challenge = get_object_or_404(Challenge, id=challenge_id)
    if request.user.is_staff:
        return HttpResponseForbidden("Un administrateur ne peut pas participer.")
    if not challenge.event.is_running:
        messages.error(request, "L'événement n'est pas en cours. Les indices sont fermés.")
        return redirect("event_challenge", slug=challenge.event.slug, order=challenge.order)
    team = user_team_for_event(request.user, challenge.event)
    if not team:
        messages.error(request, "Rejoins une team pour utiliser les indices.")
        return redirect("event_challenge", slug=challenge.event.slug, order=challenge.order)
    hint = get_object_or_404(Hint, id=hint_id, challenge=challenge)
    HintUnlock.objects.get_or_create(team=team, hint=hint, defaults={"unlocked_by": request.user})
    messages.info(request, f"Indice {hint.order} débloqué. Pénalité : -{hint.penalty_percent}%.")
    return redirect("event_challenge", slug=challenge.event.slug, order=challenge.order)


@login_required
@require_POST
def close_challenge(request, challenge_id):
    challenge = get_object_or_404(Challenge, id=challenge_id)
    if request.user.is_staff:
        return HttpResponseForbidden("Un administrateur ne peut pas participer.")
    team = user_team_for_event(request.user, challenge.event)
    if not team:
        messages.error(request, "Rejoins une team pour terminer un challenge.")
        return redirect("event_challenge", slug=challenge.event.slug, order=challenge.order)
    if team.captain_id != request.user.id:
        return HttpResponseForbidden("Seul le capitaine peut terminer un challenge.")
    ChallengeClosure.objects.get_or_create(
        team=team,
        challenge=challenge,
        defaults={"closed_by": request.user, "reason": "skipped"},
    )
    messages.info(request, "Challenge terminé pour ta team.")
    return redirect("event_challenge", slug=challenge.event.slug, order=challenge.order)


@login_required
def download_attachment(request, challenge_id):
    challenge = get_object_or_404(Challenge, id=challenge_id)
    if not challenge.attachment_path:
        raise Http404("Aucun fichier.")
    team = user_team_for_event(request.user, challenge.event)
    if request.user.is_staff or not challenge.event.is_running:
        return HttpResponseForbidden("Téléchargement fermé tant que l'événement n'est pas en cours.")
    if not team or len(solved_challenge_ids(team)) < challenge.unlock_after_solves:
        return HttpResponseForbidden("Challenge non accessible.")
    path = (settings.ROOT_DIR / challenge.attachment_path).resolve()
    if not path.exists() or settings.ROOT_DIR.resolve() not in path.parents:
        raise Http404("Fichier introuvable.")
    return FileResponse(path.open("rb"), as_attachment=True, filename=path.name)


@login_required
def download_hackathon_resource(request, resource_id):
    resource = get_object_or_404(HackathonResource.objects.select_related("event"), id=resource_id)
    event = resource.event
    team = user_team_for_event(request.user, event)
    if request.user.is_staff:
        pass
    elif not event.is_running:
        return HttpResponseForbidden("Les fichiers seront accessibles après le lancement de l'événement.")
    elif not team:
        return HttpResponseForbidden("Inscris-toi dans une team pour télécharger les fichiers.")
    path = (settings.ROOT_DIR / resource.file_path).resolve()
    if not path.exists() or settings.ROOT_DIR.resolve() not in path.parents:
        raise Http404("Fichier introuvable.")
    return FileResponse(path.open("rb"), as_attachment=True, filename=path.name)


@login_required
@require_POST
def submit_hackathon_deliverables(request, slug):
    event = get_object_or_404(Event, slug=slug, is_active=True, kind="hackathon")
    if request.user.is_staff:
        return HttpResponseForbidden("Un administrateur ne peut pas participer.")
    if not event.is_running:
        messages.error(request, "Les livrables seront acceptés après le lancement de l'événement.")
        return redirect(event)
    team = user_team_for_event(request.user, event)
    if not team:
        messages.error(request, "Inscris-toi dans une team avant de déposer les livrables.")
        return redirect(event)
    if not team.captain_id or team.captain_id != request.user.id:
        return HttpResponseForbidden("Seul le capitaine peut déposer les livrables.")
    form = HackathonSubmissionForm(request.POST, request.FILES, event=event)
    if form.is_valid():
        try:
            submission, _ = HackathonSubmission.objects.get_or_create(
                event=event,
                team=team,
                defaults={
                    "submitted_by": request.user,
                    "notebook": form.cleaned_data["notebook"],
                    "prediction_file": form.cleaned_data.get("prediction_file") or "",
                    "presentation": form.cleaned_data.get("presentation") or "",
                    "notes": form.cleaned_data["notes"],
                },
            )
            if not _:
                submission.submitted_by = request.user
                submission.notebook = form.cleaned_data["notebook"]
                if form.cleaned_data.get("prediction_file") is not None:
                    submission.prediction_file = form.cleaned_data.get("prediction_file") or ""
                if form.cleaned_data.get("presentation") is not None:
                    submission.presentation = form.cleaned_data.get("presentation") or ""
                submission.notes = form.cleaned_data["notes"]
                submission.is_evaluated = False
                submission.save()
        except CloudinaryError:
            messages.error(
                request,
                "Dépôt refusé par Cloudinary. Vérifie que la clé API autorise l'upload de fichiers raw.",
            )
        else:
            messages.success(request, "Livrables déposés avec succès.")
    else:
        messages.error(request, "Dépôt refusé. Vérifie les formats attendus.")
    return redirect(event)


@login_required
@user_passes_test(staff_required)
def download_hackathon_submission_file(request, submission_id, field_name):
    submission = get_object_or_404(HackathonSubmission, id=submission_id)
    allowed = {
        "notebook": submission.notebook,
        "prediction": submission.prediction_file,
        "presentation": submission.presentation,
    }
    file_field = allowed.get(field_name)
    if not file_field:
        raise Http404("Fichier introuvable.")
    file_url = file_field.url
    if file_url.startswith(("http://", "https://")):
        return redirect(file_url)
    return FileResponse(file_field.open("rb"), as_attachment=True, filename=file_field.name.rsplit("/", 1)[-1])


@login_required
def leaderboard_partial(request, slug):
    event = get_object_or_404(Event, slug=slug)
    return render(request, "ctf/partials/leaderboard.html", {"leaderboard_rows": leaderboard(event)})


@login_required
@user_passes_test(staff_required)
def admin_follow(request, slug):
    event = get_object_or_404(Event, slug=slug)
    return render(
        request,
        "ctf/admin_follow.html",
        {
            "event": event,
            "leaderboard_rows": leaderboard(event),
        },
    )


@login_required
@user_passes_test(staff_required)
@never_cache
def admin_dashboard(request, slug):
    event = get_object_or_404(Event, slug=slug)
    if event.is_hackathon:
        return admin_hackathon_dashboard(request, event)
    return render(
        request,
        "ctf/admin_dashboard.html",
        {
            "event": event,
            "leaderboard_rows": leaderboard(event),
            "teams": event.teams.prefetch_related("memberships__user", "submissions"),
            "users": User.objects.order_by("is_staff", "first_name", "last_name", "email"),
            "participant_users": participant_users(),
            "start_form": EventStartForm(initial={"duration_minutes": event.duration_minutes}),
        },
    )


def admin_hackathon_dashboard(request, event):
    submissions = event.hackathon_submissions.select_related("team", "submitted_by").order_by("team__name")
    for submission in submissions:
        submission.score_form = HackathonScoreForm(event=event, initial={
        "visualization_score": submission.visualization_score,
        "interpretation_score": submission.interpretation_score,
        "cleaning_score": submission.cleaning_score,
        "feature_engineering_score": submission.feature_engineering_score,
        "model_performance_score": submission.model_performance_score,
        "error_analysis_score": submission.error_analysis_score,
        "submission_quality_score": submission.submission_quality_score,
        "presentation_score": submission.presentation_score,
        "jury_feedback": submission.jury_feedback,
        })
    return render(
        request,
        "ctf/admin_hackathon_dashboard.html",
        {
            "event": event,
            "leaderboard_rows": leaderboard(event),
            "teams": event.teams.prefetch_related("memberships__user"),
            "users": User.objects.order_by("is_staff", "first_name", "last_name", "email"),
            "participant_users": participant_users(),
            "start_form": EventStartForm(initial={"duration_minutes": event.duration_minutes}),
            "resources": event.hackathon_resources.all(),
            "submissions": submissions,
            "score_max": hackathon_score_max(event),
        },
    )


@login_required
@user_passes_test(staff_required)
@require_POST
def admin_score_hackathon_submission(request, submission_id):
    submission = get_object_or_404(HackathonSubmission.objects.select_related("event"), id=submission_id)
    form = HackathonScoreForm(request.POST, event=submission.event)
    if form.is_valid():
        for field, value in form.cleaned_data.items():
            setattr(submission, field, value)
        submission.is_evaluated = True
        submission.save()
        messages.success(request, f"Score enregistré pour {submission.team.name}.")
    else:
        messages.error(request, "Score invalide. Vérifie les limites du barème.")
    return redirect("admin_dashboard", slug=submission.event.slug)


@login_required
@user_passes_test(staff_required)
@require_POST
def admin_start_event(request, slug):
    event = get_object_or_404(Event, slug=slug)
    form = EventStartForm(request.POST)
    if form.is_valid():
        minutes = form.cleaned_data["duration_minutes"]
        now = timezone.now()
        event.duration_minutes = minutes
        event.starts_at = now
        event.ends_at = now + timedelta(minutes=minutes)
        event.save(update_fields=["duration_minutes", "starts_at", "ends_at"])
        messages.success(request, f"Événement démarré pour {minutes} minutes.")
    return redirect("admin_dashboard", slug=event.slug)


@login_required
@user_passes_test(staff_required)
@require_POST
def admin_stop_event(request, slug):
    event = get_object_or_404(Event, slug=slug)
    event.starts_at = None
    event.ends_at = None
    event.save(update_fields=["starts_at", "ends_at"])
    messages.success(request, "Lancement désactivé. L'événement reste visible mais la compétition est fermée.")
    return redirect("admin_dashboard", slug=event.slug)


@login_required
@user_passes_test(staff_required)
@require_POST
def admin_create_team(request, slug):
    event = get_object_or_404(Event, slug=slug)
    if event.has_started:
        messages.error(request, "Impossible de créer une team après le lancement de l'événement.")
        return redirect("admin_dashboard", slug=event.slug)
    name = request.POST.get("name", "").strip()
    if not name:
        messages.error(request, "Nom de team obligatoire.")
        return redirect("admin_dashboard", slug=event.slug)
    try:
        Team.objects.create(event=event, name=name)
        messages.success(request, "Team créée. Choisis maintenant ses membres et son capitaine.")
    except IntegrityError:
        messages.error(request, "Ce nom de team existe déjà pour cet événement.")
    return redirect("admin_dashboard", slug=event.slug)


@login_required
@user_passes_test(staff_required)
@require_POST
def admin_delete_team(request, slug, team_id):
    event = get_object_or_404(Event, slug=slug)
    team = get_object_or_404(Team, id=team_id, event=event)
    team.delete()
    messages.success(request, "Team supprimée.")
    return redirect("admin_dashboard", slug=event.slug)


@login_required
@user_passes_test(staff_required)
@require_POST
def admin_add_member(request, slug, team_id):
    event = get_object_or_404(Event, slug=slug)
    if event.has_started:
        messages.error(request, "Impossible d'ajouter des membres après le lancement de l'événement.")
        return redirect("admin_dashboard", slug=event.slug)
    team = get_object_or_404(Team, id=team_id, event=event)
    user = get_object_or_404(User, id=request.POST.get("user_id"), is_staff=False, is_superuser=False)
    existing = TeamMembership.objects.filter(user=user, team__event=event).exclude(team=team).first()
    if existing:
        messages.error(request, "Cet inscrit est déjà dans une autre team pour cet événement.")
    elif team.memberships.count() >= event.max_team_size:
        messages.error(request, "Cette team est complète.")
    else:
        TeamMembership.objects.get_or_create(user=user, team=team)
        messages.success(request, "Membre ajouté.")
    return redirect("admin_dashboard", slug=event.slug)


@login_required
@user_passes_test(staff_required)
@require_POST
def admin_remove_member(request, slug, team_id, user_id):
    event = get_object_or_404(Event, slug=slug)
    team = get_object_or_404(Team, id=team_id, event=event)
    user = get_object_or_404(User, id=user_id)
    TeamMembership.objects.filter(user=user, team=team).delete()
    if team.captain_id == user.id:
        team.captain = None
        team.save(update_fields=["captain"])
    messages.success(request, "Membre retiré de la team.")
    return redirect("admin_dashboard", slug=event.slug)


@login_required
@user_passes_test(staff_required)
@require_POST
def admin_set_captain(request, slug, team_id):
    event = get_object_or_404(Event, slug=slug)
    team = get_object_or_404(Team, id=team_id, event=event)
    user = get_object_or_404(User, id=request.POST.get("user_id"), is_staff=False, is_superuser=False)
    if not TeamMembership.objects.filter(user=user, team=team).exists():
        messages.error(request, "Le capitaine doit d'abord être membre de cette team.")
    else:
        team.captain = user
        team.save(update_fields=["captain"])
        messages.success(request, "Capitaine mis à jour.")
    return redirect("admin_dashboard", slug=event.slug)


@login_required
@user_passes_test(staff_required)
@require_POST
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if user.is_superuser:
        messages.error(request, "Impossible de supprimer un super administrateur.")
    else:
        user.delete()
        messages.success(request, "Inscrit supprimé de la plateforme.")
    return redirect(request.POST.get("next") or "events")


def _test_state(request, event):
    key = f"admin_test_event_{event.id}"
    state = request.session.setdefault(key, {})
    state.setdefault("hints", {})
    state.setdefault("submissions", [])
    state.setdefault("solved", {})
    state.setdefault("messages", [])
    request.session[key] = state
    request.session.modified = True
    return key, state


@login_required
@user_passes_test(staff_required)
@never_cache
def admin_test_mode(request, slug):
    event = get_object_or_404(Event, slug=slug)
    key, state = _test_state(request, event)
    challenge_cards = []
    for challenge in event.challenges.prefetch_related("hints"):
        hint_ids = set(state["hints"].get(str(challenge.id), []))
        challenge_cards.append(
            {
                "challenge": challenge,
                "visible_hints": challenge.hints.filter(id__in=hint_ids).order_by("order"),
                "next_hint": challenge.hints.exclude(id__in=hint_ids).first(),
                "points_after_penalty": points_with_hint_ids(challenge, hint_ids),
                "solved": str(challenge.id) in state["solved"],
                "awarded": state["solved"].get(str(challenge.id)),
            }
        )
    messages_for_test = list(state.get("messages", []))
    state["messages"] = []
    request.session[key] = state
    request.session.modified = True
    return render(
        request,
        "ctf/admin_test_mode.html",
        {
            "event": event,
            "challenge_cards": challenge_cards,
            "submission_form": SubmissionForm(),
            "test_messages": messages_for_test,
        },
    )


@login_required
@user_passes_test(staff_required)
@require_POST
def admin_test_submit(request, challenge_id):
    challenge = get_object_or_404(Challenge, id=challenge_id)
    key, state = _test_state(request, challenge.event)
    value = request.POST.get("flag", "").strip()
    hint_ids = set(state["hints"].get(str(challenge.id), []))
    is_correct = value == challenge.flag
    points = points_with_hint_ids(challenge, hint_ids) if is_correct else 0
    state["submissions"].append({"challenge": challenge.id, "value": value, "correct": is_correct, "points": points})
    if is_correct:
        state["solved"][str(challenge.id)] = points
        state["messages"].append(f"C{challenge.order}: flag accepté, {points} point(s) auraient été accordés.")
    else:
        state["messages"].append(f"C{challenge.order}: flag refusé.")
    request.session[key] = state
    request.session.modified = True
    return redirect("admin_test_mode", slug=challenge.event.slug)


@login_required
@user_passes_test(staff_required)
@require_POST
def admin_test_hint(request, challenge_id, hint_id):
    challenge = get_object_or_404(Challenge, id=challenge_id)
    hint = get_object_or_404(Hint, id=hint_id, challenge=challenge)
    key, state = _test_state(request, challenge.event)
    ids = set(state["hints"].get(str(challenge.id), []))
    ids.add(hint.id)
    state["hints"][str(challenge.id)] = list(ids)
    state["messages"].append(f"C{challenge.order}: indice {hint.order} vu, pénalité appliquée en mode test.")
    request.session[key] = state
    request.session.modified = True
    return redirect("admin_test_mode", slug=challenge.event.slug)


@login_required
@user_passes_test(staff_required)
@require_POST
def admin_test_reset(request, slug):
    event = get_object_or_404(Event, slug=slug)
    request.session.pop(f"admin_test_event_{event.id}", None)
    messages.success(request, "Mode test réinitialisé.")
    return redirect("admin_test_mode", slug=event.slug)





