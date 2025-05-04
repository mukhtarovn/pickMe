import json

from django.shortcuts import render, redirect
import firebase_admin
from firebase_admin import credentials, db
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.contrib import messages
from django.http import JsonResponse
# Инициализация Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("google-service.json")
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://pickme-66a2b-default-rtdb.firebaseio.com/"
    })
def check_new_orders(request):
    # Логика для проверки новых заказов
    # Предположим, у нас есть база данных заказов, и мы проверяем последние обновления
    new_order = False
    # Здесь пишем проверку новых заказов (например, проверка по времени или флагу)
    if new_order:  # Если есть новый заказ
        return JsonResponse({'new_order': True})
    return JsonResponse({'new_order': False})



def main(request):
    ref = db.reference("/users/")
    try:
        snapshot = ref.get()
    except Exception as e:
        snapshot = {}
        messages.error(request, f"Ошибка при загрузке данных: {e}")
    return render(request, 'mainapp/index.html', {"content": snapshot})

@csrf_exempt
def update_price(request):
    data = json.loads(request.body)
    ref = db.reference(f"/users/{data['user_id']}/orders/{data['order_id']}")
    ref.update({'price': data['price']})
    return JsonResponse({'success': True})

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
    users = ref.get()

    order_count = 0
    for user in users.values():
        if 'orders' in user:
            order_count += len(user['orders'])

    return JsonResponse({'order_count': order_count})

def users_list(request):
    ref = db.reference('users')
    users_data = ref.get() or {}
    return render(request, 'mainapp/users.html', {'users': users_data})