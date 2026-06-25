from django.contrib import admin

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


class HintInline(admin.TabularInline):
    model = Hint
    extra = 0


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "kind", "is_active", "starts_at", "ends_at")
    list_filter = ("is_active", "kind")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ("event", "order", "title", "points", "unlock_after_solves")
    list_filter = ("event", "category", "difficulty")
    inlines = [HintInline]


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "event", "captain", "created_at")
    list_filter = ("event",)
    search_fields = ("name", "captain__username", "captain__email")


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "team", "joined_at")
    list_filter = ("team__event",)


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ("team", "challenge", "submitted_by", "is_correct", "points_awarded", "created_at")
    list_filter = ("challenge__event", "is_correct")
    search_fields = ("team__name", "value")


admin.site.register(HintUnlock)
admin.site.register(ChallengeClosure)
admin.site.register(BonusSubmission)
admin.site.register(HackathonResource)
admin.site.register(HackathonSubmission)
