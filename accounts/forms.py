from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()

CTRL = "form-control"
STYLE = "border:2px solid var(--border);border-radius:10px;padding:.65rem 1rem;font-size:.92rem"

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name","last_name","bio","birth_date","city","email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class":CTRL,"style":STYLE,"placeholder":"Ім'я"}),
            "last_name":  forms.TextInput(attrs={"class":CTRL,"style":STYLE,"placeholder":"Прізвище"}),
            "bio":        forms.Textarea(attrs={"class":CTRL,"style":STYLE,"rows":3,"placeholder":"Про себе..."}),
            "birth_date": forms.DateInput(attrs={"class":CTRL,"style":STYLE,"type":"date"}),
            "city":       forms.TextInput(attrs={"class":CTRL,"style":STYLE,"placeholder":"Місто"}),
            "email":      forms.EmailInput(attrs={"class":CTRL,"style":STYLE}),
        }
        labels = {"first_name":"Ім'я","last_name":"Прізвище","bio":"Про себе","birth_date":"Дата народження","city":"Місто","email":"Email"}

class AvatarForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["avatar"]
        widgets = {"avatar": forms.FileInput(attrs={"class":CTRL,"accept":"image/*"})}

class CoverForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["cover_photo"]
        widgets = {"cover_photo": forms.FileInput(attrs={"class":CTRL,"accept":"image/*"})}
