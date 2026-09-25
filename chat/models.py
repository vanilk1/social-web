from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """
    Розмова: приватна (2 учасники) або групова (3+).
    is_group розрізняє логіку відображення (напр. назва чату).
    """

    is_group = models.BooleanField(default=False, verbose_name="Груповий чат")
    title = models.CharField(
        max_length=150, blank=True, verbose_name="Назва (для групового чату)"
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="ConversationParticipant",
        related_name="conversations",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Розмова"
        verbose_name_plural = "Розмови"

    def __str__(self):
        return self.title or f"Розмова {self.pk}"


class ConversationParticipant(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "user"], name="unique_participant"
            )
        ]
        verbose_name = "Учасник розмови"
        verbose_name_plural = "Учасники розмов"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_messages"
    )
    text = models.TextField(blank=True)
    attachment = models.FileField(
        upload_to="chat/attachments/", null=True, blank=True,
        verbose_name="Файл/фото/відео",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Повідомлення"
        verbose_name_plural = "Повідомлення"

    def __str__(self):
        return f"{self.sender} у розмові {self.conversation_id}"
