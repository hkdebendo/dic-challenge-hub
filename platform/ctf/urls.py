from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import EmailAuthenticationForm
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html",
            authentication_form=EmailAuthenticationForm,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("events/", views.events, name="events"),
    path("events/<slug:slug>/", views.event_detail, name="event_detail"),
    path("events/<slug:slug>/challenges/", views.start_challenges, name="start_challenges"),
    path("events/<slug:slug>/challenges/<int:order>/", views.event_challenge, name="event_challenge"),
    path("events/<slug:slug>/team/create/", views.create_team, name="create_team"),
    path("events/<slug:slug>/team/join/", views.join_team, name="join_team"),
    path("events/<slug:slug>/bonus/submit/", views.submit_bonus, name="submit_bonus"),
    path("events/<slug:slug>/hackathon/submit/", views.submit_hackathon_deliverables, name="submit_hackathon_deliverables"),
    path("events/<slug:slug>/leaderboard/", views.leaderboard_partial, name="leaderboard_partial"),
    path("events/<slug:slug>/follow/", views.admin_follow, name="admin_follow"),
    path("events/<slug:slug>/admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("events/<slug:slug>/admin-dashboard/start/", views.admin_start_event, name="admin_start_event"),
    path("events/<slug:slug>/admin-dashboard/stop/", views.admin_stop_event, name="admin_stop_event"),
    path("events/<slug:slug>/admin-dashboard/team/create/", views.admin_create_team, name="admin_create_team"),
    path("events/<slug:slug>/admin-dashboard/team/<int:team_id>/delete/", views.admin_delete_team, name="admin_delete_team"),
    path("events/<slug:slug>/admin-dashboard/team/<int:team_id>/add-member/", views.admin_add_member, name="admin_add_member"),
    path("events/<slug:slug>/admin-dashboard/team/<int:team_id>/member/<int:user_id>/remove/", views.admin_remove_member, name="admin_remove_member"),
    path("events/<slug:slug>/admin-dashboard/team/<int:team_id>/captain/", views.admin_set_captain, name="admin_set_captain"),
    path("events/<slug:slug>/test-mode/", views.admin_test_mode, name="admin_test_mode"),
    path("events/<slug:slug>/test-mode/reset/", views.admin_test_reset, name="admin_test_reset"),
    path("users/<int:user_id>/delete/", views.admin_delete_user, name="admin_delete_user"),
    path("hackathon/resources/<int:resource_id>/download/", views.download_hackathon_resource, name="download_hackathon_resource"),
    path("hackathon/submissions/<int:submission_id>/score/", views.admin_score_hackathon_submission, name="admin_score_hackathon_submission"),
    path("hackathon/submissions/<int:submission_id>/<str:field_name>/download/", views.download_hackathon_submission_file, name="download_hackathon_submission_file"),
    path("challenges/<int:challenge_id>/submit/", views.submit_flag, name="submit_flag"),
    path("challenges/<int:challenge_id>/fragment/review/", views.review_fragment, name="review_fragment"),
    path("challenges/<int:challenge_id>/hint/<int:hint_id>/", views.unlock_hint, name="unlock_hint"),
    path("challenges/<int:challenge_id>/close/", views.close_challenge, name="close_challenge"),
    path("challenges/<int:challenge_id>/download/", views.download_attachment, name="download_attachment"),
    path("challenges/<int:challenge_id>/test-submit/", views.admin_test_submit, name="admin_test_submit"),
    path("challenges/<int:challenge_id>/test-hint/<int:hint_id>/", views.admin_test_hint, name="admin_test_hint"),
]
