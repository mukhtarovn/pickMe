import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import firebase_admin
from firebase_admin import credentials, db
from django.shortcuts import render, redirect
from requests import session
import time
from mainapp.models import ChatSession

# Инициализация Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("google-service.json")
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://pickme-66a2b-default-rtdb.firebaseio.com/"
    })

@login_required
def main(request):
    ref = db.reference("/users/")
    try:
        snapshot = ref.get()
    except Exception as e:
        snapshot = {}
        messages.error(request, f"Ошибка при загрузке данных: {e}")

    # Сортировка заказов (новые заказы выше)
    for user_id, user_data in snapshot.items():
        if user_data.get("orders"):
            sorted_orders = dict(
                sorted(
                    user_data["orders"].items(),
                    key=lambda item: item[1].get("date", ""),
                    reverse=True
                )
            )
            user_data["orders"] = sorted_orders

    return render(request, 'mainapp/index.html', {"content": snapshot})


@csrf_exempt
def update_price(request):
    if request.method == 'POST':
        try:
            print("🔔 update_price вызван")
            data = json.loads(request.body)
            print("📦 данные:", data)

            user_id = data.get('user_id')
            order_id = data.get('order_id')
            price = data.get('price')

            if not (user_id and order_id and price):
                print("❌ Не хватает данных")
                return JsonResponse({'error': 'Missing data'}, status=400)

            ref = db.reference(f"/users/{user_id}/orders/{order_id}")
            ref.update({'price': price})
            print("✅ Успешно обновлено")

            return JsonResponse({'success': True})
        except Exception as e:
            print("🔥 Ошибка:", e)
            return JsonResponse({'error': str(e)}, status=500)
    else:
        print("❌ Не POST-запрос")
        return JsonResponse({'error': 'Invalid request'}, status=400)


@csrf_exempt
def mark_done(request):
    data = json.loads(request.body)
    ref = db.reference(f"/users/{data['user_id']}/orders/{data['order_id']}")
    ref.update({'isDone': True})
    return JsonResponse({'success': True})


@csrf_exempt
def delete_order(request):
    data = json.loads(request.body)
    ref = db.reference(f"/users/{data['user_id']}/orders/{data['order_id']}")
    ref.delete()
    return JsonResponse({'success': True})


def check_new_orders(request):
    ref = db.reference("/users/")
    users = ref.get() or {}

    order_count = 0
    for user in users.values():
        if 'orders' in user:
            for order in user['orders'].values():
                if not order.get('isDone', False):  # считаем только не завершённые
                    order_count += 1

    return JsonResponse({'order_count': order_count})


from django.template.loader import render_to_string

def get_orders_html(request):
    ref = db.reference("/users/")
    try:
        snapshot = ref.get()
    except Exception as e:
        snapshot = {}

    html = render_to_string("mainapp/table_order.html", {"content": snapshot})
    return JsonResponse({'html': html})


@login_required
def users_list(request):
    ref = db.reference('users')
    users_data = ref.get() or {}
    return render(request, 'mainapp/users.html', {'users': users_data})
@login_required
def dispatcher_chat_view(request):
    selected_uid = request.GET.get("user_uid")
    messages_list = []
    sessions = []

    users_ref = db.reference("users")
    users_data = users_ref.get() or {}

    for uid, user in users_data.items():
        name = user.get("name", uid)  # <-- ИСПРАВЛЕНО
        has_new = False
        latest_time = 0

        chats = user.get("chats", {})
        for msg in chats.values():
            ts = msg.get("timestamp", 0)
            if ts > latest_time:
                latest_time = ts
            if msg.get("sender") != "dispatcher" and not msg.get("is_read", False):
                has_new = True

        sessions.append({
            "uid": uid,
            "name": name,
            "has_new": has_new,
            "last_time": latest_time
        })

    # Сортировка: новые выше, потом по дате
    sessions.sort(key=lambda x: (not x["has_new"], -x["last_time"]))

    # Отправка сообщения
    if request.method == "POST":
        uid = request.POST.get("user_uid")
        message_text = request.POST.get("message")
        if uid and message_text:
            db.reference(f"users/{uid}/chats").push({
                "sender": "dispatcher",
                "text": message_text,
                "timestamp": int(time.time()),
                "is_read": False
            })
            return redirect(f"/dispatcher_chat/?user_uid={uid}")
        elif "end_chat" in request.POST:
            db.reference(f"users/{uid}/chats").delete()
            messages.success(request, "Chat ended")
            return redirect("/dispatcher_chat/")

    if selected_uid:
        chat_ref = db.reference(f"users/{selected_uid}/chats")
        chat_data = chat_ref.order_by_child("timestamp").limit_to_last(50).get()
        if chat_data:
            sorted_data = sorted(chat_data.values(), key=lambda x: x.get("timestamp", 0))
            messages_list = sorted_data

            # Отметим все как прочитанные
            for key, msg in chat_data.items():
                if msg.get("sender") != "dispatcher":
                    chat_ref.child(key).update({"is_read": True})

    return render(request, "mainapp/dispatcher_chat.html", {
        "sessions": sessions,
        "selected_uid": selected_uid,
        "messages_list": messages_list
    })
# chats/views.py

def fetch_messages(request):
    uid = request.GET.get("uid")
    if not uid:
        return JsonResponse({"error": "UID is required"}, status=400)

    chat_ref = db.reference(f"users/{uid}/chats")
    chat_data = chat_ref.order_by_child("timestamp").limit_to_last(50).get()

    messages_list = []
    if chat_data:
        messages_list = sorted(chat_data.values(), key=lambda x: x.get("timestamp") or 0)

    return JsonResponse({"messages": messages_list})
chat_latest = {}

def check_chat_updates(request):
    users = db.reference("users").get() or {}
    updates = []

    for uid, user in users.items():
        chats = user.get("chats", {})
        latest_msg = max(chats.values(), key=lambda x: x.get("timestamp", 0), default=None)
        if latest_msg and latest_msg.get("sender") != "dispatcher":
            ts = latest_msg.get("timestamp")
            if chat_latest.get(uid) != ts:
                chat_latest[uid] = ts
                updates.append({
                    "uid": uid,
                    "text": latest_msg.get("text", "")
                })
                print (updates)

    return JsonResponse({"new_messages": updates})

def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST.get('email', '')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
        else:
            User.objects.create_user(username=username, password=password, email=email)
            messages.success(request, "Account created! Please log in.")
            return redirect('login')

    return render(request, 'mainapp/register.html')