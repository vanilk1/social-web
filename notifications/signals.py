"""
signals.py — автоматичне створення сповіщень через Django signals.

Кожен сигнал підписаний на відповідну модель і створює Notification
лише якщо отримувач увімкнув цей тип у своїх налаштуваннях.
"""
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Notification, NotificationSettings


def _settings(user):
    """Повертає налаштування сповіщень користувача (або дефолт)."""
    obj, _ = NotificationSettings.objects.get_or_create(user=user)
    return obj


def _create(recipient, actor, n_type, target=None):
    """Спільна утиліта: не надсилати самому собі."""
    if recipient == actor:
        return
    ct = None
    oid = None
    if target is not None:
        ct = ContentType.objects.get_for_model(target)
        oid = target.pk
    Notification.objects.create(
        recipient=recipient,
        actor=actor,
        notification_type=n_type,
        content_type=ct,
        object_id=oid,
    )


# ── Лайк публікації ───────────────────────────────────────────────────
@receiver(post_save, sender="social.Like")
def on_like(sender, instance, created, **kwargs):
    if not created:
        return
    if instance.post:
        recipient = instance.post.author
        if _settings(recipient).notify_likes:
            _create(recipient, instance.user, Notification.Type.LIKE, instance.post)
    elif instance.comment:
        recipient = instance.comment.author
        if _settings(recipient).notify_likes:
            _create(recipient, instance.user, Notification.Type.LIKE, instance.comment)


# ── Новий коментар ────────────────────────────────────────────────────
@receiver(post_save, sender="social.Comment")
def on_comment(sender, instance, created, **kwargs):
    if not created:
        return
    recipient = instance.post.author
    if _settings(recipient).notify_comments:
        _create(recipient, instance.author, Notification.Type.COMMENT, instance)


# ── Запит у друзі ─────────────────────────────────────────────────────
@receiver(post_save, sender="accounts.Friendship")
def on_friendship(sender, instance, created, **kwargs):
    if created:
        # Новий запит
        if _settings(instance.to_user).notify_friend_requests:
            _create(
                instance.to_user,
                instance.from_user,
                Notification.Type.FRIEND_REQUEST,
                instance,
            )
    else:
        # Запит прийнято — повідомляємо ініціатора
        if instance.status == "accepted":
            _create(
                instance.from_user,
                instance.to_user,
                Notification.Type.FRIEND_ACCEPTED,
                instance,
            )


# ── Новий підписник ───────────────────────────────────────────────────
@receiver(post_save, sender="accounts.Follow")
def on_follow(sender, instance, created, **kwargs):
    if not created:
        return
    recipient = instance.following
    if _settings(recipient).notify_friend_requests:
        _create(recipient, instance.follower, Notification.Type.NEW_FOLLOWER, instance)


# ── Нове повідомлення в чаті ──────────────────────────────────────────
@receiver(post_save, sender="chat.Message")
def on_message(sender, instance, created, **kwargs):
    if not created:
        return
    participants = instance.conversation.participants.exclude(pk=instance.sender.pk)
    for user in participants:
        if _settings(user).notify_messages:
            _create(user, instance.sender, Notification.Type.MESSAGE, instance)
