from django.urls import path

from .views import MissionDetailView, MissionListView, SubmitFlagView, UnlockWriteupView

urlpatterns = [
    path("", MissionListView.as_view(), name="ctf-mission-list"),
    path("<slug:slug>/", MissionDetailView.as_view(), name="ctf-mission-detail"),
    path("<slug:slug>/submit-flag/", SubmitFlagView.as_view(), name="ctf-mission-submit-flag"),
    path("<slug:slug>/unlock-writeup/", UnlockWriteupView.as_view(), name="ctf-mission-unlock-writeup"),
]
