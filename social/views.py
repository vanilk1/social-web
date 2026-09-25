from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Exists, OuterRef
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import Friendship, Follow
from .forms import CommentForm, PostForm
from .models import Comment, Like, Post, Share

User = get_user_model()


@login_required
def feed(request):
    """
    Стрічка новин. Три вкладки:
      - all      — всі публікації (за замовчуванням)
      - friends  — тільки від друзів
      - following — від підписок
    """
    tab = request.GET.get("tab", "all")

    # Друзі (прийняті запити в обидва боки)
    friend_ids = set(
        Friendship.objects.filter(
            Q(from_user=request.user) | Q(to_user=request.user),
            status=Friendship.Status.ACCEPTED,
        ).values_list(
            "from_user_id", "to_user_id"
        ).distinct()
    )
    # Розгортаємо пари в плоский set id (без себе)
    flat_friends = {uid for pair in friend_ids for uid in pair if uid != request.user.pk}

    # Підписки
    following_ids = Follow.objects.filter(
        follower=request.user
    ).values_list("following_id", flat=True)

    qs = Post.objects.select_related("author").prefetch_related(
        "likes", "comments", "shares"
    )

    if tab == "friends":
        qs = qs.filter(author_id__in=flat_friends)
    elif tab == "following":
        qs = qs.filter(author_id__in=following_ids)
    else:
        # «Всі» — друзі + підписки + свої
        visible_ids = flat_friends | set(following_ids) | {request.user.pk}
        qs = qs.filter(author_id__in=visible_ids)

    qs = qs.order_by("-created_at")

    # Позначаємо чи поточний юзер вже лайкнув кожен пост
    liked_posts = set(
        Like.objects.filter(
            user=request.user, post__isnull=False
        ).values_list("post_id", flat=True)
    )

    # Пагінація — 10 постів на сторінку
    paginator = Paginator(qs, 10)
    page_obj  = paginator.get_page(request.GET.get("page"))

    return render(request, "social/feed.html", {
        "posts":       page_obj,
        "page_obj":    page_obj,
        "tab":         tab,
        "liked_posts": liked_posts,
        "comment_form": CommentForm(),
        "post_form":   PostForm(),
        "friends_count": len(flat_friends),
    })


# ── Публікація поста ──────────────────────────────────────────────────

@login_required
@require_POST
def create_post(request):
    """Створення нової публікації."""
    form = PostForm(request.POST, request.FILES)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        messages.success(request, "Публікацію додано!")
    else:
        messages.error(request, "Не вдалося опублікувати. Перевірте поля.")
    return redirect("feed")


# ── Видалення поста ───────────────────────────────────────────────────

@login_required
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user and not request.user.is_admin:
        messages.error(request, "Немає прав для видалення.")
        return redirect(request.META.get("HTTP_REFERER", "/"))
    post.delete()
    messages.success(request, "Публікацію видалено.")
    return redirect(request.META.get("HTTP_REFERER", "/"))


# ── Поширення поста ───────────────────────────────────────────────────

@login_required
@require_POST
def share_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    _, created = Share.objects.get_or_create(user=request.user, post=post)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"shared": created, "count": post.shares.count()})
    return redirect(request.META.get("HTTP_REFERER", "/"))


# ── ЛАЙКИ ─────────────────────────────────────────────────────────────

@login_required
@require_POST
def toggle_like_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    like, created = Like.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    likes_count = post.likes.filter(comment__isnull=True).count()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"liked": liked, "count": likes_count})
    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
@require_POST
def toggle_like_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    like, created = Like.objects.get_or_create(user=request.user, comment=comment)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"liked": liked, "count": comment.likes.count()})
    return redirect(request.META.get("HTTP_REFERER", "/"))


# ── КОМЕНТАРІ ─────────────────────────────────────────────────────────

@login_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    text = request.POST.get("text", "").strip()
    if not text:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False}, status=400)
        return redirect(request.META.get("HTTP_REFERER", "/"))

    comment = Comment.objects.create(author=request.user, post=post, text=text)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({
            "success":    True,
            "comment_id": comment.pk,
            "author":     comment.author.get_full_name() or comment.author.username,
            "text":       comment.text,
            "created_at": comment.created_at.strftime("%d.%m.%Y %H:%M"),
            "avatar":     comment.author.avatar.url if comment.author.avatar else None,
        })
    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
@require_POST
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.author != request.user and not request.user.is_admin:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"success": False}, status=403)
        messages.error(request, "Немає прав для видалення.")
        return redirect(request.META.get("HTTP_REFERER", "/"))
    comment.delete()
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"success": True})
    return redirect(request.META.get("HTTP_REFERER", "/"))
