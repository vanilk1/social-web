from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Notification(models.Model):
    """
    Універсальне сповіщення. GenericForeignKey дозволяє прив'язати
    сповіщення до будь-якого об'єкта-джерела (Like, Comment, Friendship,
    Message тощо) без окремої моделі на кожен тип події.
    """

    class Type(models.TextChoices):
        FRIEND_REQUEST = "friend_request", "Запит у друзі"
        FRIEND_ACCEPTED = "friend_accepted", "Запит прийнято"
        NEW_FOLLOWER = "new_follower", "Новий підписник"
        COMMENT = "comment", "Коментар"
        LIKE = "like", "Лайк"
        MESSAGE = "message", "Повідомлення"
        GROUP_INVITE = "group_invite", "Запрошення в групу"
        MODERATION = "moderation", "Дія модерації"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Отримувач",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="triggered_notifications",
        null=True,
        verbose_name="Ініціатор дії",
    )
    notification_type = models.CharField(max_length=20, choices=Type.choices)

    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey("content_type", "object_id")

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Сповіщення"
        verbose_name_plural = "Сповіщення"

    def __str__(self):
        return f"{self.get_notification_type_display()} -> {self.recipient}"


class NotificationSettings(models.Model):
    """Персональні налаштування сповіщень користувача (per-type toggle)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_settings"
    )
    notify_friend_requests = models.BooleanField(default=True)
    notify_comments = models.BooleanField(default=True)
    notify_likes = models.BooleanField(default=True)
    notify_messages = models.BooleanField(default=True)
    notify_group_activity = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Налаштування сповіщень"
        verbose_name_plural = "Налаштування сповіщень"
