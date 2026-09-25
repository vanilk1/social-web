from django.conf import settings
from django.db import models


class Post(models.Model):
    """
    Публікація користувача. Може бути опублікована на стіні користувача
    або в групі (тоді заповнене поле group у groups_app.GroupPost-обгортці,
    див. groups_app/models.py).
    """

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
        verbose_name="Автор",
    )
    text = models.TextField(blank=True, verbose_name="Текст")
    image = models.ImageField(upload_to="posts/images/", null=True, blank=True)
    video = models.FileField(upload_to="posts/videos/", null=True, blank=True)
    link = models.URLField(blank=True, verbose_name="Посилання")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Публікація"
        verbose_name_plural = "Публікації"

    def __str__(self):
        return f"Пост {self.pk} від {self.author}"


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments", verbose_name="Публікація"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments"
    )
    text = models.TextField(verbose_name="Текст коментаря")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Коментар"
        verbose_name_plural = "Коментарі"

    def __str__(self):
        return f"Коментар {self.author} до посту {self.post_id}"


class Like(models.Model):
    """
    Уподобання може стосуватись або публікації, або коментаря
    (рівно одне з полів post/comment має бути заповнене).
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="likes"
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="likes", null=True, blank=True
    )
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name="likes", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "post"], name="unique_like_post",
                condition=models.Q(post__isnull=False),
            ),
            models.UniqueConstraint(
                fields=["user", "comment"], name="unique_like_comment",
                condition=models.Q(comment__isnull=False),
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(post__isnull=False, comment__isnull=True)
                    | models.Q(post__isnull=True, comment__isnull=False)
                ),
                name="like_target_exactly_one",
            ),
        ]
        verbose_name = "Лайк"
        verbose_name_plural = "Лайки"

    def __str__(self):
        target = self.post_id and f"post {self.post_id}" or f"comment {self.comment_id}"
        return f"{self.user} лайкнув {target}"


class Share(models.Model):
    """Поширення публікації користувачем (репост)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shares"
    )
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="shares")
    comment_text = models.TextField(blank=True, verbose_name="Коментар до поширення")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Поширення"
        verbose_name_plural = "Поширення"

    def __str__(self):
        return f"{self.user} поширив пост {self.post_id}"
