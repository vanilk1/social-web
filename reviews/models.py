from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from groups_app.models import Group
from social.models import Post


class Review(models.Model):


    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="reviews", null=True, blank=True
    )
    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="reviews", null=True, blank=True
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name="Оцінка (1-5)",
    )
    text = models.TextField(blank=True, verbose_name="Текст відгуку")
    created_at = models.DateTimeField(auto_now_add=True)

    is_hidden = models.BooleanField(
        default=False, verbose_name="Приховано модератором"
    )
    hidden_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hidden_reviews",
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(post__isnull=False, group__isnull=True)
                    | models.Q(post__isnull=True, group__isnull=False)
                ),
                name="review_target_exactly_one",
            ),
        ]
        verbose_name = "Відгук"
        verbose_name_plural = "Відгуки"

    def __str__(self):
        target = self.post_id and f"post {self.post_id}" or f"group {self.group_id}"
        return f"Відгук {self.author} на {target}: {self.rating}/5"
