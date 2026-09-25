from django.conf import settings
from django.db import models

from social.models import Post


class Group(models.Model):
    class Privacy(models.TextChoices):
        PUBLIC = "public", "Публічна"
        PRIVATE = "private", "Приватна"

    name = models.CharField(max_length=150, verbose_name="Назва")
    description = models.TextField(blank=True, verbose_name="Опис")
    cover_photo = models.ImageField(upload_to="groups/covers/", null=True, blank=True)
    privacy = models.CharField(
        max_length=10, choices=Privacy.choices, default=Privacy.PUBLIC
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_groups",
        verbose_name="Засновник",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Група"
        verbose_name_plural = "Групи"

    def __str__(self):
        return self.name


class GroupMembership(models.Model):
    class Role(models.TextChoices):
        MEMBER = "member", "Учасник"
        MODERATOR = "moderator", "Модератор"
        ADMIN = "admin", "Адміністратор групи"

    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="group_memberships"
    )
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["group", "user"], name="unique_membership")
        ]
        verbose_name = "Членство в групі"
        verbose_name_plural = "Членства в групах"

    def __str__(self):
        return f"{self.user} у групі {self.group} ({self.role})"


class GroupPost(models.Model):


    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="posts")
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name="group_post")
    is_approved = models.BooleanField(default=True, verbose_name="Схвалено модератором")
    removed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="removed_group_posts",
    )

    class Meta:
        verbose_name = "Публікація в групі"
        verbose_name_plural = "Публікації в групах"

    def __str__(self):
        return f"Пост {self.post_id} у групі {self.group}"
