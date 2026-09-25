from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from social.views import feed

urlpatterns = [
    path("admin/", admin.site.urls),


    path("", feed, name="feed"),


    path("", include("accounts.urls")),


    path("auth/", include("accounts.auth_urls")),


    path("social/", include("social.urls")),


    path("groups/", include("groups_app.urls")),


    path("chat/", include("chat.urls")),


    path("notifications/", include("notifications.urls")),


    path("reviews/", include("reviews.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
