from django import forms
from .models import Group

CTRL  = "form-control"
STYLE = "border:2px solid var(--border);border-radius:10px;padding:.65rem 1rem;font-size:.92rem"


class GroupForm(forms.ModelForm):
    """Форма створення / редагування групи."""

    class Meta:
        model  = Group
        fields = ["name", "description", "cover_photo", "privacy"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": CTRL, "style": STYLE,
                "placeholder": "Назва групи",
            }),
            "description": forms.Textarea(attrs={
                "class": CTRL, "style": STYLE,
                "rows": 4, "placeholder": "Розкажіть про групу...",
            }),
            "cover_photo": forms.FileInput(attrs={
                "class": CTRL, "accept": "image/*",
            }),
            "privacy": forms.Select(attrs={
                "class": CTRL, "style": STYLE,
            }),
        }
        labels = {
            "name":        "Назва",
            "description": "Опис",
            "cover_photo": "Обкладинка",
            "privacy":     "Приватність",
        }


class GroupPostForm(forms.Form):
    """Форма публікації у групі."""
    text  = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "rows": 3,
            "placeholder": "Напишіть щось для групи...",
            "style": "border:none;background:var(--bg);border-radius:12px;resize:none;width:100%;padding:.75rem 1rem;font-size:.97rem;outline:none",
        }),
    )
    image = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        "class": "form-control form-control-sm", "accept": "image/*",
    }))
