from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static


def health(request):
    return JsonResponse({"status": "ok"})

# Use default Django admin - Jazzmin will style it
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/auth/", include("accounts.urls")),
    path("api/courses/", include("courses.urls")),
    path("api/admin/", include("adminapi.urls")),
    path("api/ai-chat/", include("chatbot.urls")),
    path("api/missions/", include("ctf.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)