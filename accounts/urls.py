from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ActivityGraphView,
    ClientTokenObtainPairView,
    LeaderboardView,
    MeView,
    MyActivityView,
    MyProfileView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    PasswordResetVerifyView,
    ProfileDetailStatsView,
    PublicProfileView,
    RecentStudyActivityView,
    RegisterView,
)

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", ClientTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("password-reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path("password-reset/verify/", PasswordResetVerifyView.as_view(), name="password-reset-verify"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("me/", MeView.as_view(), name="me"),
    path("profile/", MyProfileView.as_view(), name="my-profile"),
    path("profile/stats/", ProfileDetailStatsView.as_view(), name="profile-stats"),
    path("profile/activity-graph/", ActivityGraphView.as_view(), name="activity-graph"),
    path("profile/recent-activity/", RecentStudyActivityView.as_view(), name="recent-study-activity"),
    path("profile/<str:username>/", PublicProfileView.as_view(), name="public-profile"),
    path("activity/", MyActivityView.as_view(), name="my-activity"),
    path("leaderboard/", LeaderboardView.as_view(), name="leaderboard"),
]
