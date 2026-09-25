from django.urls import path
from . import views

app_name = "social"

urlpatterns = [

    path("posts/create/",               views.create_post,       name="create_post"),
    path("posts/<int:post_id>/delete/", views.delete_post,       name="delete_post"),
    path("posts/<int:post_id>/share/",  views.share_post,        name="share_post"),


    path("posts/<int:post_id>/like/",        views.toggle_like_post,    name="like_post"),
    path("comments/<int:comment_id>/like/",  views.toggle_like_comment, name="like_comment"),


    path("posts/<int:post_id>/comment/",        views.add_comment,    name="add_comment"),
    path("comments/<int:comment_id>/delete/",   views.delete_comment, name="delete_comment"),
]
