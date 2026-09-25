from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Subquery, Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Conversation, ConversationParticipant, Message

User = get_user_model()


@login_required
def conversation_list(request):
    """
    Список усіх розмов поточного користувача.
    Для кожної — останнє повідомлення та кількість непрочитаних.
    """
    # Розмови, в яких бере участь юзер
    participations = ConversationParticipant.objects.filter(user=request.user)
    conversation_ids = participations.values_list("conversation_id", flat=True)

    # Підзапит для останнього повідомлення
    last_message = (
        Message.objects.filter(conversation=OuterRef("pk"), is_deleted=False)
        .order_by("-created_at")
        .values("text")[:1]
    )
    last_message_time = (
        Message.objects.filter(conversation=OuterRef("pk"), is_deleted=False)
        .order_by("-created_at")
        .values("created_at")[:1]
    )

    conversations = (
        Conversation.objects.filter(pk__in=conversation_ids)
        .annotate(
            last_text=Subquery(last_message),
            last_time=Subquery(last_message_time),
        )
        .order_by("-last_time")
    )

    # Підрахунок непрочитаних для кожної розмови
    unread_map = {}
    for p in participations:
        count = Message.objects.filter(
            conversation_id=p.conversation_id,
            is_deleted=False,
        )
        if p.last_read_at:
            count = count.filter(created_at__gt=p.last_read_at)
        count = count.exclude(sender=request.user).count()
        unread_map[p.conversation_id] = count

    # Для приватних чатів — знаходимо співрозмовника
    conv_data = []
    for conv in conversations:
        if not conv.is_group:
            other = conv.participants.exclude(pk=request.user.pk).first()
        else:
            other = None
        conv_data.append({
            "conv": conv,
            "other": other,
            "unread": unread_map.get(conv.pk, 0),
        })

    return render(request, "chat/conversation_list.html", {"conv_data": conv_data})


@login_required
def conversation_detail(request, conversation_id):
    """
    Сторінка чату: показує повідомлення і підключає WebSocket.
    Позначає повідомлення як прочитані (оновлює last_read_at).
    """
    conversation = get_object_or_404(Conversation, pk=conversation_id)

    # Перевірка участі
    participant = get_object_or_404(
        ConversationParticipant, conversation=conversation, user=request.user
    )

    # Позначаємо прочитані
    from django.utils.timezone import now
    participant.last_read_at = now()
    participant.save(update_fields=["last_read_at"])

    messages_qs = conversation.messages.filter(is_deleted=False).select_related("sender")
    other = None
    if not conversation.is_group:
        other = conversation.participants.exclude(pk=request.user.pk).first()

    return render(request, "chat/conversation_detail.html", {
        "conversation": conversation,
        "messages": messages_qs,
        "other": other,
        "participants": conversation.participants.all(),
    })


@login_required
@require_POST
def create_private_conversation(request):
    """Створення або відкриття приватної розмови з іншим юзером."""
    other_id = request.POST.get("user_id")
    other = get_object_or_404(User, pk=other_id)

    if other == request.user:
        return redirect("chat:list")

    # Шукаємо існуючий приватний чат між двома юзерами
    existing = (
        Conversation.objects.filter(is_group=False)
        .filter(participants=request.user)
        .filter(participants=other)
        .annotate(cnt=Count("participants"))
        .filter(cnt=2)
        .first()
    )

    if existing:
        return redirect("chat:detail", conversation_id=existing.pk)

    # Створюємо новий
    conv = Conversation.objects.create(is_group=False)
    ConversationParticipant.objects.bulk_create([
        ConversationParticipant(conversation=conv, user=request.user),
        ConversationParticipant(conversation=conv, user=other),
    ])
    return redirect("chat:detail", conversation_id=conv.pk)


@login_required
@require_POST
def create_group_conversation(request):
    """Створення групового чату."""
    title = request.POST.get("title", "").strip() or "Груповий чат"
    user_ids = request.POST.getlist("user_ids")

    if not user_ids:
        return redirect("chat:list")

    participants = list(User.objects.filter(pk__in=user_ids))
    conv = Conversation.objects.create(is_group=True, title=title)
    to_create = [ConversationParticipant(conversation=conv, user=request.user)]
    for u in participants:
        if u != request.user:
            to_create.append(ConversationParticipant(conversation=conv, user=u))
    ConversationParticipant.objects.bulk_create(to_create)

    return redirect("chat:detail", conversation_id=conv.pk)
