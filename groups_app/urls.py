from django.urls import path
from . import views

app_name = "groups_app"

urlpatterns = [
    path("",                                          views.group_list,        name="list"),
    path("create/",                                   views.group_create,      name="create"),
    path("<int:group_id>/",                           views.group_detail,      name="detail"),
    path("<int:group_id>/edit/",                      views.group_edit,        name="edit"),
    path("<int:group_id>/join/",                      views.toggle_membership, name="join"),
    path("<int:group_id>/post/",                      views.group_post_create, name="post_create"),
    path("<int:group_id>/post/<int:group_post_id>/remove/", views.group_post_remove, name="post_remove"),
    path("<int:group_id>/members/<int:member_id>/role/",    views.member_role_change, name="member_role"),
    path("<int:group_id>/members/<int:member_id>/kick/",    views.member_kick,        name="member_kick"),
]
