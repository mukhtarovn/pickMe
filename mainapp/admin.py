from django.contrib import admin

# chats/admin.py
from django.contrib import admin
from .models import ChatSession

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('user_uid', 'is_active')
    actions = ['end_chat']

    @admin.action(description='Завершить чат и удалить его из Firebase')
    def end_chat(self, request, queryset):
        import firebase_admin
        from firebase_admin import db

        for session in queryset:
            # Удалить чат из Firebase
            try:
                db.reference(f"users/{session.user_uid}/chats").delete()
                session.is_active = False
                session.save()
            except Exception as e:
                self.message_user(request, f"Ошибка при удалении чата {session.user_uid}: {e}")

