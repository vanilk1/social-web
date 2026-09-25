import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.utils.timezone import now

from .models import Conversation, ConversationParticipant, Message


class ChatConsumer(WebsocketConsumer):
    """
    WebSocket-консьюмер для одного чату.
    URL: ws/chat/<conversation_id>/

    Групова назва каналу: chat_<conversation_id>
    Усі учасники однієї розмови — в одній group,
    тому повідомлення від одного одразу отримують усі.
    """

    def connect(self):
        self.user = self.scope["user"]
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"

        # Перевірка: чи є юзер учасником цієї розмови
        if not self.user.is_authenticated:
            self.close()
            return

        is_participant = ConversationParticipant.objects.filter(
            conversation_id=self.conversation_id, user=self.user
        ).exists()

        if not is_participant:
            self.close()
            return

        # Приєднуємось до channel layer групи
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    def receive(self, text_data):
        """Отримуємо повідомлення від клієнта (JSON)."""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        message_text = data.get("message", "").strip()
        if not message_text:
            return

        # Зберігаємо в БД
        message = Message.objects.create(
            conversation_id=self.conversation_id,
            sender=self.user,
            text=message_text,
        )

        # Оновлюємо last_read_at для відправника
        ConversationParticipant.objects.filter(
            conversation_id=self.conversation_id, user=self.user
        ).update(last_read_at=now())

        # Розсилаємо всім учасникам групи
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                "type": "chat_message",
                "message_id": message.pk,
                "text": message.text,
                "sender_id": self.user.pk,
                "sender_name": self.user.get_full_name() or self.user.username,
                "sender_avatar": self.user.avatar.url if self.user.avatar else None,
                "created_at": message.created_at.strftime("%H:%M"),
            },
        )

    def chat_message(self, event):
        """Надсилаємо повідомлення конкретному WebSocket-клієнту."""
        self.send(text_data=json.dumps(event))
