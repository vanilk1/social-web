from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

User = get_user_model()


def register_view(request):
    if request.user.is_authenticated:
        return redirect("feed")

    if request.method == "POST":
        username   = request.POST.get("username", "").strip()
        email      = request.POST.get("email", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name  = request.POST.get("last_name", "").strip()
        password1  = request.POST.get("password1", "")
        password2  = request.POST.get("password2", "")

        errors = {}

        if not username:
            errors["username"] = "Введіть ім'я користувача."
        elif User.objects.filter(username=username).exists():
            errors["username"] = "Це ім'я вже зайнято."

        if email and User.objects.filter(email=email).exists():
            errors["email"] = "Цей email вже зареєстровано."

        if len(password1) < 8:
            errors["password1"] = "Пароль має бути не менше 8 символів."
        elif password1 != password2:
            errors["password2"] = "Паролі не співпадають."

        if not errors:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
            )
            login(request, user)
            messages.success(request, f"Ласкаво просимо, {user.get_short_name() or user.username}!")
            return redirect("feed")

        return render(request, "accounts/register.html", {
            "errors": errors,
            "data": request.POST,
        })

    return render(request, "accounts/register.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("feed")

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        next_url = request.POST.get("next", "feed")

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect(next_url if next_url else "feed")
        else:
            return render(request, "accounts/login.html", {
                "error": "Невірний логін або пароль.",
                "username": username,
                "next": next_url,
            })

    return render(request, "accounts/login.html", {
        "next": request.GET.get("next", ""),
    })


@require_POST
def logout_view(request):
    logout(request)
    return redirect("auth:login")
