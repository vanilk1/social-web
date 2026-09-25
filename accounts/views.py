from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from social.forms import CommentForm
from social.models import Post
from .forms import AvatarForm, CoverForm, ProfileEditForm
from .models import Follow, Friendship

User = get_user_model()


def profile_view(request, user_id):
    """
    Сторінка профілю будь-якого користувача.
    Для власного профілю показує кнопку «Редагувати».
    """
    profile_user = get_object_or_404(User, pk=user_id)
    posts = Post.objects.filter(author=profile_user).order_by("-created_at")

    # Стан дружби/підписки для поточного користувача
    friendship_status = None
    is_following = False

    if request.user.is_authenticated and request.user != profile_user:
        # Дружба (в будь-якому напрямку)
        friendship = Friendship.objects.filter(
            from_user=request.user, to_user=profile_user
        ).first() or Friendship.objects.filter(
            from_user=profile_user, to_user=request.user
        ).first()
        friendship_status = friendship.status if friendship else None

        is_following = Follow.objects.filter(
            follower=request.user, following=profile_user
        ).exists()

    friends_count = Friendship.objects.filter(
        from_user=profile_user, status=Friendship.Status.ACCEPTED
    ).count() + Friendship.objects.filter(
        to_user=profile_user, status=Friendship.Status.ACCEPTED
    ).count()

    followers_count = Follow.objects.filter(following=profile_user).count()

    context = {
        "profile_user": profile_user,
        "posts": posts,
        "comment_form": CommentForm(),
        "friendship_status": friendship_status,
        "is_following": is_following,
        "friends_count": friends_count,
        "followers_count": followers_count,
        "is_own_profile": request.user == profile_user,
    }
    return render(request, "accounts/profile.html", context)


@login_required
def profile_edit(request):
    """Редагування особистих даних поточного користувача."""
    if request.method == "POST":
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Профіль успішно оновлено.")
            return redirect("accounts:profile", user_id=request.user.pk)
    else:
        form = ProfileEditForm(instance=request.user)

    return render(request, "accounts/profile_edit.html", {"form": form})


@login_required
@require_POST
def update_avatar(request):
    """Оновлення аватара (окремий POST, можна через AJAX)."""
    form = AvatarForm(request.POST, request.FILES, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, "Аватар оновлено.")
    else:
        messages.error(request, "Невірний файл аватара.")
    return redirect("accounts:profile", user_id=request.user.pk)


@login_required
@require_POST
def update_cover(request):
    """Оновлення обкладинки профілю."""
    form = CoverForm(request.POST, request.FILES, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, "Обкладинку оновлено.")
    else:
        messages.error(request, "Невірний файл обкладинки.")
    return redirect("accounts:profile", user_id=request.user.pk)


# ── Друзі та підписки ──────────────────────────────────────────────────

@login_required
@require_POST
def send_friend_request(request, user_id):
    to_user = get_object_or_404(User, pk=user_id)
    if to_user == request.user:
        messages.error(request, "Не можна додати себе в друзі.")
        return redirect("accounts:profile", user_id=user_id)

    _, created = Friendship.objects.get_or_create(
        from_user=request.user, to_user=to_user
    )
    if created:
        messages.success(request, f"Запит надіслано до {to_user.username}.")
    else:
        messages.info(request, "Запит вже надіслано.")
    return redirect("accounts:profile", user_id=user_id)


@login_required
@require_POST
def respond_friend_request(request, request_id):
    """Прийняти або відхилити запит."""
    friendship = get_object_or_404(
        Friendship, pk=request_id, to_user=request.user
    )
    action = request.POST.get("action")  # "accept" або "decline"

    if action == "accept":
        friendship.status = Friendship.Status.ACCEPTED
        friendship.save()
        messages.success(request, "Запит прийнято.")
    elif action == "decline":
        friendship.status = Friendship.Status.DECLINED
        friendship.save()
        messages.info(request, "Запит відхилено.")

    return redirect("accounts:profile", user_id=friendship.from_user.pk)


@login_required
@require_POST
def toggle_follow(request, user_id):
    """Підписатись / відписатись від користувача."""
    target = get_object_or_404(User, pk=user_id)
    if target == request.user:
        return redirect("accounts:profile", user_id=user_id)

    follow, created = Follow.objects.get_or_create(
        follower=request.user, following=target
    )
    if not created:
        follow.delete()
        messages.info(request, f"Ви відписались від {target.username}.")
    else:
        messages.success(request, f"Ви підписались на {target.username}.")

    return redirect("accounts:profile", user_id=user_id)
