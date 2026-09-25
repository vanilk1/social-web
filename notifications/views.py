from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Notification, NotificationSettings


@login_required
def notification_list(request):
    """Повна сторінка сповіщень з пагінацією."""
    notifications = (
        request.user.notifications
        .select_related("actor")
        .order_by("-created_at")[:50]
    )
    unread_count = request.user.notifications.filter(is_read=False).count()

    return render(request, "notifications/notification_list.html", {
        "notifications": notifications,
        "unread_count": unread_count,
    })


@login_required
def notification_dropdown(request):
    """
    JSON-ендпоінт для дропдауну в навбарі.
    Повертає останні 10 сповіщень + загальну кількість непрочитаних.
    """
    qs = (
        request.user.notifications
        .select_related("actor")
        .order_by("-created_at")[:10]
    )
    data = {
        "unread_count": request.user.notifications.filter(is_read=False).count(),
        "notifications": [
            {
                "id": n.pk,
                "type": n.notification_type,
                "text": _notification_text(n),
                "actor_name": n.actor.get_full_name() or n.actor.username if n.actor else "Система",
                "actor_avatar": n.actor.avatar.url if n.actor and n.actor.avatar else None,
                "is_read": n.is_read,
                "created_at": n.created_at.strftime("%d.%m %H:%M"),
                "url": _notification_url(n),
            }
            for n in qs
        ],
    }
    return JsonResponse(data)


@login_required
@require_POST
def mark_read(request, notification_id):
    """Позначити одне сповіщення як прочитане."""
    n = get_object_or_404(Notification, pk=notification_id, recipient=request.user)
    n.is_read = True
    n.save(update_fields=["is_read"])

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True})
    return redirect(request.META.get("HTTP_REFERER", "notifications:list"))


@login_required
@require_POST
def mark_all_read(request):
    """Позначити всі сповіщення як прочитані."""
    request.user.notifications.filter(is_read=False).update(is_read=True)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"ok": True})
    return redirect("notifications:list")


@login_required
def notification_settings_view(request):
    """Налаштування типів сповіщень."""
    settings_obj, _ = NotificationSettings.objects.get_or_create(user=request.user)

    if request.method == "POST":
        settings_obj.notify_friend_requests = "notify_friend_requests" in request.POST
        settings_obj.notify_comments = "notify_comments" in request.POST
        settings_obj.notify_likes = "notify_likes" in request.POST
        settings_obj.notify_messages = "notify_messages" in request.POST
        settings_obj.notify_group_activity = "notify_group_activity" in request.POST
        settings_obj.email_notifications = "email_notifications" in request.POST
        settings_obj.save()
        return redirect("notifications:list")

    return render(request, "notifications/notification_settings.html", {
        "s": settings_obj,
    })


# ── Допоміжні функції ─────────────────────────────────────────────────

def _notification_text(n):
    actor = n.actor.get_full_name() or n.actor.username if n.actor else "Хтось"
    texts = {
        "friend_request": f"{actor} надіслав вам запит у друзі",
        "friend_accepted": f"{actor} прийняв ваш запит у друзі",
        "new_follower": f"{actor} підписався на вас",
        "comment": f"{actor} прокоментував вашу публікацію",
        "like": f"{actor} вподобав вашу публікацію",
        "message": f"{actor} надіслав вам повідомлення",
        "group_invite": f"{actor} запросив вас до групи",
        "moderation": "Адміністратор вжив дію щодо вашого контенту",
    }
    return texts.get(n.notification_type, "Нове сповіщення")


def _notification_url(n):
    """Посилання для переходу при кліку на сповіщення."""
    from django.urls import reverse
    urls = {
        "friend_request": reverse("accounts:profile", args=[n.actor.pk]) if n.actor else "#",
        "friend_accepted": reverse("accounts:profile", args=[n.actor.pk]) if n.actor else "#",
        "new_follower": reverse("accounts:profile", args=[n.actor.pk]) if n.actor else "#",
        "comment": "#",   # можна підставити пост, якщо є object_id
        "like": "#",
        "message": reverse("chat:list"),
        "group_invite": "#",
        "moderation": "#",
    }
    return urls.get(n.notification_type, "#")
