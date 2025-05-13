from django.db import models

class ChatSession(models.Model):
    user_uid = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Чат с пользователем {self.user_uid} ({'Активен' if self.is_active else 'Закрыт'})"

