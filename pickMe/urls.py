"""
URL configuration for pickMe project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
import mainapp.views as mainapp
from mainapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('check_new_orders/', views.check_new_orders, name='check_new_orders'),
    path('', mainapp.main),
    path('mark_done/', views.mark_done, name='mark_done'),
    path('delete_order/', views.delete_order, name='delete_order'),
    path('update_price/', views.update_price, name='update_price'),
    path('users/', views.users_list, name='users'),
    path('get-orders-html/', views.get_orders_html, name='get_orders_html'),
    path('dispatcher_chat/', views.dispatcher_chat_view, name='dispatcher_chat'),
    path('fetch_messages/', views.fetch_messages, name='fetch_messages'),
    path('check-orders/', views.check_new_orders, name='check_new_orders'),
    path('get-orders-html/', views.get_orders_html, name='get_orders_html'),
    path("check-chat-updates/", views.check_chat_updates, name="check_chat"),
    path('login/', LoginView.as_view(template_name='mainapp/login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
]
