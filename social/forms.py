from django import forms
from .models import Comment, Post

CTRL  = "form-control"
STYLE = "border:2px solid var(--border);border-radius:10px;padding:.65rem 1rem;font-size:.92rem"


class PostForm(forms.ModelForm):
    """Форма створення публікації."""
    class Meta:
        model  = Post
        fields = ["text", "image", "video", "link"]
        widgets = {
            "text":  forms.Textarea(attrs={
                "class": CTRL, "rows": 3,
                "placeholder": "Що у вас нового?",
                "style": "border:none;background:var(--bg);border-radius:10px;resize:none;font-size:.97rem",
            }),
            "image": forms.FileInput(attrs={"class": CTRL, "accept": "image/*", "style": STYLE}),
            "video": forms.FileInput(attrs={"class": CTRL, "accept": "video/*", "style": STYLE}),
            "link":  forms.URLInput(attrs={"class": CTRL, "placeholder": "https://...", "style": STYLE}),
        }
        labels = {"text": "", "image": "Фото", "video": "Відео", "link": "Посилання"}


class CommentForm(forms.ModelForm):
    class Meta:
        model  = Comment
        fields = ["text"]
        widgets = {
            "text": forms.TextInput(attrs={
                "placeholder": "Написати коментар...",
                "autocomplete": "off",
            })
        }
        labels = {"text": ""}
