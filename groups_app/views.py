from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from social.models import Post, Like
from .forms import GroupForm, GroupPostForm
from .models import Group, GroupMembership, GroupPost


def group_list(request):
    q  = request.GET.get("q", "").strip()
    qs = Group.objects.annotate(members_count=Count("memberships"))

    if q:
        qs = qs.filter(name__icontains=q)

    # Для авторизованого — окремо «мої групи»
    my_groups = []
    if request.user.is_authenticated:
        my_ids    = request.user.group_memberships.values_list("group_id", flat=True)
        my_groups = qs.filter(pk__in=my_ids).order_by("name")
        other     = qs.filter(privacy=Group.Privacy.PUBLIC).exclude(pk__in=my_ids).order_by("-members_count")
    else:
        other = qs.filter(privacy=Group.Privacy.PUBLIC).order_by("-members_count")

    return render(request, "groups_app/group_list.html", {
        "my_groups": my_groups,
        "other":     other,
        "q":         q,
    })


# ── Деталь групи ──────────────────────────────────────────────────────

def group_detail(request, group_id):
    group = get_object_or_404(Group, pk=group_id)

    membership = None
    if request.user.is_authenticated:
        membership = GroupMembership.objects.filter(
            group=group, user=request.user
        ).first()

    # Приватна — тільки учасники бачать пости
    can_see_posts = (
        group.privacy == Group.Privacy.PUBLIC or
        membership is not None or
        (request.user.is_authenticated and request.user.is_admin)
    )

    group_posts = []
    liked_posts = set()
    if can_see_posts:
        group_posts = (
            GroupPost.objects
            .filter(group=group, is_approved=True)
            .select_related("post__author")
            .prefetch_related("post__likes", "post__comments")
            .order_by("-post__created_at")
        )
        if request.user.is_authenticated:
            post_ids = group_posts.values_list("post_id", flat=True)
            liked_posts = set(
                Like.objects.filter(
                    user=request.user, post_id__in=post_ids
                ).values_list("post_id", flat=True)
            )

    members = (
        GroupMembership.objects
        .filter(group=group)
        .select_related("user")
        .order_by("role", "joined_at")[:20]
    )

    can_post = membership is not None
    is_admin = membership and membership.role in (
        GroupMembership.Role.ADMIN, GroupMembership.Role.MODERATOR
    )

    return render(request, "groups_app/group_detail.html", {
        "group":        group,
        "membership":   membership,
        "group_posts":  group_posts,
        "liked_posts":  liked_posts,
        "members":      members,
        "can_see_posts": can_see_posts,
        "can_post":     can_post,
        "is_admin":     is_admin,
        "post_form":    GroupPostForm(),
        "members_count": group.memberships.count(),
    })


# ── Створення групи ───────────────────────────────────────────────────

@login_required
def group_create(request):
    if request.method == "POST":
        form = GroupForm(request.POST, request.FILES)
        if form.is_valid():
            group = form.save(commit=False)
            group.creator = request.user
            group.save()
            # Автоматично додаємо засновника як адміна
            GroupMembership.objects.create(
                group=group, user=request.user,
                role=GroupMembership.Role.ADMIN,
            )
            messages.success(request, f"Групу «{group.name}» створено!")
            return redirect("groups_app:detail", group_id=group.pk)
    else:
        form = GroupForm()
    return render(request, "groups_app/group_form.html", {"form": form, "title": "Створити групу"})


# ── Редагування групи ─────────────────────────────────────────────────

