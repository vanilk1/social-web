from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [

    path("profile/<int:user_id>/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("profile/avatar/", views.update_avatar, name="update_avatar"),
    path("profile/cover/", views.update_cover, name="update_cover"),


    path("profile/<int:user_id>/friend-request/", views.send_friend_request, name="send_friend_request"),
    path("friend-request/<int:request_id>/respond/", views.respond_friend_request, name="respond_friend_request"),


    path("profile/<int:user_id>/follow/", views.toggle_follow, name="toggle_follow"),
]
