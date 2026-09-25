"""
context_processors.py

Додає `unread_notifications_count` до контексту кожного шаблону.
Підключити в settings.py:

    TEMPLATES = [{
        ...
        "OPTIONS": {
            "context_processors": [
                ...
                "notifications.context_processors.unread_notifications",
            ],
        },
    }]
"""


def unread_notifications(request):
    if request.user.is_authenticated:
        count = request.user.notifications.filter(is_read=False).count()
    else:
        count = 0
    return {"unread_notifications_count": count}