@login_required
def group_edit(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    membership = get_object_or_404(GroupMembership, group=group, user=request.user)
    if membership.role not in (GroupMembership.Role.ADMIN,):
        messages.error(request, "Тільки адміністратор може редагувати групу.")
        return redirect("groups_app:detail", group_id=group_id)

    if request.method == "POST":
        form = GroupForm(request.POST, request.FILES, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, "Групу оновлено.")
            return redirect("groups_app:detail", group_id=group_id)
    else:
        form = GroupForm(instance=group)
    return render(request, "groups_app/group_form.html", {"form": form, "group": group, "title": "Редагувати групу"})


# ── Вступити / вийти ──────────────────────────────────────────────────

@login_required
@require_POST
def toggle_membership(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    membership = GroupMembership.objects.filter(group=group, user=request.user).first()

    if membership:
        # Не дозволяємо засновнику покинути власну групу
        if membership.role == GroupMembership.Role.ADMIN and group.creator == request.user:
            messages.error(request, "Засновник не може покинути групу. Спочатку передайте права.")
            return redirect("groups_app:detail", group_id=group_id)
        membership.delete()
        messages.info(request, f"Ви покинули групу «{group.name}».")
    else:
        GroupMembership.objects.create(group=group, user=request.user)
        messages.success(request, f"Ви приєднались до групи «{group.name}»!")

    return redirect("groups_app:detail", group_id=group_id)


# ── Публікація у групі ────────────────────────────────────────────────

@login_required
@require_POST
def group_post_create(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    membership = GroupMembership.objects.filter(group=group, user=request.user).first()

    if not membership:
        messages.error(request, "Тільки учасники можуть публікувати у групі.")
        return redirect("groups_app:detail", group_id=group_id)

    form = GroupPostForm(request.POST, request.FILES)
    if form.is_valid():
        post = Post.objects.create(
            author=request.user,
            text=form.cleaned_data.get("text", ""),
            image=form.cleaned_data.get("image"),
        )
        GroupPost.objects.create(group=group, post=post)
        messages.success(request, "Публікацію додано!")
    else:
        messages.error(request, "Не вдалося опублікувати.")

    return redirect("groups_app:detail", group_id=group_id)


# ── Видалення поста з групи (модерація) ──────────────────────────────

@login_required
@require_POST
def group_post_remove(request, group_id, group_post_id):
    group      = get_object_or_404(Group, pk=group_id)
    group_post = get_object_or_404(GroupPost, pk=group_post_id, group=group)
    membership = GroupMembership.objects.filter(group=group, user=request.user).first()

    can_remove = (
        group_post.post.author == request.user or
        (membership and membership.role in (GroupMembership.Role.ADMIN, GroupMembership.Role.MODERATOR)) or
        request.user.is_admin
    )

    if not can_remove:
        messages.error(request, "Немає прав для видалення.")
        return redirect("groups_app:detail", group_id=group_id)

    group_post.post.delete()   # каскадно видаляє GroupPost
    messages.success(request, "Публікацію видалено.")
    return redirect("groups_app:detail", group_id=group_id)


# ── Управління учасниками (адмін) ────────────────────────────────────

@login_required
@require_POST
def member_role_change(request, group_id, member_id):
    group      = get_object_or_404(Group, pk=group_id)
    membership = get_object_or_404(GroupMembership, group=group, user=request.user)

    if membership.role != GroupMembership.Role.ADMIN:
        messages.error(request, "Тільки адміністратор може змінювати ролі.")
        return redirect("groups_app:detail", group_id=group_id)

    target = get_object_or_404(GroupMembership, group=group, pk=member_id)
    new_role = request.POST.get("role")

    if new_role in dict(GroupMembership.Role.choices):
        target.role = new_role
        target.save(update_fields=["role"])
        messages.success(request, f"Роль {target.user.username} змінено.")

    return redirect("groups_app:detail", group_id=group_id)


@login_required
@require_POST
def member_kick(request, group_id, member_id):
    group      = get_object_or_404(Group, pk=group_id)
    membership = get_object_or_404(GroupMembership, group=group, user=request.user)

    if membership.role not in (GroupMembership.Role.ADMIN, GroupMembership.Role.MODERATOR):
        messages.error(request, "Немає прав.")
        return redirect("groups_app:detail", group_id=group_id)

    target = get_object_or_404(GroupMembership, group=group, pk=member_id)
    if target.role == GroupMembership.Role.ADMIN:
        messages.error(request, "Не можна видалити адміністратора.")
        return redirect("groups_app:detail", group_id=group_id)

    target.delete()
    messages.success(request, f"Учасника {target.user.username} виключено.")
    return redirect("groups_app:detail", group_id=group_id)
