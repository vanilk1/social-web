from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Кастомна модель користувача.
    Розширює стандартну AbstractUser полями профілю та роллю доступу.
    """

    class Role(models.TextChoices):
        USER = "user", "Користувач"
        ADMIN = "admin", "Адміністратор"

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.USER,
        verbose_name="Роль",
    )
    avatar = models.ImageField(
        upload_to="avatars/", null=True, blank=True, verbose_name="Аватар"
    )
    cover_photo = models.ImageField(
        upload_to="covers/", null=True, blank=True, verbose_name="Обкладинка"
    )
    bio = models.TextField(max_length=500, blank=True, verbose_name="Про себе")
    birth_date = models.DateField(null=True, blank=True, verbose_name="Дата народження")
    city = models.CharField(max_length=100, blank=True, verbose_name="Місто")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    def __str__(self):
        return self.username


class Friendship(models.Model):
    """
    Двостороння дружба між користувачами (з підтвердженням запиту).
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Очікує підтвердження"
        ACCEPTED = "accepted", "Прийнято"
        DECLINED = "declined", "Відхилено"

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_friend_requests",
        verbose_name="Ініціатор",
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_friend_requests",
        verbose_name="Отримувач",
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["from_user", "to_user"], name="unique_friend_request"
            )
        ]
        verbose_name = "Дружба"
        verbose_name_plural = "Дружби"

    def __str__(self):
        return f"{self.from_user} -> {self.to_user} ({self.status})"


class Follow(models.Model):
    """
    Однобічна підписка на оновлення користувача (без додавання в друзі).
    """

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following",
        verbose_name="Підписник",
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="followers",
        verbose_name="На кого підписаний",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["follower", "following"], name="unique_follow"
            )
        ]
        verbose_name = "Підписка"
        verbose_name_plural = "Підписки"

    def __str__(self):
        return f"{self.follower} слідкує за {self.following}"
