from django.urls import path
from . import views

app_name = "chat"

urlpatterns = [
    path("", views.conversation_list, name="list"),
    path("<int:conversation_id>/", views.conversation_detail, name="detail"),
    path("new/private/", views.create_private_conversation, name="new_private"),
    path("new/group/", views.create_group_conversation, name="new_group"),
]
