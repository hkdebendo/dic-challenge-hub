from django.conf import settings
from django.db import models
from django.utils import timezone
from django.db.models import Max
from django.urls import reverse


class Event(models.Model):
    KIND_CHOICES = [("ctf", "CTF"), ("hackathon", "Hackathon")]

    title = models.CharField(max_length=140)
    slug = models.SlugField(unique=True)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES, default="ctf")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=120)
    bonus_flag = models.CharField(max_length=255, blank=True)
    bonus_points = models.PositiveIntegerField(default=100)
    bonus_max_attempts = models.PositiveSmallIntegerField(default=1)
    max_team_size = models.PositiveSmallIntegerField(default=4)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_active", "title"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("event_detail", kwargs={"slug": self.slug})

    @property
    def has_started(self):
        return self.starts_at is not None

    @property
    def is_running(self):
        now = timezone.now()
        return bool(self.starts_at and self.ends_at and self.starts_at <= now <= self.ends_at)

    @property
    def is_finished(self):
        return bool(self.ends_at and timezone.now() > self.ends_at)

    @property
    def is_hackathon(self):
        return self.kind == "hackathon"


class Challenge(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="challenges")
    order = models.PositiveSmallIntegerField()
    title = models.CharField(max_length=160)
    category = models.CharField(max_length=120)
    difficulty = models.CharField(max_length=80)
    points = models.PositiveIntegerField()
    statement = models.TextField()
    flag = models.CharField(max_length=255)
    fragment = models.CharField(max_length=80)
    attachment_path = models.CharField(max_length=255, blank=True)
    unlock_after_solves = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=2)

    class Meta:
        ordering = ["event", "order"]
        unique_together = [("event", "order")]

    def __str__(self):
        return f"{self.event}: C{self.order} - {self.title}"

    @property
    def file_name(self):
        return self.attachment_path.rsplit("/", 1)[-1] if self.attachment_path else ""


class Hint(models.Model):
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name="hints")
    order = models.PositiveSmallIntegerField()
    text = models.TextField()
    penalty_percent = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ["challenge", "order"]
        unique_together = [("challenge", "order")]

    def __str__(self):
        return f"{self.challenge} - indice {self.order}"


class Team(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="teams")
    name = models.CharField(max_length=80)
    captain = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="captained_teams",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        unique_together = [("event", "name")]

    def __str__(self):
        return self.name

    def members_count(self):
        return self.memberships.count()

    def solves_count(self):
        return self.submissions.filter(is_correct=True).values("challenge_id").distinct().count()

    def score(self):
        solved = self.submissions.filter(is_correct=True).values("challenge").annotate(
            best_points=Max("points_awarded")
        )
        bonus = self.bonus_submissions.filter(is_correct=True).aggregate(best=Max("points_awarded"))["best"] or 0
        return sum(item["best_points"] or 0 for item in solved) + bonus


class TeamMembership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="team_memberships")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "team")]

    def __str__(self):
        return f"{self.user} -> {self.team}"


class Submission(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="submissions")
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name="submissions")
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    points_awarded = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        state = "OK" if self.is_correct else "KO"
        return f"{self.team} {self.challenge} {state}"


class HintUnlock(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="hint_unlocks")
    hint = models.ForeignKey(Hint, on_delete=models.CASCADE, related_name="unlocks")
    unlocked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("team", "hint")]


class ChallengeClosure(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="closures")
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name="closures")
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reason = models.CharField(max_length=40, choices=[("skipped", "Termine sans flag"), ("attempts", "Tentatives epuisees")])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("team", "challenge")]


class BonusSubmission(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="bonus_submissions")
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="bonus_submissions")
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    points_awarded = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        state = "OK" if self.is_correct else "KO"
        return f"{self.team} bonus {self.event} {state}"


class HackathonResource(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="hackathon_resources")
    title = models.CharField(max_length=140)
    file_path = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["event", "order", "title"]

    def __str__(self):
        return f"{self.event} - {self.title}"

    @property
    def file_name(self):
        return self.file_path.rsplit("/", 1)[-1] if self.file_path else ""


class HackathonSubmission(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="hackathon_submissions")
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="hackathon_submissions")
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notebook = models.FileField(upload_to="hackathon_deliverables/notebooks/")
    prediction_file = models.FileField(upload_to="hackathon_deliverables/submissions/", blank=True)
    presentation = models.FileField(upload_to="hackathon_deliverables/presentations/", blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    visualization_score = models.PositiveSmallIntegerField(default=0)
    interpretation_score = models.PositiveSmallIntegerField(default=0)
    cleaning_score = models.PositiveSmallIntegerField(default=0)
    feature_engineering_score = models.PositiveSmallIntegerField(default=0)
    model_performance_score = models.PositiveSmallIntegerField(default=0)
    error_analysis_score = models.PositiveSmallIntegerField(default=0)
    submission_quality_score = models.PositiveSmallIntegerField(default=0)
    presentation_score = models.PositiveSmallIntegerField(default=0)
    jury_feedback = models.TextField(blank=True)
    is_evaluated = models.BooleanField(default=False)

    class Meta:
        ordering = ["-updated_at"]
        unique_together = [("event", "team")]

    def __str__(self):
        return f"{self.event} - {self.team}"

    @property
    def total_score(self):
        return (
            self.visualization_score
            + self.interpretation_score
            + self.cleaning_score
            + self.feature_engineering_score
            + self.model_performance_score
            + self.error_analysis_score
            + self.submission_quality_score
            + self.presentation_score
        )
